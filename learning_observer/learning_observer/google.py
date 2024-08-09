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

import aiohttp
import aiohttp.web

import learning_observer.constants as constants
import learning_observer.settings as settings
import learning_observer.log_event
import learning_observer.util
import learning_observer.auth
import learning_observer.runtime
import learning_observer.prestartup

from learning_observer.lms_integration import Endpoint, register_cleaner, api_docs_handler, raw_access_partial, make_ajax_raw_handler, make_cleaner_handler, make_cleaner_function


cache = None
LMS = "google"


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


ENDPOINTS = list(map(lambda x: Endpoint(*x, "", None, LMS), [
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


async def raw_google_ajax(runtime, target_url, **kwargs):
    '''
    Make an AJAX call to Google, managing auth + auth.

    * runtime is a Runtime class containing request information.
    * default_url is typically grabbed from ENDPOINTS
    * ... and we pass the named parameters
    '''
    request = runtime.get_request()
    url = target_url.format(**kwargs)
    user = await learning_observer.auth.get_active_user(request)
    if constants.AUTH_HEADERS not in request:
        raise aiohttp.web.HTTPUnauthorized(text="Please log in")  # TODO: Consistent way to flag this

    cache_key = "raw_google/" + learning_observer.auth.encode_id('session', user[constants.USER_ID]) + '/' + learning_observer.util.url_pathname(url)
    if settings.feature_flag('use_google_ajax') is not None:
        value = await cache[cache_key]
        if value is not None:
            return learning_observer.util.translate_json_keys(
                json.loads(value),
                GOOGLE_TO_SNAKE
            )
    async with aiohttp.ClientSession(loop=request.app.loop) as client:
        async with client.get(url, headers=request[constants.AUTH_HEADERS]) as resp:
            response = await resp.json()
            learning_observer.log_event.log_ajax(target_url, response, request)
            if settings.feature_flag('use_google_ajax') is not None:
                await cache.set(cache_key, json.dumps(response, indent=2))
            return learning_observer.util.translate_json_keys(
                response,
                GOOGLE_TO_SNAKE
            )


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
    
def initialize_google_routes(app):
    '''
    - Created debug routes to pass through AJAX requests to Google
    - Created production APIs to have access to cleaned versions of said data
    - Create local function calls to call from other pieces of code within process
    '''
    # Provide documentation on what we're doing
    app.add_routes([
        aiohttp.web.get("/google", api_docs_handler)
    ])

    for e in ENDPOINTS:
        function_name = f"raw_{e.name}"
        raw_function = raw_access_partial(remote_url=e.remote_url, name=e.name)
        globals()[function_name] = raw_function
        cleaners = e._cleaners()
        for c in cleaners:
            app.add_routes([
                aiohttp.web.get(
                    cleaners[c]['local_url'],
                    make_cleaner_handler(raw_function, cleaners[c]['function'], name=cleaners[c]['name'])
                )
            ])
            globals()[cleaners[c]['name']] = make_cleaner_function(
                raw_function,
                cleaners[c]['function'],
                name=cleaners[c]['name']
            )
        app.add_routes([
            aiohttp.web.get(raw_google_ajax, e._local_url(), make_ajax_raw_handler(e.remote_url))
        ])

# Rosters
@register_cleaner("course_roster", "roster", ENDPOINTS)
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


@register_cleaner("course_list", "courses", ENDPOINTS)
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


@register_cleaner("document", "doctext")
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
        lengths = [f['endIndex'] - f['startIndex'] for f in flat]
        text_chunks = [_force_text_length(chunk, length) for chunk, length in zip(text_chunks, lengths)]
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


@register_cleaner("coursework_submissions", "assigned_docs")
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


if __name__ == '__main__':
    import json
    import sys
    j = json.load(open(sys.argv[1]))
    # extract_text_from_google_doc_json(j, align=False, EXTRACT_DEBUG_CHECKS=True)
    # extract_text_from_google_doc_json(j, align=True, EXTRACT_DEBUG_CHECKS=True)
    output = clean_assignment_docs(j)
    print(json.dumps(output, indent=2))
