import json
import requests
import configparser

# import aiohttp
# import aiohttp.web


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

# def initialize_and_register_routes(app):
#     app.add_routes([
#         aiohttp.web.get("/google", api_docs_handler)
#     ])

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
    test()
