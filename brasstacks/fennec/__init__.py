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
    
    def get_failure_info(self, test, testtype, os):
        k = [test, testtype, os]
        lastsuccess = self.db.views.fennec.testByTimestampResult(descending=True, limit=1, 
            startkey=k+[True], endkey=k+[{}])
        if len(lastsuccess) is not 0:
            lastsuccess = lastsuccess[0]
        else:
            lastsuccess = None
        
        if lastsuccess:
            startkey = k + [False, lastsuccess['timestamp']]
        else:
            startkey = k + [False]
        
        firstfailed = self.db.views.fennec.testByTimestampResult(limit=1, 
                startkey=startkey, endkey=k+[False, {}])[0]
                
        return {"lastsuccess":lastsuccess, "firstfailed":firstfailed}
    
    def update_failure_documents(self):
        latest = self.db.views.fennecFailures.failureInfoByTimestamp(descending=True, limit=1)
        if len(latest) is 0:
            endkey = None
        else:
            endkey = latest[0].run["timestamp"]
        rows = self.db.views.fennec.runByTimestamp(descending=True, startkey={}, endkey=endkey)

        for doc in rows:
            tests = [k for k,v in doc.tests.items() if v.get('fail',0) is not 0]
            fails = dict([(test, self.get_failure_info(test, doc.testtype, doc.os),) 
                        for test in tests
                        ])
            doc.pop('tests')
            failure_info = {'run':doc, 'fails':fails, 'type':'fennec-failure-info',}
            if len(self.db.views.fennecFailures.failureInfoByID(key=doc._id)) is 0:
                self.db.create(failure_info)
        
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

