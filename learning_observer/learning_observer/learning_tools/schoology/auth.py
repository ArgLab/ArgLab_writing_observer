import requests
import configparser
import schoolopy

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

class Auth:
    def __init__(self, client_id, client_secret, domain='https://www.schoology.com'):
        self.API_ROOT = 'https://api.schoology.com/v1'
        self.DOMAIN_ROOT = domain

        self.client_id = client_id
        self.client_secret = client_secret

        self.access_token = None

    def _get_authorization_header(self):
        return f"Bearer {self.access_token}"

    def _request_header(self):
        return {
            'Authorization': self._get_authorization_header(),
            'Accept': 'application/json',
            'Host': 'api.schoology.com',
            'Content-Type': 'application/json'
        }

    def request_authorization(self, redirect_uri=None, scope=None):
        if redirect_uri is None:
            redirect_uri = 'https://gayaan.csc.ncsu.edu/callback'
        
        if scope is None:
            scope = 'user:read'  # Add your desired scopes here

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': scope
        }

        authorization_url = f"{self.DOMAIN_ROOT}/oauth/authorize?{urlencode(params)}"
        return authorization_url

    def exchange_authorization_code(self, authorization_code, redirect_uri=None):
        if redirect_uri is None:
            redirect_uri = 'https://gayaan.csc.ncsu.edu/callback'
        
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': redirect_uri
        }

        response = requests.post(f"{self.API_ROOT}/oauth2/token", data=data)
        if response.status_code == 200:
            token_info = response.json()
            self.access_token = token_info['access_token']
            return token_info
        else:
            raise Exception("Failed to exchange authorization code for access token.")

    # Additional methods for making API requests can be implemented here

def test():
    # Get client ID and secret from config file
    config = configparser.ConfigParser()
    config.read('config.ini')
    CLIENT_ID = config['SCHOOLOGY_CLIENT']['API_KEY']
    CLIENT_SECRET = config['SCHOOLOGY_CLIENT']['SECRET']

    auth = Auth(CLIENT_ID, CLIENT_SECRET)
    
    sc = schoolopy.Schoology(schoolopy.Auth(CLIENT_ID, CLIENT_SECRET))
    sc.get_feed()

    # Request authorization URL
    authorization_url = auth.request_authorization(redirect_uri='https://gayaan.csc.ncsu.edu')
    print("Authorization URL:", authorization_url)

    # Prompt the user to visit the authorization URL and grant access
    # After granting access, the user will be redirected to the callback URL
    # Make sure to handle the callback URL in your application to retrieve the authorization code

    # Simulate the retrieval of the authorization code from the callback URL
    authorization_code = input("Enter the authorization code from the callback URL: ")

    # # Exchange the authorization code for an access token
    # token_info = auth.exchange_authorization_code(authorization_code, redirect_uri='https://gayaan.csc.ncsu.edu')
    # print("Access Token:", token_info['access_token'])

    # # Use the access token to make API requests
    # # Example API request
    # url = auth.API_ROOT + '/users/me'
    # headers = auth._request_header()
    # response = requests.get(url, headers=headers)
    # if response.status_code == 200:
    #     print("API request successful.")
    #     data = response.json()
    #     # Process the API response data
    # else:
    #     print("API request failed with status code:", response.status_code)


if __name__ == '__main__':
    test()
    