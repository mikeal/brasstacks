#!/usr/bin/env python
import couchdb_wsgi
import os
os.environ['PYTHON_EGG_CACHE'] = os.path.expanduser('~/.eggs')

import couchquery
couchquery.debugging = False
from couchquery import Database

import brasstacks
from brasstacks.sitecompare import SiteCompareApplication
from brasstacks.users import UsersApplication
from brasstacks.fennec import FennecApplication
from brasstacks.tcm import TestCaseManagerApplication
from brasstacks.logcompare import LogCompareApplication
from brasstacks.mozmill import MozmillApplication
from brasstacks.firefox import FirefoxApplication

db = Database("http://localhost:5984/brasstacks")
users_application = UsersApplication(db)
sitecompare_application = SiteCompareApplication(Database("http://localhost:5984/sitecompare"))
fennec_application = FennecApplication(Database("http://localhost:5984/fennec_results"))
tcm_application = TestCaseManagerApplication(Database("http://localhost:5984/tcm"))
logcompare_application = LogCompareApplication(Database("http://pythonesque.org:5984/logcompare"))
mozmill_application = MozmillApplication(Database("http://localhost:5984/mozmill"))
firefox_application = FirefoxApplication(Database("http://localhost:5984/firefox"))

application = brasstacks.Stub()
application.add_resource('sitecompare', sitecompare_application)
application.add_resource('users', users_application)
application.add_resource('fennec', fennec_application)
application.add_resource('logcompare', logcompare_application)
application.add_resource('tcm', tcm_application)
application.add_resource('mozmill', mozmill_application)
application.add_resource('firefox', firefox_application)

couchdb_wsgi.CouchDBWSGIHandler(application).run()
