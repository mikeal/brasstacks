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

db = couchquery.CouchDatabase("http://127.0.0.1:5984/brasstacks")
db.sync_design_doc("sitecompare", os.path.join(os.path.abspath(os.path.dirname(__file__)), 'views'))

class ResourceCollection(object):
    pass

class PagesCollection(ResourceCollection):
    def add_resource(self, obj):
        obj['type'] = "page"
        return db.create(obj)
    def update_resource(self, obj):
        return db.update(obj)
    
class SiteCompareApplication(RestApplication):
    def __init__(self, *args, **kwargs):
        self.pages_collection = PagesCollection()
        super(SiteCompareApplication, self).__init__(*args, **kwargs)
    
    def GET(self, request, collection=None, resource=None):
        if collection is None:
            latest = db.views.sitecompare.runByTime(descending=True, limit=1).rows[0]
            latest.tests = db.views.sitecompare.testByRun(
                startkey=latest._id, endkey=latest._id+'0').rows
            
            return MakoResponse('index', latest=latest)
        if collection == "pages":
            if resource is None:
                view_result = db.views.sitecompare.byType(startkey="page", endkey="page0")
                return MakoResponse('pages', pages=view_result.rows)
            else:
                d = db.get(resource)
                d.query = dict(request.query)
                tests = db.views.sitecompare.testByPage(d._id).rows
                return MakoResponse('page', tests=tests, **dict(d))
        if collection == 'runs':
            if resource is None:
                runs = db.views.sitecompare.runByTime(descending=True).rows
                return MakoResponse('runs', runs=runs)
            else:
                run = db.get(resource)
                run.tests = db.views.sitecompare.testByRun(startkey=run._id, endkey=run._id+'0').rows
                return MakoResponse('run', run=run)
        if collection == 'tests':
            if resource is None:
                pass
            else:
                test = db.get(resource)
                run = db.get(test['run-id'])
                return MakoResponse('test', test=test, run=run)
        if collection == 'builds':
            if resource is None:
                pass
            else:
                build = db.get(resource)
                runs = db.views.sitecompare.runByBuild(startkey=build._id, endkey=build._id+'0').rows
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
                    r = db.views.sitecompare.pageByURI(startkey=k, endkey=k+'0')
                    if len(r) is not 0:
                        return webenv.Response303("/pages/"+str(r.rows[0]['_id'])+'?m=already')
                    resp = self.pages_collection.add_resource(dict(request.body))
                    return webenv.Response303("/pages/"+str(resp['id']))
            else:
                if request['CONTENT_TYPE'] == "application/json":
                    resp = self.pages_collection.update_resource(
                                simplejson.loads(str(request.body)))
                elif request['CONTENT_TYPE'] == "application/x-www-form-urlencoded":
                    resp = self.pages_collection.update_resource(dict(request.body))


application = SiteCompareApplication()
application.add_resource('static', FileServerApplication(static_dir))

if __name__ == "__main__":
    class Stub(RestApplication):
        def GET(self, request, *args):
            return webenv.HtmlResponse('<html><head><title>Nope.</title></head><body>Nope.</body></html>')
    a = Stub()
    a.add_resource('sitecompare', application)
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8888, a)
    print "Serving on http://localhost:8888/sitecompare"
    httpd.serve_forever()
