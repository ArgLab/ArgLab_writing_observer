import os
import json
import recordclass
import string
from requests_oauthlib import OAuth1
import configparser
import aiohttp
import aiohttp.web
from requests import Request

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
        base_url = f"/schoology/{self.name}"
        if len(parameters) == 0:
            return base_url
        else:
            return base_url + "/{" + parameters + "}"

    def _add_cleaner(self, name, cleaner):
        if self.cleaners is None:
            self.cleaners = dict()
        self.cleaners[name] = cleaner
        if 'local_url' not in cleaner:
            cleaner['local_url'] = self._local_url() + "/" + name

    def _cleaners(self):
        if self.cleaners is None:
            return []
        else:
            return self.cleaners

ENDPOINTS = list(map(lambda x: Endpoint(*x), [
    ("course_list", "/sections"),
    ("course_roster", "/sections/{sectionId}/enrollments"),
    ("course_work", "/sections/{sectionId}/assignments"),
    ("coursework_submissions", "/sections/{courseId}/assignments/{assignmentId}/submissions/{gradeItemId}"),
]))

def extract_parameters_from_format_string(format_string):
    '''
    Extracts parameters from a format string. E.g.

    >>> extract_parameters_from_format_string("hello {hi} my {bye}")
    ['hi', 'bye']
    '''
    return [f[1] for f in string.Formatter().parse(format_string) if f[1] is not None]

class Schoology:
    def __init__(self, config_path='./config.ini'):
        # Get the absolute path to the configuration file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, config_path)

        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        # Check if 'SCHOOLOGY_CONFIG' section is present
        if 'SCHOOLOGY_CONFIG' not in self.config:
            raise KeyError("The configuration file does not contain 'SCHOOLOGY_CONFIG' section")
        
        try:
            self.api_key = self.config['SCHOOLOGY_CONFIG']['API_KEY']
            self.secret = self.config['SCHOOLOGY_CONFIG']['SECRET']
        except KeyError as e:
            raise KeyError(f"Missing required configuration key: {e}")

        self.auth = OAuth1(self.api_key, self.secret, "", "")
        self.base_url = f'https://api.schoology.com/v1/'

    async def api_call(self, method, endpoint, params=None, data=None, absolute_url=False, retry=True):
        if absolute_url:
            url = endpoint
        else:
            url = self.base_url + endpoint
            if params:
                url += '?' + '&'.join(f"{k}={v}" for k, v in params.items())

        async with aiohttp.ClientSession() as client:
            response_func = getattr(client, method.lower())
            async with response_func(url, auth=self.auth, params=params, json=data) as response:
                if response.status != 200:
                    response.raise_for_status()
                
                return await response.json()
            
    def _sign_request(self, url, headers, data, method):
        req = Request(method, url, headers=headers, json=data)
        prepared = req.prepare()

        # Sign the request
        oauth = OAuth1(
            self.api_key,
            client_secret=self.secret,
            resource_owner_key=None,
            resource_owner_secret=None,
            signature_type='auth_header'
        )

	prepared = oauth(prepared)

        return prepared.url, prepared.headers, prepared.body

async def raw_schoology_ajax(runtime, target_url, retry=False, **kwargs):
    '''
    Make an AJAX call to Schoology, managing auth + auth.

    * runtime is a Runtime class containing request information.
    * target_url is typically grabbed from ENDPOINTS
    * ... and we pass the named parameters
    '''
    schoology = Schoology()
    
    params = {k: v for k, v in kwargs.items() if v is not None}
    try:
        response = await schoology.api_call('GET', target_url, params=params)
    except aiohttp.ClientResponseError as e:
        raise

    return response

def raw_access_partial(remote_url, name=None):
    '''
    This is a helper which allows us to create a function which calls specific
    Schoology APIs.
    '''
    async def caller(request, **kwargs):
        '''
        Make an AJAX request to Schoology
        '''
        return await raw_schoology_ajax(request, remote_url, **kwargs)
    setattr(caller, "__qualname__", name)
    
    return caller

def initialize_and_register_routes(app):
    '''
    Initialize and register routes for the application.
    '''
    app.add_routes([
        aiohttp.web.get("/schoology", api_docs_handler)
    ])

    def make_ajax_raw_handler(remote_url):
        async def ajax_passthrough(request):
            runtime = learning_observer.runtime.Runtime(request)
            response = await raw_schoology_ajax(runtime, remote_url, retry=True, **request.match_info)
            return aiohttp.web.json_response(response)
        return ajax_passthrough

    def make_cleaner_handler(raw_function, cleaner_function, name=None):
        async def cleaner_handler(request):
            response = cleaner_function(await raw_function(request, **request.match_info))
            if isinstance(response, dict) or isinstance(response, list):
                return aiohttp.web.json_response(response)
            elif isinstance(response, str):
                return aiohttp.web.Response(text=response)
            else:
                raise AttributeError(f"Invalid response type: {type(response)}")
        if name is not None:
            setattr(cleaner_handler, "__qualname__", name + "_handler")

        return cleaner_handler

    def make_cleaner_function(raw_function, cleaner_function, name=None):
        async def cleaner_local(request, **kwargs):
            schoology_response = await raw_function(request, **kwargs)
            clean = cleaner_function(schoology_response)
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
                    make_cleaner_handler(raw_function, cleaners[c]['function'], name=cleaners[c]['name'])
                )
            ])
            globals()[cleaners[c]['name']] = make_cleaner_function(raw_function, cleaners[c]['function'], name=cleaners[c]['name'])
        app.add_routes([
            aiohttp.web.get(e._local_url(), make_ajax_raw_handler(e.remote_url))
        ])

def api_docs_handler(request):
    response = "URL Endpoints:\n\n"
    for endpoint in ENDPOINTS:
        response += f"{endpoint._local_url()}\n"
        cleaners = endpoint._cleaners()
        for c in cleaners:
            response += f"   {cleaners[c]['local_url']}\n"
    response += "\n\n Globals:"
    return aiohttp.web.Response(text=response)

def register_cleaner(data_source, cleaner_name):
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

@register_cleaner("course_roster", "roster")
def clean_course_roster(schoology_json):
    students = schoology_json.get('enrollments', [])
    students.sort(key=lambda x: x.get('name', 'ZZ'))
    for student_json in students:
        schoology_id = student_json['id']
        local_id = learning_observer.auth.schoology_id_to_user_id(schoology_id)
        student_json['user_id'] = local_id
        if 'external_ids' not in student_json:
            student_json['external_ids'] = []
        student_json['external_ids'].append({"source": "schoology", "id": schoology_id})
    return students

@register_cleaner("course_list", "courses")
def clean_course_list(schoology_json):
    courses = schoology_json.get('courses', [])
    courses.sort(key=lambda x: x.get('title', 'ZZ'))
    return courses
        
if __name__ == '__main__':
    output = clean_course_roster({})
    print(json.dumps(output, indent=2))
