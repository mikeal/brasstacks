import os, sys

from webenv.rest import RestApplication
from webenv.applications.file_server import FileServerApplication
import webenv
import couchquery

import cronjob

cron = cronjob.run

# from mako.lookup import TemplateLookup
# 
this_dir = os.path.abspath(os.path.dirname(__file__))
design_doc = os.path.join(this_dir, 'views')
static_dir = os.path.join(this_dir, 'static')
# 
# lookup = TemplateLookup(directories=[os.path.join(this_dir, 'templates')])
# 
# def setup():
#     from cherrypy import wsgiserver
#     import pouch
#     
#     from brasstacks.rest import BrassTacksApplication
#     pouch.set_globals('http://127.0.0.1:5984', 'brasstacks')
#     pouch.sync_design_doc(os.path.join(this_dir, 'designDocs', 'testRuns'), 'testRuns')
#     
#     views = pouch.GLOBAL_DB.views
#     
#     application = BrassTacksApplication(views=views, debug=True)
#     
#     httpd = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8888,), 
#                                           application, server_name='brasstacks-httpd',
#                                           numthreads=50)
#     return httpd
# 
# def cli():
#     httpd = setup()
#     
#     print 'Serving on http://localhost:8888/'
#     try:
#         httpd.start()
#     except KeyboardInterrupt:
#         httpd.stop()


def get_wsgi_server(db):
    from buildcompare import BuildCompareApplication
    from users import UsersApplication
    from sitecompare import SiteCompareApplication
    from tcm import TestCaseManagerApplication
    from fennec import FennecApplication
    from brasstacks.mozmill import MozmillApplication
    a = Stub()
    users_application = UsersApplication(db)
    fennec_application = FennecApplication(db)
    tcm_application = TestCaseManagerApplication(db)
    buildcompare_application = BuildCompareApplication(db)
    mozmill_application = MozmillApplication(db)
    a.add_resource('sitecompare', SiteCompareApplication(db))
    a.add_resource('users', users_application)
    a.add_resource('fennec', fennec_application)
    a.add_resource('tcm', tcm_application)
    a.add_resource('static', FileServerApplication(static_dir))
    a.add_resource('users', users_application)
    a.add_resource('buildcompare', buildcompare_application)
    a.add_resource('mozmill', mozmill_application)
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8888, a)
    return httpd    

def cli():
    db = [i for i in sys.argv if i.startswith('http')]
    if len(db) is 1:
        db = couchquery.CouchDatabase(db[0], cache=Cache())
    else:
        db = couchquery.CouchDatabase('http://localhost:5984/brasstacks')
    import sitecompare
    import fennec
    import tcm
    import brasstacks
    import buildcompare
    db.sync_design_doc("sitecompare", sitecompare.design_doc)
    db.sync_design_doc("brasstacks", brasstacks.design_doc)
    db.sync_design_doc("fennecResults", buildcompare.design_doc)
    db.sync_design_doc("tcm", tcm.design_doc)
    httpd = get_wsgi_server(db)
    print "Serving on http://localhost:8888/"
    httpd.serve_forever()

class Cache(dict):
    def __init__(self, *args, **kwargs):
        super(Cache, self).__init__(*args, **kwargs)
        setattr(self, 'del', lambda *args, **kwargs: dict.__delitem__(*args, **kwargs) )
    get = lambda *args, **kwargs: dict.__getitem__(*args, **kwargs)
    set = lambda *args, **kwargs: dict.__setitem__(*args, **kwargs)
    
class Stub(RestApplication):
    def GET(self, request):
        html = '<html><head><title>Current Applications on Brasstacks</title><head><body>'
        for application in self.rest_resources.keys():
            html += '<div><a href="/'+application+'">'+application+'</a></div>'
        html += '</body></html>'
        return webenv.HtmlResponse(html)

application = Stub()

def sync():
    import sys
    db = sys.argv[-1]
    import sitecompare
    import brasstacks
    import fennec
    import buildcompare
    import tcm
    db = couchquery.CouchDatabase(db)
    db.sync_design_doc("sitecompare", sitecompare.design_doc)
    db.sync_design_doc("brasstacks", brasstacks.design_doc)
    db.sync_design_doc("fennecResults", buildcompare.design_doc)
    db.sync_design_doc("tcm", tcm.design_doc)