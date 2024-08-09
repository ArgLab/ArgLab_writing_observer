import os
import configparser
import aiohttp
import aiohttp.web

import learning_observer.log_event
import learning_observer.util
import learning_observer.auth
import learning_observer.runtime

from learning_observer.lms_integration import BaseLMS, Endpoint, register_cleaner

CANVAS_ENDPOINTS = list(map(lambda x: Endpoint(*x, "", None, "canvas"), [
    ("course_list", "/courses"),
    ("course_roster", "/courses/{courseId}/students"),
    ("course_work", "/courses/{courseId}/assignments"),
    ("coursework_submissions", "/courses/{courseId}/assignments/{assignmentId}/submissions"),
]))

class Canvas:
    def __init__(self, config_path='./config.ini'):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, config_path)
        
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        try:
            self.defaultServer = self.config['CANVAS_CONFIG']['DEFAULT_SERVER']
            self.access_token = self.config['CANVAS_CONFIG']['ACCESS_TOKEN']
            self.refresh_token = self.config['CANVAS_CONFIG']['REFRESH_TOKEN']
            self.client_id = self.config['CANVAS_CONFIG']['CLIENT_ID']
            self.client_secret = self.config['CANVAS_CONFIG']['CLIENT_SECRET']
        except KeyError as e:
            raise KeyError(f"Missing required configuration key: {e}")
        self.default_version = 'v1'
        self.defaultPerPage = 10000
        self.base_url = f'https://{self.defaultServer}/api/{self.default_version}'

    def update_access_tokens(self, access_token):
        self.config['CANVAS_CONFIG']['ACCESS_TOKEN'] = access_token
        self.access_token = access_token
        script_dir = os.path.dirname(os.path.abspath(__file__))
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

        
class CanvasLMS(BaseLMS):
    def __init__(self):
        super().__init__(lms_name="canvas", endpoints=CANVAS_ENDPOINTS, raw_ajax_function=self.raw_canvas_ajax)
        self.canvas = Canvas()

    async def raw_canvas_ajax(self, runtime, target_url, retry=False, **kwargs):
        '''
        Make an AJAX call to Canvas, managing auth + auth.

        * runtime is a Runtime class containing request information.
        * target_url is typically grabbed from ENDPOINTS
        * ... and we pass the named parameters
        '''
        params = {k: v for k, v in kwargs.items() if v is not None}
        try:
            response = await self.canvas.api_call('GET', target_url, params=params, **kwargs)
        except aiohttp.ClientResponseError as e:
            if e.status == 401 and retry:
                new_tokens = await self.canvas.refresh_tokens()
                if 'access_token' in new_tokens:
                    self.canvas.update_access_tokens(new_tokens['access_token'])
                    return await self.raw_canvas_ajax(runtime, target_url, retry=False, **kwargs)
            raise
        return response
    
    @register_cleaner("course_roster", "roster", CANVAS_ENDPOINTS)
    def clean_course_roster(canvas_json):
        students = canvas_json
        students_updated = []
        for student_json in students:
            canvas_id = student_json['id']
            integration_id = student_json['integration_id']
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
            if 'external_ids' not in student_json:
                student_json['external_ids'] = []
            student_json['external_ids'].append({"source": "canvas", "id": integration_id})
            students_updated.append(student)
        return students_updated

    @register_cleaner("course_list", "courses", CANVAS_ENDPOINTS)
    def clean_course_list(canvas_json):
        courses = canvas_json
        courses.sort(key=lambda x: x.get('name', 'ZZ'))
        return courses
    
canvas_lms = CanvasLMS()

def initialize_canvas_routes(app):
    canvas_lms.initialize_routes(app)