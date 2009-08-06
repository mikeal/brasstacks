import os, sys

from webenv.rest import RestApplication
import webenv
import couchquery

import cronjob

cron = cronjob.run

# from mako.lookup import TemplateLookup
# 
this_dir = os.path.abspath(os.path.dirname(__file__))
design_doc = os.path.join(this_dir, 'views')
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
    from fennec import FennecApplication
    from users import UsersApplication
    from sitecompare import SiteCompareApplication
    a = Stub()
    a.add_resource('sitecompare', SiteCompareApplication(db))
    users_application = UsersApplication(db)
    fennec_application = FennecApplication(db)
    a.add_resource('users', users_application)
    a.add_resource('fennec', fennec_application)
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8888, a)
    return httpd    

def cli():
    import sys
    db = [i for i in sys.argv if i.startswith('http')]
    if len(db) is 1:
        db = couchquery.CouchDatabase(db[0], cache=Cache())
    else:
        db = couchquery.CouchDatabase('http://localhost:5984/brasstacks', cache=Cache())
    import brasstacks
    import fennec
    db.sync_design_doc("sitecompare", design_doc)
    db.sync_design_doc("brasstacks", brasstacks.design_doc)
    db.sync_design_doc("fennecBrasstacks", fennec.design_doc)
    httpd = get_wsgi_server(db)
    print "Serving on http://localhost:8888/"
    httpd.serve_forever()

class Cache(dict):
    lambda *args, **kwargs: dict.__getitem__(*args, **kwargs)
    lambda *args, **kwargs: dict.__setitem__(*args, **kwargs)
    lambda *args, **kwargs: dict.__delitem__(*args, **kwargs)
    # lambda get(self, *args, **kwargs): dict.__getitem__(*args, **kwargs)
    # lambda set(self, *args, **kwargs): dict.__setitem__(*args, **kwargs)
    # lambda del(self, *args, **kwargs): dict.__delitem__(*args, **kwargs)
    
class Stub(RestApplication):
    def GET(self, request, *args):
        return webenv.HtmlResponse('<html><head><title>Nope.</title></head><body>Nope.</body></html>')

application = Stub()


