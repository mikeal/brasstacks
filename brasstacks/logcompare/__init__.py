import os
from datetime import datetime

try:
    import json as simplejson
except ImportError:
    import simplejson

from markdown import markdown
from webenv import HtmlResponse
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

class LogCompareApplication(RestApplication):
    def __init__(self, db):
        super(LogCompareApplication, self).__init__()
        self.db = db
        self.vu = self.db.views.logcompare
  
    def GET(self, request, collection=None, resource=None):
        
        starttime = datetime.now()
        
        if collection is None:
            
            # variables used to control 'states' in results paging
            limit = int(request.query.get('count', 10))
            page = request.query.get('page', 'newest')
            group = int(request.query.get('group', 0))
            
            # TODO: further error checking
            if page == 'newest':
                summary = self.vu.runSummaryByTimestamp(group=True, descending=True, limit=limit).items() 
                group = 0
            elif page == 'newer':
                if group > 0:
                    group -= 1
                else:
                    group = 0
                skip = limit * group
                summary = self.vu.runSummaryByTimestamp(group=True, descending=True, limit=limit, skip=skip).items()
            elif page == 'older':
                group += 1
                skip = limit * group
                summary = self.vu.runSummaryByTimestamp(group=True, descending=True, limit=limit, skip=skip).items()
            
            runs = self.vu.runCounts(group=True).items()
            
            return LogCompareResponse("index", starttime, summary=summary, limit=limit, group=group, runs=runs)
          
        if collection == "run":
            if resource is None:
                return MakoResponse("error", error="no build id input is given")
            else:
                doc = self.vu.entireRunByDocId(key=resource).items()
                if len(doc) is 0:
                    return MakoResponse("error", error="build id cannot be found")
                else:
                    status = request.query.get('tests', "all")
                    similardocs = self.find_previous(doc, 10)
                    build = Build(doc)
                    buildtests = build.get_tests(status)
                    return MakoResponse("run", build=build, buildtests=buildtests, similardocs=similardocs)

        if collection == "compare":
            if resource is None:
                return MakoResponse("error", error="no input is given")
            else:
              
                inputs = resource.split('&')
                
                if len(inputs) is 1:
                    doc1 = self.vu.entireBuildsById(key=inputs[0]).items()
                    if len(doc1) is 0:
                        return MakoResponse("error", error="build id cannot be found")
                    else:
                        buildid2 = self.findPrevious(doc1)
                        if buildid2 is None:
                            return MakoResponse("error", error="this build has no prior builds")
                        else:
                            doc2 = self.vu.entireBuildsById(key=buildid2).items()
                elif len(inputs) is 2:
                    doc1 = self.vu.entireBuildsById(key=inputs[0]).items()
                    doc2 = self.vu.entireBuildsById(key=inputs[1]).items()
                    if len(doc1) is 0 or len(doc2) is 0:
                        return MakoResponse("error", error="build ids cannot be found")
                
                if doc1 == doc2:
                    return MakoResponse("error", error="cannot compare with itself")
                else:
                    build1 = Build(doc1)
                    build2 = Build(doc2)
                    
                    answer = build1.compare(build2)
                    return MakoResponse("compare", answer=answer, build1=build1, build2=build2)

        if collection == "product":
            if resource is None:
                return MakoResponse("error", error="not implemented yet")
            else:
                buildsbyproduct = self.vu.metadataByProduct(
                    startkey=[resource, {}], endkey=[resource, 0], descending=True).items()
                return MakoResponse("product", buildsbyproduct=buildsbyproduct)

        if collection == "testtype":
            if resource is None:
                return MakoResponse("error", error="not implemented yet")
            else:
                buildsbytesttype = self.vu.metadataByTesttype(
                    startkey=[resource, {}], endkey=[resource, 0], descending=True).items()
                return MakoResponse("testtype", buildsbytesttype=buildsbytesttype)

        if collection == "platform":
            if resource is None:
                return MakoResponse("error", error="not implemented yet")
            else:
                buildsbyplatform = self.vu.metadataByPlatform(
                    startkey=[resource, {}], endkey=[resource, 0], descending=True).items()
                return MakoResponse("platform", buildsbyplatform=buildsbyplatform)

        if collection == "builds":
            if resource is None:
                return MakoResponse("error", error="not implemented yet")
            else:
                input = resource.split('+')
                if len(input) < 3:
                    return MakoResponse("error", error="not enough build info")
                else:
                    builds = self.vu.buildIdsByMetadata(
                        startkey=[input[0], input[1], input[2], {}], 
                        endkey=[input[0], input[1], input[2], 0], 
                        descending=True).items()
                    return MakoResponse("builds", builds=builds)
      
        if collection == "test":
            if resource is None:
                return MakoResponse("error", error="not implemented yet")
            else:
                results = self.vu.tests(
                    startkey=[resource, {}], endkey=[resource, 0], descending=True).items()
                return MakoResponse("test", results=results)
      
        if collection == "failures":
            lastbuild = self.vu.summaryBuildsByMetadata(group=True, descending=True, limit=1).items()
            (key, value) = lastbuild[0]
            buildid = key[1]
            doc = self.vu.entireBuildsById(key=buildid).items()
            build = Build(doc)
            buildtests = build.getTests()
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
  
    def POST(self, request, collection = None, resource = None):
        if collection == "compare":
            if request['CONTENT_TYPE'] == "application/x-www-form-urlencoded":
                if not hasattr(request.body, 'form'):
                    return MakoResponse("error", error="body has no form")
                else:
                    if 'buildid1' not in request.body.form or 'buildid2' not in request.body.form:
                        return MakoResponse("error", error="inputs cannot be blank")
                    else:
                        doc1 = self.vu.entireBuildsById(key=request.body['buildid1']).items()
                        doc2 = self.vu.entireBuildsById(key=request.body['buildid2']).items()
        
                        if len(doc1) is 0 or len(doc2) is 0:
                            return MakoResponse("error", error="input is not a valid build id")
                        else:
                            if doc1 == doc2:
                                return MakoResponse("error", error="cannot compare with itself")
                            else:
                                build1 = Build(doc1)
                                build2 = Build(doc2)
                                answer = build1.compare(build2)
                                return MakoResponse("compare", answer = answer, build1 = build1, build2 = build2)
  
    def findTenPrevious(self, doc):
        # max limit of the results
        length = 11
        # entry of self
        selfentry = 0
        
        if len(doc) is 0:
            return None
        else:
            (key, value) = doc[0]
            product = value['product']
            os = value['os']
            testtype = value['testtype']
            timestamp = value['timestamp']
            
            similardocs = self.vu.buildIdsByMetadata(
                startkey=[product, os, testtype, timestamp], 
                endkey=[product, os, testtype, 0], 
                descending=True, 
                limit=length).items()
          
            if len(similardocs) > 0:
                del similardocs[selfentry]
            return similardocs
  
    def findPrevious(self, doc):
        # querying must return one result: its previous
        minlength = 1
        # when sorted in reverse-chronological order from the current build, 
        # the index of the previous build is 0
        previous = 0
        
        similardocs = self.findTenPrevious(doc)
        
        if similardocs is None:
            return None
        else:
            if len(similardocs) < minlength:
                return None
            else:
                (key, value) = similardocs[previous]
                return value

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
                
class Build(object):
    def __init__(self, doc):
        (key, value) = doc[0]
        self.doc = value
        self.docid = self.doc['_id']
        self.buildid = self.doc['build']
        self.product = self.doc['product']
        self.os = self.doc['os']
        self.testtype = self.doc['testtype']
        self.timestamp = Then(self.doc['timestamp'])
        self.tests = self.doc['tests']

    def get_tests(self, status):
        return TestsResult(self.tests, status)
    
    def compare(self, build):
      
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
        tests2 = build.tests
        
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
  
    # note: %f directive not supported in python 2.5 so microsecond needs to be parsed manually
    def newer(self, build):
      
        directives = "%Y-%m-%d %H:%M:%S"
        
        parts = self.timestamp.split(".")
        dt1 = datetime.strptime(parts[0], directives)
        dt1 = dt1.replace(microsecond = int(parts[1]))
        
        parts = build.timestamp.split(".")
        dt2 = datetime.strptime(parts[0], directives)
        dt2 = dt2.replace(microsecond = int(parts[1]))
        
        # true if self's time is later than build's time
        return dt > dt2

class TestsResult(object):
    def __init__(self, tests, status):
        
        result = []
        if status == "fail":
            print status
            for item in tests.items():
                key, value = item
                if value['fail'] > 0:
                    result.append(item)
        elif status == "all":
            print status
            for item in tests.items():
                result.append(item)
        
        self.totalfails = 0
        self.totalpasses = 0
        self.totaltodos = 0
        
        for key, value in result:
            self.totalfails += value['fail']
            self.totalpasses += value['pass']
            self.totaltodos += value['todo']
        
        self.numtestfiles = len(result)
        self.totaltests = self.totalfails + self.totalpasses + self.totaltodos
        self.tests = result
            
    # def smart_sum(x, y):
      # x['totalfails'] += y['fail']
      # x['totalpasses'] += y['pass']
      # x['totaltodos'] += y['todo']
    
    # totals = reduce(smart_sum, tests.values(), {"totalfails":0, "totalpasses":0, "totaltodos":0})
    
    # for key, value in totals.items():
      # setattr(self, key, value)
      
      # 11:51:54 AM) mikeal: for (testname, result) in [(k, v,) for k, v in buildtests.tests.items() if v.fail is 0]
# (11:52:08 AM) mikeal: for (testname, result) in [(k, v,) for k, v in doc.tests.items() if v.fail is 0]:
# (11:52:43 AM) mikeal: for (testname, result) in [(k, v,) for k, v in doc.tests.items() if v.fail is not 0]