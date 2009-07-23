import os
try:
    import json as simplejson
except ImportError:
    import simplejson
from mako.template import Template
import webenv
from webenv.applications import FileServerApplication
from webenv.rest import RestApplication
import couchquery

template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates')
static_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')

class MakoResponse(webenv.HtmlResponse):
    def __init__(self, name, **kwargs):
        self.body = Template(filename=os.path.join(template_dir, name+'.mko')).render(**kwargs)
        self.headers = []

design_doc = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'views')

class ResourceCollection(object):
    def __init__(self, db):
        self.db = db

class PagesCollection(ResourceCollection):
    def add_resource(self, obj):
        obj['type'] = "page"
        return self.db.create(obj)
    def update_resource(self, obj):
        return self.db.update(obj)
    
class SiteCompareApplication(RestApplication):
    def __init__(self, db):
        super(SiteCompareApplication, self).__init__()
        self.db = db
        self.pages_collection = PagesCollection(db)
        self.add_resource('static', FileServerApplication(static_dir))
    
    def GET(self, request, collection=None, resource=None):
        if collection is None:
            latest = self.db.views.sitecompare.runByTime(descending=True, limit=1).rows[0]
            latest.tests = self.db.views.sitecompare.testByRun(key=latest._id).rows
            
            return MakoResponse('index', latest=latest)
        if collection == "pages":
            if resource is None:
                view_result = self.db.views.sitecompare.byType(key="page")
                return MakoResponse('pages', pages=view_result.rows)
            else:
                d = self.db.get(resource)
                d.query = dict(request.query)
                tests = self.db.views.sitecompare.testByPage(startkey=[d._id,0], endkey=[d._id,{}]).rows
                return MakoResponse('page', tests=tests, **dict(d))
        if collection == 'runs':
            if resource is None:
                runs = self.db.views.sitecompare.runByTime(descending=True).rows
                return MakoResponse('runs', runs=runs)
            else:
                run = self.db.get(resource)
                run.tests = self.db.views.sitecompare.testByRun(key=run._id).rows
                return MakoResponse('run', run=run)
        if collection == 'tests':
            if resource is None:
                pass
            else:
                test = self.db.get(resource)
                run = self.db.get(test['run-id'])
                return MakoResponse('test', test=test, run=run)
        if collection == 'builds':
            if resource is None:
                pass
            else:
                build = self.db.get(resource)
                runs = self.db.views.sitecompare.runByBuild(startkey=build._id, endkey=build._id+'0').rows
                return MakoResponse('build', build=build, runs=runs)
            
    def POST(self, request, collection=None, resource=None):
        if collection == "pages":
            if resource is None:
                if request['CONTENT_TYPE'] == "application/json":
                    resp = self.pages_collection.add_resource(
                                simplejson.loads(str(request.body)))
                elif request['CONTENT_TYPE'] == "application/x-www-form-urlencoded":
                    # Check if this already exists:
                    k = request.body['uri']
                    r = self.db.views.sitecompare.pageByURI(key=k)
                    if len(r) is not 0:
                        return webenv.Response303("/sitecompare/pages/"+str(r.rows[0]['_id'])+'?m=already')
                    resp = self.pages_collection.add_resource(dict(request.body))
                    return webenv.Response303("/sitecompare/pages/"+str(resp['id']))
            else:
                if request['CONTENT_TYPE'] == "application/json":
                    resp = self.pages_collection.update_resource(
                                simplejson.loads(str(request.body)))
                elif request['CONTENT_TYPE'] == "application/x-www-form-urlencoded":
                    resp = self.pages_collection.update_resource(dict(request.body))

def get_wsgi_server(db):
    class Stub(RestApplication):
        def GET(self, request, *args):
            return webenv.HtmlResponse('<html><head><title>Nope.</title></head><body>Nope.</body></html>')
    a = Stub()
    a.add_resource('sitecompare', SiteCompareApplication(db))
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8888, a)
    return httpd

def cli():
    import sys
    db = [i for i in sys.argv if i.startswith('http')]
    if len(db) is 1:
        db = couchquery.CouchDatabase(db[0])
    else:
        db = couchquery.CouchDatabase('http://localhost:5984/sitecompare')
    db.sync_design_doc("sitecompare", design_doc)
    httpd = get_wsgi_server(db)
    print "Serving on http://localhost:8888/sitecompare"
    httpd.serve_forever()
    