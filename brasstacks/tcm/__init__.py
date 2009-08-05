import os

from webenv import HtmlResponse, Response303
from webenv.rest import RestApplication
from mako.lookup import TemplateLookup
from markdown import markdown
from cgi import escape

this_directory = os.path.abspath(os.path.dirname(__file__))
design_doc = os.path.join(this_directory, 'views')

lookup = TemplateLookup(directories=[os.path.join(this_directory, 'templates')])

def render_description(body):
    return markdown(escape(body))

class MakoResponse(HtmlResponse):
    def __init__(self, name, **kwargs):
        self.body = lookup.get_template(name+'.mko').render(**kwargs)
        self.headers = []

class TestCaseManagerProducts(RestApplication):
    def __init__(self, db):
        super(TestCaseManagerProducts, self).__init__()
        self.db = db
    def GET(self, request, product=None, collection=None):
        if product is None:
            return MakoResponse('products')
        if collection is None:
            return MakoResponse('product', product=product)
        if collection == 'write_test':
            return MakoResponse('simple_editor', product=product)

class TestCaseManagerApplication(RestApplication):
    def __init__(self, db):
        super(TestCaseManagerApplication, self).__init__()
        self.db = db
        self.add_resource('products', TestCaseManagerProducts(self.db))
    def GET(self, request, collection=None, resource=None):
        if collection is None:
            return MakoResponse('index')
        if collection == 'write_test':
            return MakoResponse('simple_editor', product=None)
        if collection == "testcase":
            if resource is None:
                return MakoResponse("testcases")
            else:
                return MakoResponse("testcase", testcase=self.db.get(resource))
    def POST(self, request, collection=None):
        if collection == 'write_test':
            form = request.body.form
            doc = {"type":"tcm-testcase", "title":escape(form['title']), "product":form['product'],
                   "raw_description":escape(form['description']),
                   "rendered_description":render_description(form['description']),
                   "tags":form["tags"].replace(' ','').split(',')}
            info = self.db.create(doc)
            return Response303('/tcm/testcase/'+info['id'])


            


