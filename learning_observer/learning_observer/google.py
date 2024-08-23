'''
We will gradually move all of the Google-specific code into here.

Our design goals:
- Easily call into Google APIs (Classroom, Drive, Docs, etc.)
- Be able to preprocess the data into standard formats

On a high level, for each Google request, we plan to have a 4x4 grid:
- Web request and function call
- Cleaned versus raw data

The Google APIs are well-designed (if poorly-documented, and with occasional
bugs), but usually return more data than we need, so we have cleaner functions.

For a given call, we might have several cleaners. For example, for a Google Doc,
Google returns a massive JSON object containing everything. For most purposes,
we don't need all of that, and it's more convenient to work with a plain
text representation, and for downstream code to not need to understand this
JSON. However, for some algorithms, we might need additonal data of different
sorts. It's still more convenient to hand this back in something simplified for
analysis.
'''

import itertools
import json
import re
import functools

import learning_observer.constants as constants
import learning_observer.settings as settings
import learning_observer.log_event
import learning_observer.util
import learning_observer.auth
import learning_observer.runtime
import learning_observer.prestartup
import learning_observer.lms_integration


cache = None
LMS_NAME = "google"


GOOGLE_FIELDS = [
    'alternateLink', 'calculationType', 'calendarId', 'courseGroupEmail',
    'courseId', 'courseState', 'creationTime', 'descriptionHeading',
    'displaySetting', 'emailAddress', 'enrollmentCode', 'familyName',
    'fullName', 'givenName', 'gradebookSettings', 'guardiansEnabled',
    'ownerId', 'photoUrl', 'teacherFolder', 'teacherGroupEmail', 'updateTime',
    'userId'
]

# On in-take, we want to convert Google's CamelCase to LO's snake_case. This
# dictionary contains the conversions.
camel_to_snake = re.compile(r'(?<!^)(?=[A-Z])')
GOOGLE_TO_SNAKE = {field: camel_to_snake.sub('_', field).lower() for field in GOOGLE_FIELDS}


GOOGLE_ENDPOINTS = list(map(lambda x: learning_observer.lms_integration.Endpoint(*x, "", None, LMS_NAME), [
    ("document", "https://docs.googleapis.com/v1/documents/{documentId}"),
    ("course_list", "https://classroom.googleapis.com/v1/courses"),
    ("course_roster", "https://classroom.googleapis.com/v1/courses/{courseId}/students"),
    ("course_work", "https://classroom.googleapis.com/v1/courses/{courseId}/courseWork"),
    ("coursework_submissions", "https://classroom.googleapis.com/v1/courses/{courseId}/courseWork/{courseWorkId}/studentSubmissions"),
    ("coursework_materials", "https://classroom.googleapis.com/v1/courses/{courseId}/courseWorkMaterials"),
    ("course_topics", "https://classroom.googleapis.com/v1/courses/{courseId}/topics"),
    ("drive_files", "https://www.googleapis.com/drive/v3/files"),    # This paginates. We only return page 1.
    ("drive_about", "https://www.googleapis.com/drive/v3/about?fields=%2A"),  # Fields=* probably gives us more than we need
    ("drive_comments", "https://www.googleapis.com/drive/v3/files/{documentId}/comments?fields=%2A&includeDeleted=true"),
    ("drive_revisions", "https://www.googleapis.com/drive/v3/files/{documentId}/revisions")
]))

register_cleaner_with_endpoints = functools.partial(learning_observer.lms_integration.register_cleaner, endpoints=GOOGLE_ENDPOINTS)

# Google Docs
def _force_text_length(text, length):
    '''
    Force text to a given length, either concatenating or padding

    >>> force_text_length("Hello", 3)
    >>> 'Hel'

    >>> force_text_length("Hello", 13)
    >>> 'Hello        '
    '''
    return text[:length] + " " * (length - len(text))

def get_error_details(error):
    messages = {
        403: 'Student working on private document.',
        404: 'Unable to fetch document.'
    }
    code = error['code']
    message = messages.get(code, 'Unknown error.')
    return {'error': {'code': code, 'message': message}}

class GoogleLMS(learning_observer.lms_integration.LMS):
    def __init__(self):
        super().__init__(lms_name=LMS_NAME, endpoints=GOOGLE_ENDPOINTS)

    # Rosters
    @register_cleaner_with_endpoints("course_roster", "roster")
    def clean_course_roster(google_json):
        '''
        Retrieve the roster for a course, alphabetically
        '''
        students = google_json.get('students', [])
        students.sort(
            key=lambda x: x.get('name', {}).get('fullName', 'ZZ'),
        )
        # Convert Google IDs to internal ideas (which are the same, but with a gc- prefix)
        for student_json in students:
            google_id = student_json['profile']['id']
            local_id = learning_observer.auth.google_id_to_user_id(google_id)
            student_json[constants.USER_ID] = local_id
            del student_json['profile']['id']

            # For the present there is only one external id so we will add that directly.
            if 'external_ids' not in student_json['profile']:
                student_json['profile']['external_ids'] = []
            student_json['profile']['external_ids'].append({"source": "google", "id": google_id})
        return students

    @register_cleaner_with_endpoints("course_list", "courses")
    def clean_course_list(google_json):
        '''
        Google's course list is one object deeper than we'd like, and alphabetic
        sort order is nicer. This will clean it up a bit
        '''
        courses = google_json.get('courses', [])
        courses.sort(
            key=lambda x: x.get('name', 'ZZ'),
        )
        return courses

    @register_cleaner_with_endpoints("document", "doctext")
    def extract_text_from_google_doc_json(
            j, align=True,
            EXTRACT_DEBUG_CHECKS=False):
        '''
        Extract text from a Google Docs JSON object, ignoring formatting.

        There is an alignment issue between Google's and Python's handling
        of Unicode. We can either:
        * extract text faithfully (align=False)
        * extract text with aligned indexes by cutting text / adding
        spaces (align=True)

        This issue came up in text with a Russian flag unicode symbol
        (referencing the current conflict). I tried various encodings,
        and none quite matched Google 100%.

        Note that align=True doesn't necessarily give perfect local alignment
        within text chunks, since we do have different lengths for something like
        this flag. It does work okay globally.
        '''
        # return error message for text
        if 'error' in j:
            return get_error_details(j['error'])
        length = j['body']['content'][-1]['endIndex']
        elements = [a.get('paragraph', {}).get('elements', []) for a in j['body']['content']]
        flat = sum(elements, [])
        text_chunks = [f.get('textRun', {}).get('content', '') for f in flat]
        if align:
            for f in flat:
                text = f.get('textRun', {}).get('content', None)
                if text != None:
                    length = f['endIndex'] - f['startIndex']
                    text_chunks.append(_force_text_length(text, length))
        else:
            for f in flat:
                text = f.get('textRun', {}).get('content', None)
                if text != None:
                    text_chunks.append(text)
        text = ''.join(text_chunks)

        if EXTRACT_DEBUG_CHECKS:
            print("Text length versus Google length:")
            print(len(text), length)
            print("We expect these to be off by one, since Google seems to starts at 1 (and Python at 0)")
            if align:
                print
                print("Offsets (these should match):")
                print(list(zip(itertools.accumulate(map(len, text_chunks)), itertools.accumulate(lengths))))

        return {'text': text}

    @register_cleaner_with_endpoints("coursework_submissions", "assigned_docs")
    def clean_assignment_docs(google_json):
        '''
        Retrieve set of documents per student associated with an assignment
        '''
        student_submissions = google_json.get('studentSubmissions', [])
        for student_json in student_submissions:
            google_id = student_json[constants.USER_ID]
            local_id = learning_observer.auth.google_id_to_user_id(google_id)
            student_json[constants.USER_ID] = local_id
            docs = [d['driveFile'] for d in learning_observer.util.get_nested_dict_value(student_json, 'assignmentSubmission.attachments', []) if 'driveFile' in d]
            student_json['documents'] = docs
            # TODO we should probably remove some of the keys provided
        return student_submissions

    @learning_observer.prestartup.register_startup_check
    def connect_to_google_cache():
        '''Setup cache for requests to the Google API.
        The cache is currently only used with the `use_google_ajax`
        feature flag.
        '''
        if 'google_routes' not in settings.settings['feature_flags']:
            return

        for key in ['save_google_ajax', 'use_google_ajax', 'save_clean_ajax', 'use_clean_ajax']:
            if key in settings.settings['feature_flags']:
                global cache
                try:
                    cache = learning_observer.kvs.KVS.google_cache()
                except AttributeError:
                    error_text = 'The google_cache KVS is not configured.\n'\
                        'Please add a `google_cache` kvs item to the `kvs` '\
                        'key in `creds.yaml`.\n'\
                        '```\ngoogle_cache:\n  type: filesystem\n  path: ./learning_observer/static_data/google\n'\
                        '  subdirs: true\n```\nOR\n'\
                        '```\ngoogle_cache:\n  type: redis_ephemeral\n  expiry: 600\n```'
                    raise learning_observer.prestartup.StartupCheck("Google KVS: " + error_text) 
        
google_lms = GoogleLMS()

def initialize_google_routes(app):
    google_lms.initialize_routes(app)

if __name__ == '__main__':
    import json
    import sys
    j = json.load(open(sys.argv[1]))
    output = google_lms.clean_assignment_docs(j)
    print(json.dumps(output, indent=2))
