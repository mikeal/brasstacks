import os
from datetime import datetime

from webenv import HtmlResponse, Response303
from webenv.rest import RestApplication
from mako.lookup import TemplateLookup
from markdown import markdown
from cgi import escape

this_directory = os.path.abspath(os.path.dirname(__file__))
design_doc = os.path.join(this_directory, 'views')

lookup = TemplateLookup(directories=[os.path.join(this_directory, 'templates')])

products = ["Firefox", "Thunderbird", "Fennec", "Sunbird"]

def render_description(body):
    return markdown(escape(body))

def get_locale(request):
    if request.headers.has_key('accept-language'):
        locale = request.headers["accept-language"].split(',')[0].lower()
    else:
        locale = 'en-us'
    return locale

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
        locale = get_locale(request)
        if collection is None:
            return MakoResponse('index', locale=locale)
        if collection == 'write_test':
            return MakoResponse('simple_editor', product=None, locale=locale)
        if collection == "testcase":
            if resource is None:
                kwargs = {"descending":True, "limit":20}
                latest = dict([
                    (product, self.db.views.tcm.casesByProductCreation(
                    startkey=[product,{}],endkey=[product,None],**kwargs),)
                    for product in products
                ])
                return MakoResponse("testcases", latest=latest, products=products, locale=locale)
            else:
                return MakoResponse("testcase", testcase=self.db.get(resource), locale=locale)
    def POST(self, request, collection=None):
        locale = get_locale(request)
        if collection == 'write_test':
            form = request.body.form
            doc = {"type":"tcm-testcase", "title":{locale:escape(form['title'])}, 
                   "product":form['product'],
                   "raw_description":{locale:escape(form['description'])},
                   "rendered_description":{locale:render_description(form['description'])},
                   "tags":form["tags"].replace(' ','').split(','),
                   "creation_dt":datetime.now().isoformat()}
            info = self.db.create(doc)
            return Response303('/tcm/testcase/'+info['id'])


            


