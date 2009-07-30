import os

from webenv import HtmlResponse
from webenv.rest import RestApplication
from mako.lookup import TemplateLookup

this_directory = os.path.abspath(os.path.dirname(__file__))
design_doc = os.path.join(this_directory, 'views')

lookup = TemplateLookup(directories=[os.path.join(this_directory, 'templates')])


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
    def GET(self, request, collection=None):
        if collection is None:
            return MakoResponse('index')
        if collection == 'write_test':
            return MakoResponse('simple_editor', product=None)


            


