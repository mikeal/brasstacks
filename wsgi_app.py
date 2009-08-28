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

db = Database("http://localhost:5984/brasstacks")
users_application = UsersApplication(db)
sitecompare_application = SiteCompareApplication(Database("http://localhost:5984/sitecompare"))
fennec_application = FennecApplication(Database("http://pythonesque.org:5984/fennec_test"))
tcm_application = TestCaseManagerApplication(Database("http://localhost:5984/tcm"))
logcompare_application = LogCompareApplication(Database("http://pythonesque.org:5984/logcompare"))
mozmill_application = MozmillApplication(Database("http://localhost:5984/mozmill"))

application = brasstacks.Stub()
application.add_resource('sitecompare', sitecompare_application)
application.add_resource('users', users_application)
application.add_resource('fennec', fennec_application)
application.add_resource('logcompare', logcompare_application)
application.add_resource('tcm', tcm_application)
application.add_resource('mozmill', mozmill_application)