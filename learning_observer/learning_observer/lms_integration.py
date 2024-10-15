import json
import recordclass
import string
import aiohttp
import aiohttp.web

import learning_observer
import learning_observer.runtime
import learning_observer.google
import learning_observer.constants as constants
import learning_observer.settings as settings
import pmss

pmss.register_field(
    name="lms_api",
    type=pmss.pmsstypes.TYPES.string,
    description="The Canvas Base API URL",
    required=True
)

cache = None

class Endpoint(recordclass.make_dataclass("Endpoint", ["name", "remote_url", "doc", "cleaners", "lms"], defaults=["", None])):
    """
    The Endpoint class represents an API endpoint, allowing for parameter extraction,
    URL construction, and cleaner (function) management.
    
    Attributes:
        name (str): The name of the endpoint.
        remote_url (str): The remote URL of the endpoint, which may contain parameters.
        doc (str): Documentation or description of the endpoint.
        cleaners (dict): A dictionary of cleaner functions associated with the endpoint.
        lms (str): The learning management system (LMS) that the endpoint belongs to.
    """
    
    def arguments(self):
        """
        Extracts the parameters from the remote URL.

        Returns:
            list: A list of parameters extracted from the remote_url.
        """
        return extract_parameters_from_format_string(self.remote_url)

    def _local_url(self):
        """
        Constructs the local URL based on the LMS, endpoint name, and any parameters.

        Returns:
            str: The constructed local URL in the format "/{lms}/{name}/{parameters}".
            If there are no parameters, the URL will be "/{lms}/{name}".
        """
        parameters = "}/{".join(self.arguments())
        base_url = f"/{self.lms}/{self.name}"
        if len(parameters) == 0:
            return base_url
        else:
            return base_url + "/{" + parameters + "}"

    def _add_cleaner(self, name, cleaner):
        """
        Adds a cleaner function to the endpoint, assigning it a name. If the cleaner
        doesn't have a local URL, one is generated.

        Args:
            name (str): The name to associate with the cleaner.
            cleaner (dict): The cleaner function to be added, optionally containing 
                            additional metadata such as its local URL.
        """
        if self.cleaners is None:
            self.cleaners = dict()
        self.cleaners[name] = cleaner
        if 'local_url' not in cleaner:
            cleaner['local_url'] = self._local_url + "/" + name

    def _cleaners(self):
        """
        Retrieves the list of cleaner functions associated with the endpoint.

        Returns:
            list: A list of cleaner functions, or an empty list if no cleaners exist.
        """
        if self.cleaners is None:
            return []
        else:
            return self.cleaners

def extract_parameters_from_format_string(format_string):
    '''
    Extracts parameters from a format string. E.g.
    >>> ("hello {hi} my {bye}")]
    ['hi', 'bye']
    
    Args:
        format_string (str): The format string containing parameters enclosed in braces.

    Returns:
        list: A list of parameter names extracted from the format string.
    '''
    return [f[1] for f in string.Formatter().parse(format_string) if f[1] is not None]

def raw_access_partial(raw_ajax_function, target_url, name=None):
    '''
    Creates an asynchronous function that calls a specific LMS API.

    This helper function allows you to wrap an AJAX function to easily
    call a specific API endpoint.

    Args:
        raw_ajax_function (callable): The function to be called for making the AJAX request.
        target_url (str): The target URL for the API call.
        name (str, optional): The name to assign to the created function.

    Returns:
        callable: An asynchronous function that can be called to perform the AJAX request.
    '''
    async def ajax_caller(request, **kwargs):
        '''
        Make an AJAX request to LMS
        
        Args:
            request: The incoming request object.
            **kwargs: Additional keyword arguments to pass to the raw AJAX function.

        Returns:
            The response from the raw AJAX function.
        '''
        return await raw_ajax_function(request, target_url, **kwargs)
    setattr(ajax_caller, "__qualname__", name)

    return ajax_caller

def api_docs_handler(endpoints):
    '''
    Returns a list of available endpoints in a human-readable format.
    
    Eventually, we should also document available function calls

    Args:
        endpoints (list): A list of Endpoint objects to document.

    Returns:
        aiohttp.web.Response: A response object containing the documentation of endpoints.
    '''
    
    response = "URL Endpoints:\n\n"
    for endpoint in endpoints:
        response += f"{endpoint._local_url()}\n"
        cleaners = endpoint._cleaners()
        for c in cleaners:
            response += f"   {cleaners[c]['local_url']}\n"
    response += "\n\n Globals:"
    return aiohttp.web.Response(text=response)

def register_cleaner(data_source, cleaner_name, endpoints):
    '''
    Registers a cleaner function, allowing it to be exported both as a web service
    and as a local function call.

    Args:
        data_source (str): The name of the data source to associate with the cleaner.
        cleaner_name (str): The name of the cleaner function to register.
        endpoints (list): A list of Endpoint objects to search for the data source.

    Returns:
        callable: A decorator for registering the cleaner function.
    
    Raises:
        AttributeError: If the data source is not found in the endpoints.
    '''
    def add_cleaner(f):
        found = False
        for endpoint in endpoints:
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

    return add_cleaner

def make_ajax_raw_handler(raw_ajax_function, remote_url):
    '''
    Creates an AJAX passthrough handler that calls a raw AJAX function.

    This function handles requests and passes them to the specified raw AJAX function,
    returning the response as a JSON response.

    Args:
        raw_ajax_function (callable): The raw AJAX function to call.
        remote_url (str): The URL to which the AJAX request is sent.

    Returns:
        callable: An asynchronous function that handles AJAX requests.
    '''
    async def ajax_passthrough(request):
        '''
        Handle the AJAX request by calling the raw AJAX function.

        Args:
            request: The incoming request object.

        Returns:
            aiohttp.web.json_response: A JSON response containing the result of the AJAX function.
        '''
        runtime = learning_observer.runtime.Runtime(request)
        response = await raw_ajax_function(runtime, remote_url, retry=True, **request.match_info)
        return aiohttp.web.json_response(response)
    return ajax_passthrough

def make_cleaner_handler(raw_function, cleaner_function, name=None):
    '''
    Creates a handler for the cleaner function.

    This function will process the input from the raw function, apply the cleaner,
    and return the cleaned response.

    Args:
        raw_function (callable): The raw function to call.
        cleaner_function (callable): The function to clean the response from the raw function.
        name (str, optional): The name to assign to the created function.

    Returns:
        callable: An asynchronous function that handles requests and cleans the responses.
    '''
    async def cleaner_handler(request):
        '''
        Handle the request by applying the cleaner function to the raw function's response.

        Args:
            request: The incoming request object.

        Returns:
            aiohttp.web.json_response: A JSON response containing the cleaned data.
        '''
        # Call the raw function with the request and match_info as parameters
        response = cleaner_function(await raw_function(request, **request.match_info))
        
        # Determine the response type and return appropriately
        if isinstance(response, dict) or isinstance(response, list):
            return aiohttp.web.json_response(response) # Return JSON response for dict or list
        elif isinstance(response, str):
            return aiohttp.web.Response(text=response) # Return plain text response if it's a string
        else:
            raise AttributeError(f"Invalid response type: {type(response)}") # Handle unexpected response types
    if name is not None:
        setattr(cleaner_handler, "__qualname__", name + "_handler")

    return cleaner_handler

def make_cleaner_function(raw_function, cleaner_function, name=None):
    """
    Creates a cleaner function that processes the output of a raw function.

    This function wraps a raw function and a cleaner function, allowing the cleaner 
    to be applied to the response of the raw function.

    Args:
        raw_function (callable): The function that makes the raw API call.
        cleaner_function (callable): The function that cleans the response.
        name (str, optional): The name to assign to the created cleaner function.

    Returns:
        callable: An asynchronous cleaner function that calls the raw function 
                  and processes its output with the cleaner function.
    """
    async def cleaner_local(request, **kwargs):
        """
        Handles the request, calls the raw function, and applies the cleaner function.

        Args:
            request: The incoming request object.
            **kwargs: Additional keyword arguments for the raw function.

        Returns:
            The cleaned response from the cleaner function.
        """
        lms_response = await raw_function(request, **kwargs)
        clean = cleaner_function(lms_response)
        return clean
    
    if name is not None:
        setattr(cleaner_local, "__qualname__", name)
    return cleaner_local

async def raw_ajax(runtime, target_url, lms_name, base_url=None, **kwargs):
    """
    Make an authenticated AJAX call to a specified service (e.g., Google, Canvas), handling 
    authorization, caching, and retries.

    Parameters:
    - runtime: An instance of the Runtime class containing request information.
    - lms_name: A string indicating the name of the service ('google' or 'canvas').
    - target_url: The URL endpoint to be called, with optional formatting using kwargs.
    - base_url: An optional base URL for the service. If provided, it will be prefixed 
      to target_url.
    - kwargs: Additional keyword arguments to format the target_url or control behavior 
      (e.g., retry).

    Returns:
    - A JSON response from the requested service, with key translation if necessary.

    Raises:
    - aiohttp.web.HTTPUnauthorized: If the request lacks necessary authorization.
    - aiohttp.ClientResponseError: If the request fails, with special handling for 401 errors on Canvas.
    """
    # Retrieve the incoming request and active user
    request = runtime.get_request()
    user = await learning_observer.auth.get_active_user(request)
    
    # Extract 'retry' flag from kwargs (defaults to False)
    retry = kwargs.pop('retry', False)
    
    # mapping to determine the appropriate headers based on the service
    headers = {
        constants.GOOGLE: request.get(constants.AUTH_HEADERS),
        constants.CANVAS: request.get(constants.CANVAS_AUTH_HEADERS)
    }

    # Ensure Google requests are authenticated
    if lms_name == constants.GOOGLE and constants.AUTH_HEADERS not in request:
        raise aiohttp.web.HTTPUnauthorized(text="Please log in")
    
    # Construct the full URL using the base URL if provided, otherwise use the target URL directly
    if base_url:
        url = base_url + target_url.format(**kwargs)
    else:
        url = target_url.format(**kwargs)

    # Generate a unique cache key based on the service, user, and request URL
    cache_key = f"raw_{lms_name}/" + learning_observer.auth.encode_id('session', user[constants.USER_ID]) + '/' + learning_observer.util.url_pathname(url)
    
    cache_flag = f"use_{lms_name}_ajax"
    # Check cache and return cached response if available
    if settings.feature_flag(cache_flag) is not None:
        value = await cache[cache_key]
        if value is not None:
            # Translate keys if the service is Google, otherwise return raw JSON
            if lms_name == constants.GOOGLE:
                return learning_observer.util.translate_json_keys(
                    json.loads(value),
                    learning_observer.google.GOOGLE_TO_SNAKE
                )
            else: 
                return json.loads(value)

    # Make the actual AJAX call to the service
    async with aiohttp.ClientSession(loop=request.app.loop) as client:
        try:
            async with client.get(url, headers=headers[lms_name]) as resp:
                response = await resp.json()

                # Log the AJAX request and response
                learning_observer.log_event.log_ajax(target_url, response, request)
                # Cache the response if the feature flag is enabled
                if settings.feature_flag(cache_flag) is not None:
                    await cache.set(cache_key, json.dumps(response, indent=2))
                # Translate keys if the service is Google, otherwise return raw JSON
                if lms_name == constants.GOOGLE:
                    return learning_observer.util.translate_json_keys(
                        response,
                        learning_observer.google.GOOGLE_TO_SNAKE
                    )
                # Return response for other LMSes
                else:
                    # Raise an exception for non-successful HTTP responses
                    resp.raise_for_status()
                    return response
        # Handle 401 errors for Canvas with an optional retry
        except aiohttp.ClientResponseError as e:
            if lms_name == constants.CANVAS and e.status == 401 and retry:
                new_tokens = await learning_observer.auth.social_sso._handle_canvas_authorization(request)
                if 'access_token' in new_tokens:
                    return await raw_ajax(runtime, target_url, lms_name, base_url, **kwargs)
            raise

# Abstract raw_ajax for each LMS to specify their different arguments

async def raw_google_ajax(runtime, target_url, **kwargs):
    """Make an authenticated AJAX call to the Google API."""
    return await raw_ajax(runtime, target_url, constants.GOOGLE, **kwargs)

async def raw_canvas_ajax(runtime, target_url, **kwargs):
    """Make an authenticated AJAX call to the Canvas API."""
    base_url = settings.pmss_settings.lms_api(types=['lms', 'canvas_oauth'])
    # This is used to request the access token again in order to retry the ajax call one more time
    kwargs.setdefault('retry', True)
    return await raw_ajax(runtime, target_url, constants.CANVAS, base_url, **kwargs)


class LMS:
    """
    The LMS class represents a Learning Management System, encapsulating
    the necessary information and methods for API interactions.

    Attributes:
        lms_name (str): The name of the LMS (e.g., 'google', 'canvas').
        endpoints (list): A list of Endpoint objects that represent the API endpoints.
        raw_ajax_function (dict): A dictionary mapping LMS names to their respective AJAX functions.
    """
    def __init__(self, lms_name, endpoints):
        """
        Initializes the LMS instance with the specified name and endpoints.

        Args:
            lms_name (str): The name of the LMS.
            endpoints (list): A list of Endpoint objects.
        """
        self.lms_name = lms_name
        self.endpoints = endpoints
        self.raw_ajax_function = {
            constants.GOOGLE: raw_google_ajax,
            constants.CANVAS: raw_canvas_ajax
        }

    def initialize_routes(self, app):
        """
        Initializes the API routes for the specified LMS within the given web application.

        This method sets up the endpoint routes and associates them with their corresponding 
        handler functions.

        Args:
            app: An instance of the aiohttp web application to which routes will be added.
        """
        
        # Add the main API documentation route
        app.add_routes([
            aiohttp.web.get(f"/{self.lms_name}", lambda _: api_docs_handler(self.endpoints))
        ])

        # Iterate through the endpoints to set up routes for each one
        for e in self.endpoints:
            function_name = f"raw_{e.name}" # Construct the function name for the raw AJAX function
            raw_function = raw_access_partial(
                raw_ajax_function = self.raw_ajax_function[self.lms_name], # Get the appropriate raw AJAX function
                target_url = e.remote_url, # Use the endpoint's remote URL
                name = e.name # Set the name for the function
            )
            globals()[function_name] = raw_function # Register the raw function globally
            
            # Add routes for each cleaner associated with the endpoint
            cleaners = e._cleaners()
            for c in cleaners:
                app.add_routes([
                    aiohttp.web.get(
                        cleaners[c]['local_url'], # The local URL for the cleaner
                        make_cleaner_handler(raw_function, cleaners[c]['function'], name=cleaners[c]['name']) # Handler for the cleaner
                    )
                ])
                lms_module = getattr(learning_observer, self.lms_name) # Get the module for the LMS
                
                # Create the cleaner function and set it in the LMS module
                cleaner_function = make_cleaner_function(
                    raw_function,
                    cleaners[c]['function'],
                    name=cleaners[c]['name']
                )
                setattr(lms_module, cleaners[c]['name'], cleaner_function)
                
            # Add the main route for the endpoint
            app.add_routes([
                aiohttp.web.get(e._local_url(), make_ajax_raw_handler(
                    self.raw_ajax_function[self.lms_name], # The raw AJAX function for the LMS
                    e.remote_url # The endpoint's remote URL
                ))
            ])