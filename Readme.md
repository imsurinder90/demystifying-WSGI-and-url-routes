# Demystifying WSGI and URL map/routes - Shortner

It is a URL Shortner application which users Werkzeug as WSGI web server, Jinja for templates and Redis as database to store Short URL generated.

This project is aimed at creating a basic functionality to understand how:
- HTTP request is send to web server
- HTTP request from web server to python application
- A URL is mapped to function/methods
- To write Rules for binding an URI to endpoint(method)

Code is well documented and easy to understand the story of how HTTP request is handled by python code and how response is returned.


## Installation

Clone this project on your machine and then create a virtual environment and install all dependent packages by running requirements.txt

```bash
pip install -r requirements.txt
```

## How Rules are written

```bash
# Create Rule for mapping URL with endpoint(methods)
# For example: Map / to def on_new_url(self, request) method
# This endpoint is being called by dispatch_request method
self.url_map = Map([
    Rule('/', endpoint='new_url'),
    Rule('/<short_id>', endpoint='follow_short_link'),
    Rule('/<short_id>+', endpoint='short_link_details')
])
```

## Mapping URL to endpoint
```bash
def dispatch_request(self, request):
    """
    Binds request.environ(http request data) with url map
    to extract endpoint(method to call) and its arguments
    then it calls endpoint with its arguments
    """
    adapter = self.url_map.bind_to_environ(request.environ)
    try:
        endpoint, values = adapter.match()
        """
        endpoint = 'follow_short_link'
        values = {'short_id': u'foo'}
        """
        return getattr(self, 'on_' + endpoint)(request, **values)
    except HTTPException as e:
        return e
```

## Start WSGI Server

```bash
# To start WSGI Server
if __name__ == '__main__':
    """
    Create an app object of Shortner class and pass
    this app object to run_simple(...) method to let
    WSGI server know of app object and its __call__ method
    to route http request and its header to __call__ method
    """
    from werkzeug.serving import run_simple
    app = create_app()
    run_simple('127.0.0.1', 6543, app,
                use_debugger=True, use_reloader=True)
```
## Call to app method from WSGI
```bash
def __call__(self, environ, start_response):
    """
    WSGI from werkzeug makes call to this method
    and pass http request contained in environ and
    sends start_response callback.
    When run_simple(host, port, app) is called in
    if __name__ == '__main__', we pass on app object
    which our Shortner class and has __call__ method
    This way WSGI registers app object and when an
    http request is made by client, WSGI makes call
    to app.__call__(environ, start_response)
    """
    return self.wsgi_app(environ, start_response)
```

## TODO

Unit test cases are pending

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## References/Credits
https://werkzeug.palletsprojects.com/

## License
Free to use