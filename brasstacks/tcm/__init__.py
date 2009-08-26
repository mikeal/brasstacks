import os
from datetime import datetime

from webenv import HtmlResponse, Response303, Response
from webenv.rest import RestApplication
from mako.lookup import TemplateLookup
from markdown2 import markdown
from cgi import escape
try:
    import json
except:
    import simplejson as json

this_directory = os.path.abspath(os.path.dirname(__file__))
design_doc = os.path.join(this_directory, 'views')
tags_design_doc = os.path.join(this_directory, 'tagViews')

lookup = TemplateLookup(directories=[os.path.join(this_directory, 'templates')], encoding_errors='ignore', input_encoding='utf-8', output_encoding='utf-8')

products = ["Firefox", "Thunderbird", "Fennec", "Calendar", "AMO (addons.mozilla.org)", "Rock your Firefox (Facebook application)", "SeaMonkey", "SFx (spreadfirefox.com)", "SUMO (support.mozilla.com)", "Weave"]

def render_description(body):
    return markdown(body, safe_mode="escape")

def get_locale(request):
    if request.headers.has_key('accept-language'):
        locale = request.headers["accept-language"].split(',')[0].lower()
    else:
        locale = 'en-us'
    return locale

class MakoResponse(HtmlResponse):
    def __init__(self, name, **kwargs):
        template = lookup.get_template(name+'.mko')
        kwargs['json'] = json
        self.body = template.render_unicode(**kwargs).encode('utf-8', 'replace')
        self.headers = []
        
class JSONResponse(Response):
    content_type = 'application/json'
    def __init__(self, obj):
        self.body = json.dumps(obj)
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

class TestCaseManagerAPI(RestApplication):
    def __init__(self, db):
        super(TestCaseManagerAPI, self).__init__()
        self.db = db
    def PUT(self, request, collection=None, resource=None):
        if collection == 'editcase':
            if resource is not None:
                # Edit a document
                rev = request.query['rev']
                doc = self.db.get(resource)
                assert rev == doc._rev
                changes = json.loads(str(request.body))
                if changes.has_key('tags'):
                    changes['tags'] = [t.replace(' ', '') for t in changes['tags']]
                if changes.has_key('description_raw'):
                    for locale, desc in changes['description_raw'].items():
                        doc['description_raw'][locale] = desc
                        doc['description_rendered'][locale] = render_description(desc)
                        changes.pop('description_raw')
                if changes.has_key('title'):
                    for locale, desc in changes['title'].items():
                        doc['title'][locale] = desc
                        changes.pop('title')
                for k, v in changes.items():
                    doc[k] = v
                info = self.db.save(doc)
                return JSONResponse(self.db.get(info['id']))
    def POST(self, request, collection, resource=None):
        if collection == 'createcollection':
            collection = json.loads(str(request.body))
            collection['type'] = 'tcm-collection'
            # Validation
            # TODO: Make these return proper errors
            assert collection.get('name')
            assert collection.get('product')
            assert collection.get('tags')
            info = self.db.create(collection)
            return JSONResponse(self.db.get(info['id']))


class TestCaseManagerTags(RestApplication):
    def __init__(self, db):
        super(TestCaseManagerTags, self).__init__()
        self.db = db
    def GET(self, request, tag=None, collection=None):
        if tag is None:
            rows = self.db.views.tcmTags.tagCount(group=True)
            collections = self.db.views.tcm.byType(key="tcm-collection")
            return MakoResponse('tags', tags=rows.items(), collections=collections, 
                                products=products)
        elif tag == "collection":
            if collection is None:
                pass
                # collection index
            else:
                coll = self.db.get(collection)
                keys = [[t, coll.product] for t in coll.tags]
                rows = self.db.views.tcmTags.casesByTag(keys=keys)
                testcases = dict([(d._id, d,) for d in rows]).values()
                return MakoResponse('testcases', testcases=testcases, 
                                    page_header="Collection :: "+coll.name)
        else:
            rows = self.db.views.tcmTags.casesByTag(startkey=[tag, None], endkey=[tag, {}])
            return MakoResponse('testcases', testcases=rows, page_header="Tags :: "+tag)

class TestCaseManagerApplication(RestApplication):
    def __init__(self, db):
        super(TestCaseManagerApplication, self).__init__()
        self.db = db
        self.add_resource('products', TestCaseManagerProducts(self.db))
        self.add_resource('api', TestCaseManagerAPI(self.db))
        self.add_resource('tags', TestCaseManagerTags(self.db))
    def GET(self, request, collection=None, resource=None, force_locale=None):
        if force_locale is not None and force_locale != 'advanced':
            locale = force_locale
        else: 
            locale = get_locale(request)
        
        if force_locale == 'advanced':
            advanced = True
            force_locale = None
        else:
            advanced = False
        
        if collection is None:
            return MakoResponse('index', locale=locale, force_locale=force_locale)
        if collection == 'write_test':
            return MakoResponse('simple_editor', product=None, locale=locale, force_locale=force_locale, 
                                advanced=advanced)
        if collection == "testcase":
            if resource is None:
                kwargs = {"descending":True, "limit":20}
                latest = dict([
                    (product, self.db.views.tcm.casesByProductCreation(
                    startkey=[product,{}],endkey=[product,None],**kwargs),)
                    for product in products
                ])
                return MakoResponse("latestTestcases", latest=latest, products=products, locale=locale,
                                    force_locale=force_locale,)
            else:
                if resource in products:
                    page_header = "All "+resource+" Tests"
                    return MakoResponse("testcases",
                                        testcases=self.db.views.tcm.casesByProduct(key=resource),
                                        locale=locale, force_locale=force_locale, page_header=page_header)
                return MakoResponse("testcase", testcase=self.db.get(resource), locale=locale,
                                    force_locale=force_locale, advanced=advanced)
    def POST(self, request, collection=None, force_locale=None):
        if force_locale is not None:
            locale = force_locale
        else: 
            locale = get_locale(request)
        if collection == 'write_test':
            form = request.body.form
            doc = {"type":"tcm-testcase", "title":{locale:escape(form['title'])}, 
                   "product":form['product'],
                   "description_raw":{locale:escape(form['description'])},
                   "description_rendered":{locale:render_description(form['description'])},
                   "tags":form["tags"].replace(' ','').split(','),
                   "creation_dt":datetime.now().isoformat()}
            info = self.db.create(doc)
            return Response303('/tcm/testcase/'+info['id'])


            


