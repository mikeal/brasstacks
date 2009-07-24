import os

from webenv import HtmlResponse
from mako.template import Template
from webenv.rest import RestApplication

template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fennec_templates')

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
        
        if collection == "build":
            if resource is None:
                pass
        if collection == "product":
            pass
        if collection == "testtype":
            pass
        if collection == "test":
            pass

