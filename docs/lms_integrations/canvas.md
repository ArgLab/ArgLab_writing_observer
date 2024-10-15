## Canvas LMS Documentation: 
Reference: https://canvas.instructure.com/doc/api/file.oauth.html

This guide will walk you through the process of obtaining the `client_id`, `client_secret`, and `refresh_token` for interacting with the Canvas LMS API. These credentials are essential for making authenticated API requests to Canvas.

### Prerequisites

- You need to have administrator access to the Canvas LMS instance.

### Steps to Obtain the `client_id` and `client_secret`

1. **Log in to Your Canvas LMS Account**:
   - Go to your Canvas LMS instance and log in with your administrator credentials.

2. **Navigate to the Developer Keys Section**:
   - From the Canvas dashboard, click on the **Admin** panel located on the left-hand side.
   - Select the specific account (usually your institution's name) where you want to manage developer keys.
   - Scroll down and click on **Developer Keys** in the left-hand menu under the **Settings** section.

3. **Create a New Developer Key**:
   - In the Developer Keys section, click the **+ Developer Key** button at the top-right corner.
   - Choose **API Key** from the dropdown menu.

4. **Fill Out the Developer Key Details**:
   - **Name**: Enter a name for the Developer Key (e.g., "My Canvas API Integration").
   - **Owner's Email**: Enter administrator's email.
   - **Redirect URIs**: Provide the redirect URI that will handle OAuth callbacks. This is typically a URL on your institution server where you handle OAuth responses.

5. **Save and Enable the Developer Key**:
   - After filling out the required information, click **Save Key**.
   - Ensure the key is **enabled** by toggling the switch next to your newly created key.

6. **Obtain the `client_id` and `client_secret`**:
   - After saving, your `client_id` and `client_secret` will be displayed in the list of developer keys.
   - **Client ID**: This is usually displayed as a numeric value in the details column.
   - **Client Secret**: Click on the `show key` button and it will display the `client_secret`.

### Steps to Obtain the `refresh_token`

1. **Redirect User to Canvas Authorization Endpoint**:
   - To obtain the `refresh_token`, you need to perform an OAuth flow.
   - Direct the user to the Canvas OAuth authorization endpoint:
     ```
     https://canvas.instructure.com/login/oauth2/auth?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=YOUR_REDIRECT_URI
     ```
   - Replace `YOUR_CLIENT_ID` with the `client_id` obtained earlier and `YOUR_REDIRECT_URI` with the redirect URI you configured.

2. **User Authorizes the Application**:
   - The user will be prompted to log in (if not already logged in) and authorize the application to access their Canvas data.

3. **Handle the Authorization Code**:
   - After the user authorizes the application, they will be redirected to the `redirect_uri` you provided, with an authorization `code` appended as a query parameter.
   - Example: `https://your-redirect-uri.com?code=AUTHORIZATION_CODE`

4. **Exchange the Authorization Code for a Refresh Token**:
   - Use the authorization `code` to request an access token and refresh token by making a POST request to the Canvas token endpoint:
     ```
     POST https://canvas.instructure.com/login/oauth2/token
     ```
   - Include the following parameters in the request body:
     - `client_id`: Your Canvas `client_id`
     - `client_secret`: Your Canvas `client_secret`
     - `redirect_uri`: Your `redirect_uri` used in the authorization request
     - `code`: The authorization code you received
     - `grant_type`: Set this to `authorization_code`

   - Example of the POST request in `curl`:
     ```bash
     curl -X POST https://canvas.instructure.com/login/oauth2/token \
       -F 'client_id=YOUR_CLIENT_ID' \
       -F 'client_secret=YOUR_CLIENT_SECRET' \
       -F 'redirect_uri=YOUR_REDIRECT_URI' \
       -F 'code=AUTHORIZATION_CODE' \
       -F 'grant_type=authorization_code'
     ```

5. **Extract the Refresh Token**:
   - The response to the token request will include an `access_token`, a `refresh_token`, and other token information.
   - **Refresh Token**: This token can be used to obtain new access tokens without requiring the user to re-authorize.

### Example JSON Response from Token Request

```json
{
  "access_token": "ACCESS_TOKEN",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "REFRESH_TOKEN",
  "user": {
    "id": 12345,
    "name": "John Doe",
    "sortable_name": "Doe, John",
    "short_name": "John"
  }
}
```

- **`refresh_token`**: The value you will need to store securely for future use.

### Important Notes

- **Security**: The `client_id`, `client_secret`, and `refresh_token` should be stored securely. Do not expose them in client-side code or public repositories.
- **Token Expiration**: The `access_token` typically expires after a short period (e.g., 1 hour). The `refresh_token` does not expire as quickly and can be used to obtain new `access_token`s.

### Conclusion

By following these steps, you will obtain the necessary credentials (`client_id`, `client_secret`, and `refresh_token`) to interact with the Canvas LMS API programmatically. These credentials are essential for making authenticated requests to access and manage Canvas resources through the API.