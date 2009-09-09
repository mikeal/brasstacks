import os
from datetime import datetime

from webenv import HtmlResponse, Response303, Response
from webenv.rest import RestApplication
from mako.lookup import TemplateLookup
try:
    import json
except:
    import simplejson as json

this_directory = os.path.abspath(os.path.dirname(__file__))
design_doc = os.path.join(this_directory, 'views')
failures_design_doc = os.path.join(this_directory, 'failureViews')

lookup = TemplateLookup(directories=[os.path.join(this_directory, 'templates')], encoding_errors='ignore', input_encoding='utf-8', output_encoding='utf-8')

class MakoResponse(HtmlResponse):
    def __init__(self, name, **kwargs):
        template = lookup.get_template(name+'.mko')
        kwargs['json'] = json
        self.body = template.render_unicode(**kwargs).encode('utf-8', 'replace')
        self.headers = []
        
class JSONResponse(Response):
    content_type = 'application/json'
    def __init__(self, obj):
        self.body = json.dumps(obj)
        self.headers = []

class FennecApplication(RestApplication):
    def __init__(self, db):
        super(FennecApplication, self).__init__()
        self.db = db
        self.add_resource('api', FennecAPIApplication(db))
    
    def get_failure_info(self, test, testtype, os, stale=False):
        k = [test, testtype, os]
        kwargs = {'descending':True, 'limit':1, 'startkey':k+[True], 'endkey':k+[{}]}
        if stale:
            kwargs['stale'] = 'ok'
        lastsuccess = self.db.views.fennec.testByTimestampResult(**kwargs)
            
        if len(lastsuccess) is not 0:
            lastsuccess = lastsuccess[0]
        else:
            lastsuccess = None
        
        if lastsuccess:
            startkey = k + [False, lastsuccess['timestamp']]
        else:
            startkey = k + [False]
        
        kwargs = {'limit':1, 'startkey':startkey, 'endkey':k+[False, {}]}
        if stale:
            kwargs['stale'] = 'ok'
        
        firstfailed = self.db.views.fennec.testByTimestampResult(**kwargs)[0]
                
        return {"lastsuccess":lastsuccess, "firstfailed":firstfailed}
    
    def create_failure_document(self, doc, stale=False):
        """Create failure_info Document for testrun document"""
        # tests = [k for k,v in doc.tests.items() if v.get('fail',0) is not 0]
        tests = doc.failed_test_names
        fails = dict([(test, self.get_failure_info(test, doc.testtype, doc.os, stale=stale),) 
                    for test in tests
                    ])
        doc.pop('tests')
        doc.pop('passed_test_names')
        doc.pop('failed_test_names')
        # new_failures = []
        # for name, test in fails:
        #     if test['firstfailed']['_id'] == doc._id:
        #         new_failures
        
        failure_info = {'run':doc, 'fails':fails, 'type':'fennec-failure-info',}
        
        if len(self.db.views.fennecFailures.failureInfoByID(key=doc._id)) is 0:
            return self.db.create(failure_info)
    
    def update_failure_documents(self):
        latest = self.db.views.fennecFailures.failureInfoByTimestamp(descending=True, limit=1)
        if len(latest) is 0:
            endkey = None
        else:
            endkey = latest[0].run["timestamp"][:-1]
        rows = self.db.views.fennec.runByTimestamp(descending=True, startkey={}, endkey=endkey)

        for doc in rows:
            self.create_failure_document(doc, stale=True)
        
    def GET(self, request, collection=None, resource=None):
        if collection is None:
            limit = int(request.query.get('count', 20))
            runs = self.db.views.fennec.runByTimestamp(descending=True, limit=limit)
            return MakoResponse('runs', runs=runs, page_header="Latest "+str(limit)+" Runs")
        if collection == "detail":
            self.update_failure_documents()
            
            if resource is None:
                limit = int(request.query.get('count', 5))
                runs = self.db.views.fennec.runByTimestamp(descending=True, limit=limit)
                fail_info = self.db.views.fennecFailures.failureInfoByID(keys=runs.ids())
                for run in runs:
                    run.failure_info = fail_info[run._id][0]
                page_header = "Details for latest "+str(limit)+" Runs"
            else:
                runs = [self.db.get(resource)]
                runs[0].failure_info = self.db.views.fennecFailures.failureInfoByID(key=resource)[0]
                page_header = "Details for Run "+resource
                
            return MakoResponse('runsdetail', runs=runs, page_header=page_header)
        if collection == "newfailures":
            self.update_failure_documents()
            limit = int(request.query.get('count', 50))
            rows = self.db.views.fennecFailures.newFailures(descending=True, limit=limit)
            failures = {}
            for test in rows:
                day, time = test['run']['timestamp'].split(' ')
                test['time'] = time
                failures.setdefault(day, []).append(test)
            return MakoResponse('newfailures', failures=failures)

class FennecAPIApplication(FennecApplication):
    def __init__(self, db):
        RestApplication.__init__(self)
        self.db = db
    def POST(self, request, collection):
        if collection == 'testrun':
            obj = json.loads(str(request.body))
            obj['failed_test_names'] = [k for k, t in obj['tests'].items() if t.get('fail') is not 0]
            obj['passed_test_names'] = [k for k, t in obj['tests'].items() if t.get('fail') is 0]
            obj['pass_count'] = sum([t.get('pass', 0) for t in obj['tests'].values()], 0)
            obj['fail_count'] = sum([t.get('fail', 0) for t in obj['tests'].values()], 0)
            obj['type'] = 'fennec-test-run'
            info = self.db.create(obj)
            
            f_info = self.create_failure_document(self.db.get(info['id']), stale=False)
            return JSONResponse({'testrun':info,'failure_info':f_info})

