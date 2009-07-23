import os, sys
from webenv.rest import RestApplication

import cronjob

cron = cronjob.run

# from mako.lookup import TemplateLookup
# 
# this_dir = os.path.abspath(os.path.dirname(__file__))
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

class Stub(RestApplication):
    def GET(self, request, *args):
        return webenv.HtmlResponse('<html><head><title>Nope.</title></head><body>Nope.</body></html>')

application = Stub()


