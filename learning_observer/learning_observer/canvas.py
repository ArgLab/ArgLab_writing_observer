import os
import json
import string
import requests
import recordclass
import configparser
import aiohttp
import aiohttp.web
import pmss
import yaml

import learning_observer.settings as settings
import learning_observer.log_event
import learning_observer.util
import learning_observer.auth
import learning_observer.runtime

cache = None

pmss.register_field(
    name="default_server",
    type=pmss.pmsstypes.TYPES.string,
    description="The default server for Canva",
    required=True
)
pmss.register_field(
    name="client_id",
    type=pmss.pmsstypes.TYPES.string,
    description="The client ID for Canva",
    required=True
)
pmss.register_field(
    name="client_secret",
    type=pmss.pmsstypes.TYPES.string,
    description="The client secret for Canva",
    required=True
)
pmss.register_field(
    name="access_token",
    type=pmss.pmsstypes.TYPES.string,
    description="The access token for Canva",
    required=True
)
pmss.register_field(
    name="refresh_token",
    type=pmss.pmsstypes.TYPES.string,
    description="The refresh token for Canva",
    required=True
)

class Endpoint(recordclass.make_dataclass("Endpoint", ["name", "remote_url", "doc", "cleaners"], defaults=["", None])):
    def arguments(self):
        return extract_parameters_from_format_string(self.remote_url)

    def _local_url(self):
        parameters = "}/{".join(self.arguments())
        base_url = f"/canvas/{self.name}"
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
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, config_path)
        
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        # Check if 'SCHOOLOGY_CONFIG' section is present
        if 'CANVAS_CONFIG' not in self.config:
            raise KeyError("The configuration file does not contain 'CANVAS_CONFIG' section")
        
        try:
            self.defaultServer = self.config['CANVAS_CONFIG']['DEFAULT_SERVER']
            self.access_token = self.config['CANVAS_CONFIG']['ACCESS_TOKEN']
            self.refresh_token = self.config['CANVAS_CONFIG']['REFRESH_TOKEN']
            self.client_id = self.config['CANVAS_CONFIG']['CLIENT_ID']
            self.client_secret = self.config['CANVAS_CONFIG']['CLIENT_SECRET']
        except KeyError as e:
            raise KeyError(f"Missing required configuration key: {e}")
        
        """
        self.defaultServer = settings.pmss_settings.default_server(types=['canvas'])
        self.access_token = settings.pmss_settings.access_token(types=['canvas'])
        self.refresh_token = settings.pmss_settings.refresh_token(types=['canvas'])
        self.client_id = settings.pmss_settings.client_id(types=['canvas'])
        self.client_secret = settings.pmss_settings.client_secret(types=['canvas'])
        """
        self.default_version = 'v1'
        self.defaultPerPage = 10000
        self.base_url = f'https://{self.defaultServer}/api/{self.default_version}'

    def update_access_tokens(self, access_token):
        self.config['CANVAS_CONFIG']['ACCESS_TOKEN'] = access_token
        self.access_token = access_token
        script_dir = os.path.dirname(os.path.abspath(__file__))
        """
        config_path = os.path.join(script_dir, '../creds.yaml')
        with open(config_path, 'r') as configfile:
            config = yaml.safe_load(configfile)
        
        config['canvas']['access_token'] = access_token
        
        with open(config_path, 'w') as configfile:
            yaml.safe_dump(config, configfile, sort_keys=False)
        """
        config_path = os.path.join(script_dir, './config.ini')
        with open(config_path, 'w') as configfile:
            self.config.write(configfile)

    async def api_call(self, method, endpoint, params=None, data=None, absolute_url=False, retry=True, **kwargs):
        if absolute_url:
            url = endpoint
        else:
            url = self.base_url + endpoint
            #if params:
                #url += '?' + '&'.join(f"{k}={v}" for k, v in params.items())
        
        url = url.format(**kwargs)

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        async with aiohttp.ClientSession() as client:
            response_func = getattr(client, method.lower())
            async with response_func(url, headers=headers, params=params, json=data) as response:
                if response.status == 401 and retry:
                    new_tokens = await self.refresh_tokens()
                    if 'access_token' in new_tokens:
                        self.update_access_tokens(new_tokens['access_token'])
                        return await self.api_call(method, endpoint, params, data, absolute_url, retry=False, **kwargs)
                
                if response.status != 200:
                    response.raise_for_status()
                
                return await response.json()

    async def refresh_tokens(self):
        url = f'https://{self.defaultServer}/login/oauth2/token'
        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        return await self.api_call('POST', url, params=params, absolute_url=True)

async def raw_canvas_ajax(runtime, target_url, retry=False, **kwargs):
    '''
    Make an AJAX call to Canvas, managing auth + auth.

    * runtime is a Runtime class containing request information.
    * target_url is typically grabbed from ENDPOINTS
    * ... and we pass the named parameters
    '''
    canvas = Canvas()
    
    params = {k: v for k, v in kwargs.items() if v is not None}
    try:
        response = await canvas.api_call('GET', target_url, params=params, **kwargs)
        #response["kwargs"] = kwargs
    except aiohttp.ClientResponseError as e:
        if e.status == 401 and retry:
            new_tokens = await canvas.refresh_tokens()
            if 'access_token' in new_tokens:
                canvas.update_access_tokens(new_tokens['access_token'])
                return await raw_canvas_ajax(runtime, target_url, retry=False, **kwargs)
        raise
    
    print(kwargs)
    return response

def raw_access_partial(remote_url, name=None):
    '''
    This is a helper which allows us to create a function which calls specific
    Canvas APIs.
    '''
    async def caller(request, **kwargs):
        '''
        Make an AJAX request to Canvas
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
    app.add_routes([
        aiohttp.web.get("/canvas", api_docs_handler)
    ])

    def make_ajax_raw_handler(remote_url):
        async def ajax_passthrough(request):
            runtime = learning_observer.runtime.Runtime(request)
            response = await raw_canvas_ajax(runtime, remote_url, retry=True, **request.match_info)
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
def clean_course_roster(canvas_json):
    students = canvas_json
    students_updated = []
    #students.sort(key=lambda x: x.get('name', {}).get('fullName', 'ZZ'))
    for student_json in students:
        canvas_id = student_json['id']
        integration_id = student_json['integration_id']
        #canvas_id = "118337587800688588675"
        local_id = learning_observer.auth.google_id_to_user_id(integration_id)
        student = {
            "course_id": "1",
            "user_id": local_id,
            "profile": {
                "id": canvas_id,
                "name": {
                    "given_name": student_json['name'],
                    "family_name": student_json['name'],
                    "full_name": student_json['name']
                }
            }
        }
        #local_id = learning_observer.auth.canvas_id_to_user_id(canvas_id)
        #student_json['user_id'] = local_id
        if 'external_ids' not in student_json:
            student_json['external_ids'] = []
        student_json['external_ids'].append({"source": "canvas", "id": integration_id})
        students_updated.append(student)
    return students_updated

@register_cleaner("course_list", "courses")
def clean_course_list(canvas_json):
    courses = canvas_json
    courses.sort(key=lambda x: x.get('name', 'ZZ'))
    return courses
        
if __name__ == '__main__':
    output = clean_course_roster({})
    print(json.dumps(output, indent=2))
