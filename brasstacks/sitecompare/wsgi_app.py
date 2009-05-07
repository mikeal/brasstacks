import os
import simplejson
from mako.template import Template
import webenv
from webenv.applications import FileServerApplication
from webenv.rest import RestApplication
import couchquery

template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates')
static_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')
index_template = os.path.join(template_dir, 'index.mko')
page_template = os.path.join(template_dir, 'page.mko')
pages_template = os.path.join(template_dir, 'pages.mko')

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
            return webenv.HtmlResponse(Template(filename=index_template).render())
        if collection == "pages":
            if resource is None:
                view_result = db.views.sitecompare.byType(startkey="page", endkey="page0")
                resp = Template(filename=pages_template).render(pages=view_result.rows)
                return webenv.HtmlResponse(resp)
            else:
                d = db.get(resource).dict
                d['query'] = dict(request.query)
            
                resp = Template(filename=page_template).render(**d)
                return webenv.HtmlResponse(resp)
            
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
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8888, application)
    print "Serving on http://localhost:8888/"
    httpd.serve_forever()
