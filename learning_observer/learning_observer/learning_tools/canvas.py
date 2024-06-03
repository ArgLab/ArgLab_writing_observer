import json
import string
import requests
import recordclass
import configparser

import aiohttp
import aiohttp.web

import learning_observer.settings as settings
import learning_observer.log_event
import learning_observer.util
import learning_observer.auth
import learning_observer.runtime

cache = None

class Endpoint(recordclass.make_dataclass("Endpoint", ["name", "remote_url", "doc", "cleaners"], defaults=["", None])):
    def arguments(self):
        return extract_parameters_from_format_string(self.remote_url)

    def _local_url(self):
        parameters = "}/{".join(self.arguments())
        base_url = f"/google/{self.name}"
        if len(parameters) == 0:
            return base_url
        else:
            return base_url + "/{" + parameters + "}"

    def _add_cleaner(self, name, cleaner):
        if self.cleaners is None:
            self.cleaners = dict()
        self.cleaners[name] = cleaner
        if 'local_url' not in cleaner:
            cleaner['local_url'] = self._local_url + "/" + name

    def _cleaners(self):
        if self.cleaners is None:
            return []
        else:
            return self.cleaners

ENDPOINTS = list(map(lambda x: Endpoint(*x), [
    ("course_list", "/courses"),
    ("course_roster", "/courses/{courseId}/students"),
    ("course_work", "/courses/{courseId}/assignments"),
    ("coursework_submissions", "/courses/{courseId}/assignments/{assignmentId}/submissions"),
    # ("coursework_materials", "/courses/{courseId}/courseWorkMaterials"),
    # ("course_topics", "https://classroom.googleapis.com/v1/courses/{courseId}/topics"),
]))


def extract_parameters_from_format_string(format_string):
    '''
    Extracts parameters from a format string. E.g.

    >>> ("hello {hi} my {bye}")]
    ['hi', 'bye']
    '''
    # The parse returns a lot of context, which we discard. In particular, the
    # last item is often about the suffix after the last parameter and may be
    # `None`
    return [f[1] for f in string.Formatter().parse(format_string) if f[1] is not None]

class Canvas:
    def __init__(self, config_path='./config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.defaultServer = self.config['CANVAS_CONFIG']['DEFAULT_SERVER']
        self.access_token = self.config['CANVAS_CONFIG']['ACCESS_TOKEN']
        self.refresh_token = self.config['CANVAS_CONFIG']['REFRESH_TOKEN']
        self.client_id = self.config['CANVAS_CONFIG']['CLIENT_ID']
        self.client_secret = self.config['CANVAS_CONFIG']['CLIENT_SECRET']
        self.default_version = 'v1'
        self.defaultPerPage = 10000
        self.base_url = f'https://{self.defaultServer}/api/{self.default_version}'

    def update_access_tokens(self, access_token):
        self.config['CANVAS_CONFIG']['ACCESS_TOKEN'] = access_token
        self.access_token = access_token
        with open('./config.ini', 'w') as configfile:
            self.config.write(configfile)

    def api_call(self, method, endpoint, params=None, data=None, absolute_url=False, retry=True):        
        if absolute_url:
            url = endpoint
        else:
            url = self.base_url + endpoint
            # Append params key/values if added
            if params:
                url += '?' + '&'.join(f"{k}={v}" for k, v in params.items())

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        response_func = getattr(requests, method.lower())
        response = response_func(url, headers=headers, params=params, data=json.dumps(data))
        
        # Handle invalid/expired token
        if response.status_code == 401 and retry:
            new_tokens = self.refresh_tokens()
            if 'access_token' in new_tokens:
                self.update_access_tokens(new_tokens['access_token'])
                return self.api_call(method, endpoint, params, data, absolute_url, retry=False)
        
        if response.status_code != 200:
            response.raise_for_status()
        
        return response.json()

    def refresh_tokens(self):
        url = f'https://{self.defaultServer}/login/oauth2/token'
        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        return self.api_call('POST', url, params=params, absolute_url=True)

    def get_users(self):
        return self.api_call('GET', '/accounts/self/users')

    def get_courses(self):
        return self.api_call('GET', '/courses', params={'per_page': self.defaultPerPage})
    
    def get_course_enrollment(self, course_id):
        return self.api_call('GET', f'/courses/{course_id}/students', params={'per_page': self.defaultPerPage})
    
    def get_course_teachers(self, course_id):
        return self.api_call('GET', f'/courses/{course_id}/users', params={'per_page': self.defaultPerPage, 'enrollment_type[]': 'teacher'})

    def get_course_assignments(self, course_id):
        return self.api_call('GET', f'/courses/{course_id}/assignments', params={'per_page': self.defaultPerPage})

async def raw_canvas_ajax(runtime, target_url, **kwargs):
    '''
    Make an AJAX call to Canvas, managing auth + auth.

    * runtime is a Runtime class containing request information.
    * default_url is typically grabbed from ENDPOINTS
    * ... and we pass the named parameters
    '''
    # request = runtime.get_request()
    request = {
        "auth_headers": {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    }
    url = target_url.format(**kwargs)
    # cache_key = "raw_canvas/" + learning_observer.util.url_pathname(url)
    # if settings.feature_flag('use_google_ajax') is not None:
    #     value = await cache[cache_key]
    #     if value is not None:
    #         return learning_observer.util.translate_json_keys(
    #             json.loads(value),
    #             GOOGLE_TO_SNAKE
    #         )

    async with aiohttp.ClientSession(loop=request.app.loop) as client:
        if 'auth_headers' not in request:
            raise aiohttp.web.HTTPUnauthorized(text="Please log in")  # TODO: Consistent way to flag this
        async with client.get(url, headers=request["auth_headers"]) as resp:
            # Handle invalid/expired token
            # if resp.status_code == 401 and retry:
            #     new_tokens = self.refresh_tokens()
            #     if 'access_token' in new_tokens:
            #         self.update_access_tokens(new_tokens['access_token'])
            #         async with client.get(url, headers=request["auth_headers"]) as resp:
            #             response = await resp.json()
            #             learning_observer.log_event.log_ajax(target_url, response, request)
            #             # if settings.feature_flag('use_google_ajax') is not None:
            #             #     await cache.set(cache_key, json.dumps(response, indent=2))
            #             return response
                
            response = await resp.json()
            learning_observer.log_event.log_ajax(target_url, response, request)
            # if settings.feature_flag('use_google_ajax') is not None:
            #     await cache.set(cache_key, json.dumps(response, indent=2))
            return response

def raw_access_partial(remote_url, name=None):
    '''
    This is a helper which allows us to create a function which calls specific
    Canvas APIs.

    To test this, try:

        print(await raw_document(request, documentId="some_google_doc_id"))
    '''
    async def caller(request, **kwargs):
        '''
        Make an AJAX request to Google
        '''
        return await raw_canvas_ajax(request, remote_url, **kwargs)
    setattr(caller, "__qualname__", name)

    return caller

def initialize_and_register_routes(app):
    '''
    This is a big 'ol function which might be broken into smaller ones at some
    point. We:

    - Created debug routes to pass through AJAX requests to Google
    - Created production APIs to have access to cleaned versions of said data
    - Create local function calls to call from other pieces of code
      within process

    We probably don't need all of this in production, but a lot of this is
    very important for debugging. Having APIs is more useful than it looks, since
    making use of Google APIs requires a lot of infrastructure (registering
    apps, auth/auth, etc.) which we already have in place on dev / debug servers.
    '''
    # # For now, all of this is behind one big feature flag. In the future,
    # # we'll want seperate ones for the debugging tools and the production
    # # staff
    # if 'google_routes' not in settings.settings['feature_flags']:
    #     return

    # for key in ['save_google_ajax', 'use_google_ajax', 'save_clean_ajax', 'use_clean_ajax']:
    #     if key in settings.settings['feature_flags']:
    #         global cache
    #         cache = learning_observer.kvs.FilesystemKVS(path=learning_observer.paths.data('google'), subdirs=True)

    # Provide documentation on what we're doing
    app.add_routes([
        aiohttp.web.get("/canvas", api_docs_handler)
    ])

    def make_ajax_raw_handler(remote_url):
        '''
        This creates a handler to forward Google requests to the client. It's used
        for debugging right now. We should think through APIs before relying on this.
        '''
        async def ajax_passthrough(request):
            '''
            And the actual handler....
            '''
            request = {
                "auth_headers": {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            }
            runtime = learning_observer.runtime.Runtime(request)
            response = await raw_canvas_ajax(
                runtime,
                remote_url,
                **request.match_info
            )

            return aiohttp.web.json_response(response)
        return ajax_passthrough

    def make_cleaner_handler(raw_function, cleaner_function, name=None):
        async def cleaner_handler(request):
            '''
            '''
            response = cleaner_function(
                await raw_function(request, **request.match_info)
            )
            if isinstance(response, dict) or isinstance(response, list):
                return aiohttp.web.json_response(
                    response
                )
            elif isinstance(response, str):
                return aiohttp.web.Response(
                    text=response
                )
            else:
                raise AttributeError(f"Invalid response type: {type(response)}")
        if name is not None:
            setattr(cleaner_handler, "__qualname__", name + "_handler")

        return cleaner_handler

    def make_cleaner_function(raw_function, cleaner_function, name=None):
        async def cleaner_local(request, **kwargs):
            canvas_response = await raw_function(request, **kwargs)
            clean = cleaner_function(canvas_response)
            return clean
        if name is not None:
            setattr(cleaner_local, "__qualname__", name)
        return cleaner_local

    for e in ENDPOINTS:
        function_name = f"raw_{e.name}"
        raw_function = raw_access_partial(remote_url=e.remote_url, name=e.name)
        globals()[function_name] = raw_function
        cleaners = e._cleaners()
        for c in cleaners:
            app.add_routes([
                aiohttp.web.get(
                    cleaners[c]['local_url'],
                    make_cleaner_handler(
                        raw_function,
                        cleaners[c]['function'],
                        name=cleaners[c]['name']
                    )
                )
            ])
            globals()[cleaners[c]['name']] = make_cleaner_function(
                raw_function,
                cleaners[c]['function'],
                name=cleaners[c]['name']
            )
        app.add_routes([
            aiohttp.web.get(
                e._local_url(),
                make_ajax_raw_handler(e.remote_url)
            )
        ])

def api_docs_handler(request):
    '''
    Return a list of available endpoints.

    Eventually, we should also document available function calls
    '''
    response = "URL Endpoints:\n\n"
    for endpoint in ENDPOINTS:
        response += f"{endpoint._local_url()}\n"
        cleaners = endpoint._cleaners()
        for c in cleaners:
            response += f"   {cleaners[c]['local_url']}\n"
    response += "\n\n Globals:"
    return aiohttp.web.Response(text=response)

def register_cleaner(data_source, cleaner_name):
    '''
    This will register a cleaner function, for export both as a web service
    and as a local function call.
    '''
    def decorator(f):
        found = False
        for endpoint in ENDPOINTS:
            if endpoint.name == data_source:
                found = True
                endpoint._add_cleaner(
                    cleaner_name,
                    {
                        'function': f,
                        'local_url': f'{endpoint._local_url()}/{cleaner_name}',
                        'name': cleaner_name
                    }
                )

        if not found:
            raise AttributeError(f"Data source {data_source} invalid; not found in endpoints.")
        return f

    return decorator

# Rosters
@register_cleaner("course_roster", "roster")
def clean_course_roster(canvas_json):
    '''
    Retrieve the roster for a course, alphabetically
    '''
    students = canvas_json.get('students', [])
    students.sort(
        key=lambda x: x.get('name', {}).get('fullName', 'ZZ'),
    )
    # Convert Google IDs to internal ideas (which are the same, but with a gc- prefix)
    for student_json in students:
        google_id = student_json['profile']['id']
        local_id = learning_observer.auth.google_id_to_user_id(google_id)
        student_json['user_id'] = local_id
        del student_json['profile']['id']

        # For the present there is only one external id so we will add that directly.
        if 'external_ids' not in student_json['profile']:
            student_json['profile']['external_ids'] = []
        student_json['profile']['external_ids'].append({"source": "google", "id": google_id})
    return students

@register_cleaner("course_list", "courses")
def clean_course_list(canvas_json):
    '''
    Google's course list is one object deeper than we'd like, and alphabetic
    sort order is nicer. This will clean it up a bit
    '''
    courses = canvas_json.get('courses', [])
    courses.sort(
        key=lambda x: x.get('name', 'ZZ'),
    )
    return courses


def test():
    canvas = Canvas()
    
    users = canvas.get_users()
    print(f'Users: {users} \n')
    
    courses = canvas.get_courses()
    print(f'Courses: {courses} \n')
    
    for course in courses:
        students = canvas.get_course_enrollment(course.get('id'))
        print(f'Students taking {course.get("name")} course are: {students} \n')
        
        teachers = canvas.get_course_teachers(course.get('id'))
        print(f'Teachers managing {course.get("name")} course are: {teachers} \n')
        
        assignments = canvas.get_course_assignments(course.get('id'))
        print(f'Assignments under {course.get("name")} course are: {assignments} \n')
        
        
if __name__ == '__main__':
    import json
    import sys
    # j = json.load(open(sys.argv[1]))
    # output = clean_course_roster(j)
    output = clean_course_roster("")
    print(json.dumps(output, indent=2))