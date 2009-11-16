import os, sys

from webenv.rest import RestApplication
from webenv.applications.file_server import FileServerApplication
from webenv import Response404
import webenv
import couchquery
from wsgiref.simple_server import make_server

import cronjob

cron = cronjob.run

class Stub(RestApplication):
    def GET(self, request, favicon=None):
        if favicon:
            return Response404('not found')
        html = '<html><head><title>Current Applications on Brasstacks</title><head><body>'
        for application in self.rest_resources.keys():
            html += '<div><a href="/'+application+'">'+application+'</a></div>'
        html += '</body></html>'
        return webenv.HtmlResponse(html)

this_dir = os.path.abspath(os.path.dirname(__file__))
design_doc = os.path.join(this_dir, 'views')
static_dir = os.path.join(this_dir, 'static')

def sync(db, names):
    if 'sitecompare' in names:
        from brasstacks import sitecompare
        db.sync_design_doc("sitecompare", sitecompare.design_doc)
    if 'logcompare' in names:
        from brasstacks import logcompare
        db.sync_design_doc("logcompare", logcompare.design_doc)
    if 'fennec' in names:
        from brasstacks import fennec
        db.sync_design_doc("fennec", fennec.design_doc)
        db.sync_design_doc("fennecFailures", fennec.failures_design_doc)
    if 'firefox' in names:
        from brasstacks import firefox
        db.sync_design_doc("results", firefox.results_design_doc, "python")
        db.sync_design_doc("failures", firefox.failures_design_doc, "python") 
    if 'users' in names or 'brasstacks' in names:
        import brasstacks
        db.sync_design_doc("brasstacks", brasstacks.design_doc)
    if 'tcm' in names:
        from brasstacks import tcm
        db.sync_design_doc("tcm", tcm.design_doc)
        db.sync_design_doc("tcmTags", tcm.tags_design_doc)
    if 'crashtest' in names:
        from brasstacks import crashtest
        if 'crashes' in names:
            db.sync_design_doc("crashes", crashtest.crashes_design_doc)
        if 'crash_results' in names:
            db.sync_design_doc("jobs", crashtest.jobs_design_doc)
            db.sync_design_doc("results", crashtest.results_design_doc)
    
def get_application(db, names):
    a = Stub()
    a.add_resource('static', FileServerApplication(static_dir))
    if 'sitecompare' in names:
        from brasstacks.sitecompare import SiteCompareApplication
        a.add_resource('sitecompare', SiteCompareApplication(db))
    if 'logcompare' in names:
        from brasstacks.logcompare import LogCompareApplication
        logcompare_application = LogCompareApplication(db)
        a.add_resource('logcompare', logcompare_application)
    if 'users' in names or 'brasstacks' in names:
        from brasstacks.users import UsersApplication
        users_application = UsersApplication(db)
        a.add_resource('users', users_application)
    if 'tcm' in names:
        from brasstacks.tcm import TestCaseManagerApplication
        tcm_application = TestCaseManagerApplication(db)
        a.add_resource('tcm', tcm_application)
    if 'fennec' in names:
        from brasstacks.fennec import FennecApplication
        fennec_application = FennecApplication(db)
        a.add_resource('fennec', fennec_application)
    if 'mozmill' in names:
        from brasstacks.mozmill import MozmillApplication
        mozmill_application = MozmillApplication(db)
        a.add_resource('mozmill', mozmill_application)
    if 'crashtest' in names:
        resultdb = couchquery.Database(db.uri[:-1]+'_results')
        a.add_resource('crashtest', crashtest.CrashTestApplication(db, resultdb))
    if 'firefox' in names:
        from brasstacks.firefox import FirefoxApplication
        firefox_application = FirefoxApplication(db)
        a.add_resource('firefox', firefox_application)
    
    return a

def cli():
    db = [i for i in sys.argv if i.startswith('http')]
    assert len(db) is 1
    dbname = db[0]
    db = couchquery.Database(dbname, cache=Cache())
    sys.argv.remove(dbname)
    
    sync(db, sys.argv)
    a = get_application(db, sys.argv)
    httpd = make_server('', 8888, a)
    print "Serving on http://localhost:8888/"
    httpd.serve_forever()

def sync_cli(db=None):
    db = [i for i in sys.argv if i.startswith('http')]
    assert len(db) is 1
    dbname = db[0]
    db = couchquery.Database(dbname, cache=Cache())
    sys.argv.remove(dbname)
    
    sync(db, sys.argv)

class Cache(dict):
    def __init__(self, *args, **kwargs):
        super(Cache, self).__init__(*args, **kwargs)
        setattr(self, 'del', lambda *args, **kwargs: dict.__delitem__(*args, **kwargs) )
    get = lambda *args, **kwargs: dict.__getitem__(*args, **kwargs)
    set = lambda *args, **kwargs: dict.__setitem__(*args, **kwargs)

    