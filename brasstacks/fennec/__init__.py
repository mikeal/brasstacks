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
        
    def GET(self, request, collection=None, resource=None):
        if collection is None:
            limit = int(request.query.get('count', 20))
            runs = self.db.views.fennec.runByTimestamp(descending=True, limit=limit)
            return MakoResponse('runs', runs=runs, page_header="Latest "+str(limit)+" Runs")
        if collection == "detail":
            if resource is None:
                limit = int(request.query.get('count', 5))
                runs = self.db.views.fennec.runByTimestamp(descending=True, limit=limit)
                page_header = "Details for latest "+str(limit)+" Runs"
            else:
                runs = [self.db.get(resource)]
                page_header = "Details for Run "+resource
                
            def reduction(tests, run):
                for testname, test in run.tests.items():
                    if test.get('fail', 0) is not 0:
                        tests.append([testname, run.testtype, run.os])
                return tests
            
            def smart_set(l):
                r = []
                for i in l:
                    if i not in r:
                        r.append(i)
                return r
            failures = smart_set(reduce(reduction, runs, []))
            failure_info = dict([
                        ((test, testtype, os,), self.get_failure_info(test, testtype, os),) 
                        for test, testtype, os in failures
                        ])
                
            return MakoResponse('runsdetail', runs=runs, page_header=page_header, 
                                failure_info=failure_info)
                

