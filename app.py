"""
Shortly - URL Shortner app
References: https://werkzeug.palletsprojects.com/en/1.0.x/
"""
import os
import redis
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.utils import redirect
from jinja2 import Environment, FileSystemLoader
from utils import is_valid_url, base36_encode

class Shortly(object):
    """
    This is an app class which has wsgi_app and __call__ method
    which will be called by wsgi server when we pass app object
    to the run_simple() function. It also creates a redis database
    connection.
    """

    def __init__(self, config):
        self.redis = redis.Redis(config['redis_host'], config['redis_port'])
        template_path = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_path),
                                     autoescape=True)
        # Create Rule for mapping URL with endpoint(methods)
        # For example: Map / to def on_new_url(self, request) method
        # This endpoint is being called by dispatch_request method
        self.url_map = Map([
            Rule('/', endpoint='new_url'),
            Rule('/<short_id>', endpoint='follow_short_link'),
            Rule('/<short_id>+', endpoint='short_link_details')
        ])

    def render_template(self, template_name, **context):
        """ Loads html template and return as a response"""
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype='text/html')

    def on_follow_short_link(self, request, short_id):
        link_target = self.redis.get('url-target:' + short_id)
        if link_target is None:
            raise NotFound()
        self.redis.incr('click-count:' + short_id)
        return redirect(link_target)

    def on_short_link_details(self, request, short_id):
        link_target = self.redis.get('url-target:' + short_id)
        if link_target is None:
            raise NotFound()
        click_count = int(self.redis.get('click-count:' + short_id) or 0)
        return self.render_template('short_link_details.html',
            link_target=link_target,
            short_id=short_id,
            click_count=click_count
        )

    def on_new_url(self, request):
        error = None
        url = ''
        if request.method == 'POST':
            url = request.form['url']
            if not is_valid_url(url):
                error = 'Please enter a valid URL'
            else:
                short_id = self.insert_url(url)
                if type(short_id) is bytes:
                    short_id = short_id.decode('utf-8')
                return redirect('/%s+' % short_id)
        return self.render_template('new_url.html', error=error, url=url)

    def insert_url(self, url):
        short_id = self.redis.get('reverse-url:' + url)
        if short_id is not None:
            return short_id
        url_num = self.redis.incr('last-url-id')
        short_id = base36_encode(url_num)
        print(url_num, short_id)
        self.redis.set('url-target:' + short_id, url)
        self.redis.set('reverse-url:' + url, short_id)
        return short_id

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

    def wsgi_app(self, environ, start_response):
        """
        Transform environ to Request object and then
        pass this request object to dispatch_request
        which maps this call to endpoint function, then
        response is requrned with environ(http request data)
        and callback function start_response
        start_response call like start_response("200 OK", headers)
        headers contains information like Content-length, message
        body(Hello World) and request type like below:
        HTTP / 1.1 200 OK
        Content length: 11
        Hello World
        """
        request = Request(environ)
        response = self.dispatch_request(request)
        print("request %s" % request)
        return response(environ, start_response)

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


def create_app(redis_host='localhost', redis_port=6379, with_static=True):
    app = Shortly({
        'redis_host': redis_host,
        'redis_port': redis_port
    })
    if with_static:
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/static':  os.path.join(os.path.dirname(__file__), 'static')
        })
    return app


# To start a WSGI Server
if __name__ == '__main__':
    """
    Create an app object of Shortner class and pass
    this app object to run_simple(...) method to let
    WSGI server know of app object and its __call__ method
    to route http request and its header to __call__ method
    """
    from werkzeug.serving import run_simple
    app = create_app()
    run_simple('127.0.0.1', 6543, app, use_debugger=True, use_reloader=True)
