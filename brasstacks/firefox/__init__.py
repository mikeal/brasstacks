import os
from datetime import datetime

from webenv import HtmlResponse, Response303, Response
from webenv.rest import RestApplication
try:
    import json
except:
    import simplejson as json

this_directory = os.path.abspath(os.path.dirname(__file__))
results_design_doc = os.path.join(this_directory, 'resultsDesign')
failures_design_doc = os.path.join(this_directory, 'failureDesign')
        
class JSONResponse(Response):
    content_type = 'application/json'
    def __init__(self, obj):
        self.body = json.dumps(obj)
        self.headers = []

class FirefoxApplication(RestApplication):
    def __init__(self, db):
        super(FirefoxApplication, self).__init__()
        self.db = db
        self.add_resource('api', FirefoxAPIApplication(db))
    
    def get_failure_info(self, test, testtype, product, os, stale=False):
        k = [test, testtype, product, os]
        kwargs = {'descending':True, 'limit':1, 'startkey':k+[True], 'endkey':k+[{}]}
        if stale:
            kwargs['stale'] = 'ok'
        lastsuccess = self.db.views.results.testByTimestampResult(**kwargs)
            
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
        
        firstfailed = self.db.views.results.testByTimestampResult(**kwargs)[0]
                
        return {"lastsuccess":lastsuccess, "firstfailed":firstfailed}
    
    def create_failure_document(self, doc, stale=False):
        """Create failure_info Document for testrun document"""
        # tests = [k for k,v in doc.tests.items() if v.get('fail',0) is not 0]
        tests = [t['name'] for t in doc.tests if t['result'] == False]
        fails = dict([(test, self.get_failure_info(test, doc.testtype, doc.product, doc.os, stale=stale),) 
                    for test in tests
                    ])
        doc.pop('tests')
        # new_failures = []
        # for name, test in fails:
        #     if test['firstfailed']['_id'] == doc._id:
        #         new_failures
        
        failure_info = {'run':doc, 'fails':fails, 'type':'failure-info',}
        
        if len(self.db.views.failures.failureByID(key=doc._id)) is 0:
            return self.db.create(failure_info)
    
    def update_failure_documents(self):
        latest = self.db.views.failures.failureByTimestamp(descending=True, limit=1)
        if len(latest) is 0:
            endkey = None
        else:
            endkey = latest[0].run["timestamp"][:-1]
        rows = self.db.views.results.runByTimestamp(descending=True, startkey={}, endkey=endkey)

        for doc in rows:
            self.create_failure_document(doc, stale=True)

class FirefoxAPIApplication(FirefoxApplication):
    def __init__(self, db):
        RestApplication.__init__(self)
        self.db = db
    def POST(self, request, collection):
        if collection == 'testrun':
            obj = json.loads(str(request.body))
            if 'tests' not in obj:
                return Response('invalid, has not tests')
            obj['type'] = 'test-run'
            info = self.db.create(obj)
        
            f_info = self.create_failure_document(self.db.get(info['id']), stale=False)
        return JSONResponse({'testrun':info,'failure_info':f_info})


