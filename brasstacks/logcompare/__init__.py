import os
from datetime import datetime

try:
    import json
except:
    import simplejson as json

from markdown import markdown
from webenv import HtmlResponse, Response
from mako.template import Template
from mako.lookup import TemplateLookup
from webenv.rest import RestApplication

from logcompare import Then

this_directory = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(this_directory, 'templates')
design_doc = os.path.join(this_directory, 'logcompareviews')
testdesign_doc = os.path.join(this_directory, 'testviews')
lookup = TemplateLookup(directories=[template_dir], encoding_errors='ignore', input_encoding='utf-8', output_encoding='utf-8')

class MakoResponse(HtmlResponse):
    def __init__(self, name, **kwargs):
        self.body = lookup.get_template(name + '.mko').render_unicode(**kwargs).encode('utf-8', 'replace')
        self.headers = []
    
class LogCompareResponse(HtmlResponse):
    def __init__(self, name, starttime=None, **kwargs):
        if starttime is None:
            kwargs['latency'] = starttime
        else:
            kwargs['latency'] = datetime.now() - starttime
        self.body = lookup.get_template(name + '.mko').render_unicode(**kwargs).encode('utf-8', 'replace')
        self.headers = []

# TODO
class RSSResponse(Response):
    content_type = 'application/json'
    def __init__(self, body):
        self.body = json.dumps(body)
        self.headers = []

class LogCompareApplication(RestApplication):
    def __init__(self, db):
        super(LogCompareApplication, self).__init__()
        self.db = db
        self.vu = self.db.views.logcompare
  
    def GET(self, request, collection=None, resource=None):
        
        starttime = datetime.now()
        
        if collection is None:
            
            limit = int(request.query.get('count', 10))
            page = request.query.get('page', None)
            link = request.query.get('link', None)
            
            if page == 'prev' and link is not None:
                summary = self.vu.runSummaryByTimestamp(group=True, descending=True, limit=limit + 1, endkey=json.loads(link)).items()
            elif page == 'next' and link is not None:
                summary = self.vu.runSummaryByTimestamp(group=True, descending=True, limit=limit + 1, startkey=json.loads(link)).items()
            else:
                summary = self.vu.runSummaryByTimestamp(group=True, descending=True, limit=limit + 1).items()
            
            prev_startkey, value = summary[0] 
            next_startkey, value = summary[len(summary) - 1]
            summary = summary[0:len(summary) - 1]
            
            runs = self.vu.runCounts(group=True).items()
            
            return LogCompareResponse(
                "index", starttime, summary=summary, limit=limit, prev_startkey=json.dumps(prev_startkey), 
                next_startkey=json.dumps(next_startkey), runs=runs)
                
          
        if collection == "run":
            if resource is None:
                return MakoResponse("error", error="No test run ID given as input")
            else:
                doc = self.vu.entireRunByDocId(key=resource).items()
                if len(doc) is 0:
                    return MakoResponse("error", error="Test run ID cannot be found")
                else:
                    run = Run(doc)
                    similardocs = self.find_previous(doc, 10)
                    status = request.query.get('tests', "fail")
                    tests = run.get_tests(self.db, status)
                    return MakoResponse("run", run=run, tests=tests, similardocs=similardocs, status=status)

        if collection == "compare":
            if resource is None:
                return MakoResponse("error", error="No input is given")
            else:
                inputs = resource.split('&')
                if len(inputs) is 1:
                    doc1 = self.vu.entireRunByDocId(key=inputs[0]).items()
                    if len(doc1) is 0:
                        return MakoResponse("error", error="Test run ID cannot be found")
                    else:
                        buildid2 = self.find_last(doc1)
                        print buildid2
                        if buildid2 is None:
                            return MakoResponse("error", error="This test run has no prior runs")
                        else:
                            doc2 = self.vu.entireRunByDocId(key=buildid2).items()
                elif len(inputs) is 2:
                    doc1 = self.vu.entireRunByDocId(key=inputs[0]).items()
                    doc2 = self.vu.entireRunByDocId(key=inputs[1]).items()
                    if len(doc1) is 0 or len(doc2) is 0:
                        return MakoResponse("error", error="Test run IDs cannot be found")
                if doc1 == doc2:
                    return MakoResponse("error", error="Cannot compare with itself")
                else:
                    # comparetype = int(request.query.get('comparetype', 'newfails'))
                    run1 = Run(doc1)
                    run2 = Run(doc2)
                    answer = run1.compare(run2)
                    return MakoResponse("compare", answer=answer, run1=run1, run2=run2)

        if collection == "runs":
            if resource is None:
                return MakoResponse("error", error="not implemented yet")
            else:
                product = request.query.get('product')
                os = request.query.get('os')
                testtype = request.query.get('testtype')
                
                if product is None and os is None and testtype is None:
                    return MakoResponse("error", error="Inputs given are not complete")
                else:
                    summary = self.vu.runSummaryByTimestamp(
                            startkey=[{}, product, os, testtype, {}], 
                            endkey=[0, product, os, testtype, 0], 
                            descending=True, group=True).items()
                            
                    runs = self.vu.runCounts(group=True).items()
                    
                    return MakoResponse("runs", runs=runs, summary=summary)
                        
      
        if collection == "test":
            if resource is None:
                return MakoResponse("error", error="not implemented yet")
            else:
                product = request.query.get('product')
                os = request.query.get('os')
                testtype = request.query.get('testtype')
                
                if product is None or os is None or testtype is None:
                    return MakoResponse("error", error="not implemented yet")
                else:
                    similarruns = self.vu.testsByMetadata(
                        startkey=[product, os, testtype, {}], 
                        endkey=[product, os, testtype, 0],
                        descending=True, limit=100).items()
                    
                    for key, value in similarruns:
                        tests = value[0]
                        docid = value[1]
                        if resource in tests:                            
                            result = tests[resource]
                            tests.clear()
                            tests[resource] = result
                        else:
                            tests.clear()
                    
                    return MakoResponse("test", results=similarruns, testname=resource, product=product, os=os, testtype=testtype)
        
        if collection == "failures":
            lastbuild = self.vu.summaryBuildsByMetadata(group=True, descending=True, limit=1).items()
            (key, value) = lastbuild[0]
            buildid = key[1]
            doc = self.vu.entireBuildsById(key=buildid).items()
            run = Run(doc)
            buildtests = run.getTests()
            tests = {}
            
            for (testname, result) in buildtests.tests:
                results = {}
                
                firstfail = self.vu.allFailsByTimestamp(
                    startkey=[testname, {}], endkey=[testname, 0], descending=True, limit=1).items()
                
                lastpass = self.vu.allPassesByTimestamp(
                    startkey=[testname, 0], endkey=[testname, {}], descending=False, limit=1).items()
                
                if len(firstfail) is 0:
                    results['firstfail'] = None
                else:
                    (key, value) = firstfail[0]
                    buildid = value[1]
                    results['firstfail'] = buildid
                
                if len(lastpass) is 0:
                    results['lastpass'] = None
                else:
                    (key, value) = lastpass[0]
                    buildid = value[1]
                    results['lastpass'] = buildid
                  
                tests[testname] = results
            
            return MakoResponse("failures", tests=tests)
        
        if collection == "build":
            if resource is None:
                return MakoResponse("error", error="not implemented yet")
            else:
                runs = self.vu.tests(
                    startkey=[resource, {}], endkey=[resource, 0], descending=True).items()
                return MakoResponse("test", results=results)
    
    def POST(self, request, collection = None, resource = None):
        if collection == "compare":
            if request['CONTENT_TYPE'] == "application/x-www-form-urlencoded":
                if not hasattr(request.body, 'form'):
                    return MakoResponse("error", error="body has no form")
                else:
                    if 'runid1' not in request.body.form or 'runid2' not in request.body.form:
                        return MakoResponse("error", error="inputs cannot be blank")
                    else:
                        doc1 = self.vu.entireRunByDocId(key=request.body['runid1']).items()
                        doc2 = self.vu.entireRunByDocId(key=request.body['runid2']).items()
        
                        if len(doc1) is 0 or len(doc2) is 0:
                            return MakoResponse("error", error="input is not a valid run id")
                        else:
                            if doc1 == doc2:
                                return MakoResponse("error", error="cannot compare with itself")
                            else:
                                run1 = Run(doc1)
                                run2 = Run(doc2)
                                answer = run1.compare(run2)
                                return MakoResponse("compare", answer=answer, run1=run1, run2=run2)
  
    # def findTenPrevious(self, doc):
        # # max limit of the results
        # length = 11
        # # entry of self
        # selfentry = 0
        
        # if len(doc) is 0:
            # return None
        # else:
            # (key, value) = doc[0]
            # product = value['product']
            # os = value['os']
            # testtype = value['testtype']
            # timestamp = value['timestamp']
            
            # similardocs = self.vu.buildIdsByMetadata(
                # startkey=[product, os, testtype, timestamp], 
                # endkey=[product, os, testtype, 0], 
                # descending=True, 
                # limit=length).items()
          
            # if len(similardocs) > 0:
                # del similardocs[selfentry]
            # return similardocs
  
    # def findPrevious(self, doc):
        # # querying must return one result: its previous
        # minlength = 1
        # # when sorted in reverse-chronological order from the current build, 
        # # the index of the previous build is 0
        # previous = 0
        
        # similardocs = self.findTenPrevious(doc)
        
        # if similardocs is None:
            # return None
        # else:
            # if len(similardocs) < minlength:
                # return None
            # else:
                # (key, value) = similardocs[previous]
                # return value

    def find_previous(self, doc, limit=10):
        # max limit of the results
        length = limit + 1
        # entry of self
        selfentry = 0
        similardocs = []
        if len(doc) is 0:
            return similardocs
        else:
            (key, value) = doc[0]
            product = value['product']
            os = value['os']
            testtype = value['testtype']
            timestamp = value['timestamp']
            
            similardocs = self.vu.docIdsByMetadata(
                startkey=[product, os, testtype, timestamp], 
                endkey=[product, os, testtype, 0], 
                descending=True, 
                limit=length).items()
          
            if len(similardocs) > 0:
                del similardocs[selfentry]
            return similardocs
  
    def find_last(self, doc):
        # querying must return one result: its previous
        minlength = 1
        # when sorted in reverse-chronological order from the current build, 
        # the index of the previous build is 0
        previous = 0
        
        similardocs = self.find_previous(doc, minlength)
        
        if len(similardocs) < minlength:
            return None
        else:
            (key, value) = similardocs[previous]
            return value
                
class Run(object):
    def __init__(self, doc):
        (key, value) = doc[0]
        self.doc = value
        self.docid = self.doc['_id']
        self.buildid = self.doc['build']
        self.product = self.doc['product']
        self.os = self.doc['os']
        self.testtype = self.doc['testtype']
        self.timestamp = self.doc['timestamp']
        # self.timestamp = Then(self.doc['timestamp'])
        self.tests = self.doc['tests']

    def compare(self, run):
        
        newtestfiles = []
        missingtestfiles = []
        
        prevlynotfails = []
        prevlynotpasses = []
        prevlynottodos = []
        
        missingfails = []
        missingpasses = []
        missingtodos = []
        
        newfails = []
        newpasses = []
        newtodos = []
        
        stabletests = []
        
        tests1 = self.tests
        tests2 = run.tests
        
        for testfile in tests1:
          
            if testfile not in tests2:
                newtestfiles.append({'testfile': testfile, 'result': tests1[testfile]})
            else:
                result1 = tests1[testfile]
                result2 = tests2[testfile]

                sum1 = result1['fail'] + result1['pass'] + result1['todo']
                sum2 = result2['fail'] + result2['pass'] + result2['todo']
              
                if sum1 == sum2: 
                    if result1['fail'] == result2['fail'] and result1['pass'] == result2['pass'] and result1['todo'] == result2['todo']:
                        stabletests.append({'testfile': testfile, 'result': tests1[testfile]})
                    else:
                        if result1['fail'] > result2['fail']:
                            prevlynotfails.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result1['fail'] - result2['fail']})
                        if result1['pass'] > result2['pass']:
                            prevlynotpasses.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result1['pass'] - result2['pass']})
                        if result1['todo'] > result2['todo']:
                            prevlynottodos.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result1['todo'] - result2['todo']})
                
                elif sum1 < sum2:
                    if result1['fail'] < result2['fail']:
                        missingfails.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result2['fail'] - result1['fail']})
                    if result1['pass'] < result2['pass']:
                        missingpasses.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result2['fail'] - result1['fail']})
                    if result1['todo'] < result2['todo']:
                        missingtodos.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result2['fail'] - result1['fail']})
                  
                else:
                    if result1['fail'] > result2['fail']:
                        newfails.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result1['fail'] - result2['fail']})
                    if result1['pass'] > result2['pass']:
                        newpasses.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result1['fail'] - result2['fail']})
                    if result1['todo'] > result2['todo']:
                        newtodos.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result1['fail'] - result2['fail']})

                del tests2[testfile]
        
        for remainingtestfile in tests2:
            missingtestfiles.append({'testfile': remainingtestfile, 'result': tests2[remainingtestfile]})
        
        result = {}
        result['newtestfiles'] = newtestfiles
        result['missingtestfiles'] = missingtestfiles
      
        result['stabletests'] = stabletests
        
        result['prevlynotfails'] = prevlynotfails
        result['prevlynotpasses'] = prevlynotpasses
        result['prevlynottodos'] = prevlynottodos
        
        result['missingfails'] = missingfails
        result['missingpasses'] = missingpasses
        result['missingtodos'] = missingtodos
        
        result['newfails'] = newfails
        result['newpasses'] = newpasses
        result['newtodos'] = newtodos
        
        return result

    def compare(self, run, comparetype='newfails'):
        
        results = []
        
        tests1 = self.tests
        tests2 = run.tests
        
        if comparetype == 'newfails':
            for testfile in tests1:
                if testfile in tests2:
                    result1 = tests1[testfile]
                    result2 = tests2[testfile]
                    sum1 = result1['fail'] + result1['pass'] + result1['todo']
                    sum2 = result2['fail'] + result2['pass'] + result2['todo']
                    if sum1 > sum2:
                        if result1['fail'] > result2['fail']:
                            results.append({
                                'testfile': testfile, 
                                'result1': tests1[testfile], 
                                'result2': tests2[testfile], 
                                'delta': result1['fail'] - result2['fail']})
        return results
        
        
    # note: %f directive not supported in python 2.5 so microsecond needs to be parsed manually
    def newer(self, run):
      
        directives = "%Y-%m-%d %H:%M:%S"
        
        parts = self.timestamp.split(".")
        dt1 = datetime.strptime(parts[0], directives)
        dt1 = dt1.replace(microsecond = int(parts[1]))
        
        parts = run.timestamp.split(".")
        dt2 = datetime.strptime(parts[0], directives)
        dt2 = dt2.replace(microsecond = int(parts[1]))
        
        # true if self's time is later than run's time
        return dt > dt2

    def get_tests(self, db, status="all"):
        
        # get the tests based on user option
        result = []
        if status == "all":
            for item in self.tests.items():
                result.append(item)
        elif status == "fail":
            for item in self.tests.items():
                key, value = item
                if value['fail'] > 0:
                    result.append(item)
        elif status == "pass":
            for item in self.tests.items():
                key, value = item
                if value['pass'] > 0:
                    result.append(item)
        elif status == "todo":
            for item in self.tests.items():
                key, value = item
                if value['todo'] > 0:
                    result.append(item)
        elif status == "zerofail":
            for item in self.tests.items():
                key, value = item
                if value['fail'] == 0:
                    result.append(item)
        elif status == "zeropass":
            for item in self.tests.items():
                key, value = item
                if value['pass'] == 0:
                    result.append(item)
        elif status == "zerotodo":
            for item in self.tests.items():
                key, value = item
                if value['todo'] == 0:
                    result.append(item)
        else:
            for item in self.tests.items():
                result.append(item)
        
        # aggregate the counts
        self.totalfails = 0
        self.totalpasses = 0
        self.totaltodos = 0
        
        for key, value in result:
            self.totalfails += value['fail']
            self.totalpasses += value['pass']
            self.totaltodos += value['todo']
        
        self.numtestfiles = len(result)
        self.totaltests = self.totalfails + self.totalpasses + self.totaltodos
        self.filteredtests = result
        
        # for each test, find it's last change
        for key, value in self.filteredtests:
            if value['fail'] > 0 or value['todo'] > 0:
                self.prevdocs = db.views.logcompare.testresultByTestnameMetadata(
                    startkey=[key, self.product, self.os, self.testtype, self.timestamp], 
                    endkey=[key, self.product, self.os, self.testtype, 0], 
                    descending=True, 
                    limit=100).items()
                ago = 0
                value['lastchange'] = None
                for k, v in self.prevdocs:
                    res = v[0]
                    docid = v[1]
                    if res['fail'] != value['fail'] or res['pass'] != value['pass'] or res['todo'] != value['todo']:
                        ago += 1
                        value['lastchange'] = {'run': docid, 'ago': ago}
                        break
                    else:
                        for msg in value['note']:
                            if msg not in res['note']:
                                ago += 1
                                value['lastchange'] = {'run': docid, 'ago': ago}
                                break

# 11:51:54 AM) mikeal: for (testname, result) in [(k, v,) for k, v in buildtests.tests.items() if v.fail is 0]
# (11:52:08 AM) mikeal: for (testname, result) in [(k, v,) for k, v in doc.tests.items() if v.fail is 0]:
# (11:52:43 AM) mikeal: for (testname, result) in [(k, v,) for k, v in doc.tests.items() if v.fail is not 0]