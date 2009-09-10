import os
os.environ['PYTHON_EGG_CACHE'] = os.path.expanduser('~/.eggs')

import couchquery
couchquery.debugging = False
from couchquery import Database

import brasstacks
from brasstacks import crashtest
from brasstacks import fennec
crashdb = Database('http://localhost:5984/crashtest')
resultdb = Database('http://localhost:5984/crashtest_results')
application = brasstacks.Stub()
application.add_resource('crashtest', crashtest.CrashTestApplication(crashdb, resultdb))

