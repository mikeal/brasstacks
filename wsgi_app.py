import os
os.environ['PYTHON_EGG_CACHE'] = os.path.expanduser('~/.eggs')

import webenv
from webenv.rest import RestApplication
import couchquery
couchquery.debugging = False

from brasstacks import sitecompare
from brasstacks import users
from brasstacks import fennec
from brasstacks import tcm
from brasstacks import buildcompare

class Stub(RestApplication):
    def GET(self, request):
        return webenv.HtmlResponse('<html><head><title>Nope.</title></head><body>Nope.</body></html>')

sitecompare_application = sitecompare.SiteCompareApplication(
    couchquery.CouchDatabase("http://localhost:5984/sitecompare")
    )
db = couchquery.CouchDatabase("http://localhost:5984/brasstacks")
users_application = users.UsersApplication(db)
fennec_application = fennec.FennecApplication(couchquery.Database("http://pythonesque.org:5984/fennec"))
tcm_application = tcm.TestCaseManagerApplication(couchquery.Database("http://localhost:5984/tcm"))
buildcompare_application = buildcompare.BuildCompareApplication(couchquery.Database("http://pythonesque.org:5984/fennec"))
application = Stub()
application.add_resource('sitecompare', sitecompare_application)
application.add_resource('users', users_application)
application.add_resource('fennec', fennec_application)
application.add_resource('buildcompare', buildcompare_application)
application.add_resource('tcm', tcm_application)




