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
    def arguments(self):
        return extract_parameters_from_format_string(self.remote_url)

    def _local_url(self):
        parameters = "}/{".join(self.arguments())
        base_url = f"/{self.lms}/{self.name}"
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

def extract_parameters_from_format_string(format_string):
    '''
    Extracts parameters from a format string. E.g.
    >>> ("hello {hi} my {bye}")]
    ['hi', 'bye']
    '''
    return [f[1] for f in string.Formatter().parse(format_string) if f[1] is not None]

def raw_access_partial(raw_ajax_function, target_url, name=None):
    '''
    This is a helper which allows us to create a function which calls specific
    Google APIs.

    To test this, try:

        print(await raw_document(request, documentId="some_google_doc_id"))
    '''
    async def caller(request, **kwargs):
        '''
        Make an AJAX request to LMS
        '''
        return await raw_ajax_function(request, target_url, **kwargs)
    setattr(caller, "__qualname__", name)

    return caller

def api_docs_handler(endpoints):
    '''
    Return a list of available endpoints.

    Eventually, we should also document available function calls
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
    This will register a cleaner function, for export both as a web service
    and as a local function call.
    '''
    def decorator(f):
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

    return decorator

def make_ajax_raw_handler(raw_ajax_function, remote_url):
    async def ajax_passthrough(request):
        runtime = learning_observer.runtime.Runtime(request)
        response = await raw_ajax_function(runtime, remote_url, retry=True, **request.match_info)
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
                new_tokens = await learning_observer.auth.social_sso._canvas(request)
                if 'access_token' in new_tokens:
                    return await raw_ajax(runtime, target_url, lms_name, base_url, **kwargs)
            raise

async def raw_google_ajax(runtime, target_url, **kwargs):
    return await raw_ajax(runtime, target_url, constants.GOOGLE, **kwargs)

async def raw_canvas_ajax(runtime, target_url, **kwargs):
    base_url = settings.pmss_settings.lms_api(types=['lms', 'canvas_oauth'])
    kwargs.setdefault('retry', True)
    return await raw_ajax(runtime, target_url, constants.CANVAS, base_url, **kwargs)


class LMS:
    def __init__(self, lms_name, endpoints):
        self.lms_name = lms_name
        self.endpoints = endpoints
        self.raw_ajax_function = {
            constants.GOOGLE: raw_google_ajax,
            constants.CANVAS: raw_canvas_ajax
        }

    def initialize_routes(self, app):
        app.add_routes([
            aiohttp.web.get(f"/{self.lms_name}", lambda _: api_docs_handler(self.endpoints))
        ])

        for e in self.endpoints:
            function_name = f"raw_{e.name}"
            raw_function = raw_access_partial(
                raw_ajax_function = self.raw_ajax_function[self.lms_name], 
                target_url = e.remote_url, 
                name = e.name
            )
            globals()[function_name] = raw_function
            cleaners = e._cleaners()
            for c in cleaners:
                app.add_routes([
                    aiohttp.web.get(
                        cleaners[c]['local_url'],
                        make_cleaner_handler(raw_function, cleaners[c]['function'], name=cleaners[c]['name'])
                    )
                ])
                lms_module = getattr(learning_observer, self.lms_name)
                
                cleaner_function = make_cleaner_function(
                    raw_function,
                    cleaners[c]['function'],
                    name=cleaners[c]['name']
                )
                setattr(lms_module, cleaners[c]['name'], cleaner_function)
            app.add_routes([
                aiohttp.web.get(e._local_url(), make_ajax_raw_handler(
                    self.raw_ajax_function[self.lms_name], 
                    e.remote_url
                ))
            ])