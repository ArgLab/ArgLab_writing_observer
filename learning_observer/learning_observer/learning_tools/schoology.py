import json
import requests
import configparser
from requests_oauthlib import OAuth1

class Schoology:
    def __init__(self, config_path='./config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        API_KEY = self.config['SCHOOLOGY_CONFIG']['API_KEY']
        SECRET = self.config['SCHOOLOGY_CONFIG']['SECRET']
        self.auth = OAuth1(API_KEY, SECRET, "", "")
        self.base_url = f'https://api.schoology.com/v1/'

    # REST Methods
    def _get(self,uri):
        return requests.get(uri, auth=self.auth)

    def _post(self,uri,data):
        return requests.post(uri, json=data, auth=self.auth)

    def _put(self,uri,data):
        return requests.post(uri, json=data, auth=self.auth)

    def _delete(self,uri):
        return requests.delete(uri, auth=self.auth)
    
    def api_call(self, method, endpoint, params=None, data=None, absolute_url=False, retry=True):        
        if absolute_url:
            url = endpoint
        else:
            url = self.base_url + endpoint
            # Append params key/values if added
            if params:
                url += '?' + '&'.join(f"{k}={v}" for k, v in params.items())

        response_func = getattr(requests, method.lower())
        response = response_func(url, auth=self.auth, params=params, data=json.dumps(data) if data else None)
        
        if response.status_code != 200:
            response.raise_for_status()
        
        return response.json()


    # Schoology API calls

    #can be used to retrieve user information if email of the student is known
    def get_user_id(self,email,users=None):
        if(not users): users = self.list_users()
        for user in users:
            if(user['primary_email'] == email): return user['id']
        return "No Schoology ID found for: {}".format(email)
    
    #returns user information if the user id is avaialable
    def view_user(self,id):
        uri = 'https://api.schoology.com/v1/users/{0}'.format(id)
        return self._get(uri)

    #can be used to delete the user if the user id is known
    def delete_user(self,id):
        uri = 'https://api.schoology.com/v1/users/{0}?email_notification=0'.format(id)
        return self._delete(uri)

    #used to retireve school ID if the email and user id or email is known
    def get_school_uid(self,email,users=None):
        if(not users): users = self.list_users()
        for user in users:
            if(user['primary_email'] == email): return user['school_uid']
        return "No Schoology ID found for: {}".format(email)

    def list_users(self,role_id=None):
        uri = 'https://api.schoology.com/v1/users?limit=150'
        if(role_id): uri += "&role_ids={}".format(role_id)
        response = self._get(uri).json()
        if('do not exist' not in response):
            users = response['user']
            links = response['links']
            try:
                while(links['next'] != ''):
                    uri = links['next']
                    response = self._get(uri).json()
                    links = response['links']
                    u = response['user']
                    users += u # append paginated results to users json
            except KeyError: pass   # no next page will throw KeyError
            return users
        else:
            return "Role {} does not exist.".format(role_id)

    #can be used to create a user
    def create_user(self, user):
        uri = 'https://api.schoology.com/v1/users'
        return self._post(uri,user)
    
    #lists all the users in the system
    def list_all_users(self):
        return self.api_call('GET', 'users')
    
    #lists all the sections in the system
    def list_all_sections(self):
        return self.api_call('GET', 'sections')
    
    #In progress
    def get_section(self,userid):
        return self.api_call('GET', 'users/{0}/sections')
    
    def get_courses_for_students(self, userid):
        uri = 'https://api.schoology.com/v1/[realm]/enrollments/'.format(userid)

    #returns all the courses in the system
    def get_courses(self):
        uri =' https://api.schoology.com/v1/courses'
        return self._get(uri)
    
    def get_events(self):
        self.get_sections()
        today = date.today().isoformat()
        events = self.make_api_request("events", {"start_date": today}).get("event", [])
        temp = []

        for event in events:
            try:
                temp.append(
                    {
                        "name": event["title"],
                        "description": event["description"],
                        "course_id": event["section_id"],
                        "assignment_id": event["assignment_id"],
                        "date": event["start"],
                        "all_day": event["all_day"],
                    }
                )
            except KeyError:
                continue

        self.events = temp


def test():
    schoology = Schoology()
    
    all_users = schoology.list_all_users()
    print(f"All Users: {all_users}")
    
    all_sections = schoology.list_all_sections()
    print(f"All Sections: {all_sections}")


if __name__ == '__main__':
    test()
    