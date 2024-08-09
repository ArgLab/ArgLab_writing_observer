import recordclass
import string
import aiohttp
import aiohttp.web
import learning_observer.runtime


# These took a while to find, but many are documented here:
# https://developers.google.com/drive/api/v3/reference/
# This list might change. Many of these contain additional (optional) parameters
# which we might add later. This is here for debugging, mostly. We'll stabilize
# APIs later.
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

def raw_access_partial(raw_ajax, remote_url, name=None):
    '''
    This is a helper which allows us to create a function which calls specific
    Google APIs.

    To test this, try:

        print(await raw_document(request, documentId="some_google_doc_id"))
    '''
    async def caller(request, **kwargs):
        '''
        Make an AJAX request to Google
        '''
        return await raw_ajax(request, remote_url, **kwargs)
    setattr(caller, "__qualname__", name)

    return caller

def api_docs_handler(request, ENDPOINTS):
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

def register_cleaner(data_source, cleaner_name, ENDPOINTS):
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

def make_ajax_raw_handler(raw_canvas_ajax, remote_url):
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

class BaseLMS:
    def __init__(self, lms_name, endpoints, raw_ajax_function):
        self.lms_name = lms_name
        self.endpoints = endpoints
        self.raw_ajax_function = raw_ajax_function

    def initialize_routes(self, app):
        app.add_routes([
            aiohttp.web.get(f"/{self.lms_name}", lambda request: api_docs_handler(request, self.endpoints))
        ])

        for e in self.endpoints:
            function_name = f"raw_{e.name}"
            raw_function = raw_access_partial(self.raw_ajax_function, remote_url=e.remote_url, name=e.name)
            globals()[function_name] = raw_function
            cleaners = e._cleaners()
            for c in cleaners:
                app.add_routes([
                    aiohttp.web.get(
                        cleaners[c]['local_url'],
                        make_cleaner_handler(raw_function, cleaners[c]['function'], name=cleaners[c]['name'])
                    )
                ])
                globals()[cleaners[c]['name']] = make_cleaner_function(
                    raw_function,
                    cleaners[c]['function'],
                    name=cleaners[c]['name']
                )
            app.add_routes([
                aiohttp.web.get(e._local_url(), make_ajax_raw_handler(self.raw_ajax_function, e.remote_url))
            ])