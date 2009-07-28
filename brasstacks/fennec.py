import os
try:
    import json as simplejson
except ImportError:
    import simplejson
    
from markdown import markdown

from webenv import HtmlResponse
from mako.template import Template
from webenv.rest import RestApplication

template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fennec_templates')
design_doc = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fennec_views')

class MakoResponse(HtmlResponse):
    def __init__(self, name, **kwargs):
        self.body = Template(filename=os.path.join(template_dir, name+'.mko')).render(**kwargs)
        self.headers = []

class FennecApplication(RestApplication):
    def __init__(self, db):
        super(FennecApplication, self).__init__()
        self.db = db
    def GET(self, request, collection=None, resource=None):
        if collection is None:
            return MakoResponse("index")
        if collection == "builds":
            if resource is None:
                # List of last 100 builds by timestamp
                pass
            else:
                # Test info for specific build
                pass
        if collection == "products":
            if resource is None:
                products = set(self.db.views.metadata.products(reduce=False).rows.keys())
                return MakoResponse("products", products=products)
            else:
                tests = self.db.views.fennecBrasstacks.testsByProduct(key=resource).rows
                return MakoResponse("product", tests=tests)
        if collection == "testtypes":
            pass
        if collection == "tests":
            if resource is None:
                # List of last 100 tests by timestamp
                pass
            else:
                test = self.db.get(resource)
                # This is crap code, it's just there to show the whole object
                return MakoResponse("test", test=test)

