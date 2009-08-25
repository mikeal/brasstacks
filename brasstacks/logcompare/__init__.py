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

this_directory = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(this_directory, 'templates')
design_doc = os.path.join(this_directory, 'views')
testdesign_doc = os.path.join(this_directory, 'testviews')
lookup = TemplateLookup(directories=[template_dir], encoding_errors='ignore', input_encoding='utf-8', output_encoding='utf-8')

class MakoResponse(HtmlResponse):
  def __init__(self, name, **kwargs):
    self.body = lookup.get_template(name + '.mko').render_unicode(**kwargs).encode('utf-8', 'replace')
    self.headers = []

class LogCompareApplication(RestApplication):
  def __init__(self, db):
    super(LogCompareApplication, self).__init__()
    self.db = db
  
  def GET(self, request, collection=None, resource=None):
    if collection is None:
      
      products = self.db.views.fennecResults.productCounts(reduce = True, group = True).items()
      testtypes = self.db.views.fennecResults.testtypeCounts(reduce = True, group = True).items()
      oses = self.db.views.fennecResults.osCounts(reduce = True, group = True).items()
      builds = self.db.views.fennecResults.buildCounts(reduce = True, group = True).items()
      summary = self.db.views.fennecResults.summaryBuildsByMetadata(reduce = True, group = True, descending=True, limit=20).items()
      
      return MakoResponse("index", products = products, testtypes = testtypes, oses = oses, builds = builds, summary = summary)
      
    if collection == "build":
      if resource is None:
        return MakoResponse("error", error="no build id input is given")
      else:
        doc = self.db.views.fennecResults.entireBuildsById(key = resource).items()
        if len(doc) == 0:
          return MakoResponse("error", error="build id cannot be found")
        else:
          similardocs = self.findTenPrevious(doc)
          build = Build(doc)
          buildtests = build.getTests()
          return MakoResponse("build", build = build, buildtests = buildtests, similardocs = similardocs)

    if collection == "compare":
      if resource is None:
        return MakoResponse("error", error="no input is given")
      else:
        
        inputs = resource.split('&')
        
        if len(inputs) == 1:
          doc1 = self.db.views.fennecResults.entireBuildsById(key=inputs[0]).items()
          if len(doc1) == 0:
            return MakoResponse("error", error="build id cannot be found")
          else:
            buildid2 = self.findPrevious(doc1)
            if buildid2 == None:
              return MakoResponse("error", error="this build has no prior builds")
            else:
              doc2 = self.db.views.fennecResults.entireBuildsById(key=buildid2).items()
        elif len(inputs) == 2:
          doc1 = self.db.views.fennecResults.entireBuildsById(key=inputs[0]).items()
          doc2 = self.db.views.fennecResults.entireBuildsById(key=inputs[1]).items()
          if len(doc1) == 0 or len(doc2) == 0:
            return MakoResponse("error", error="build ids cannot be found")
        
        build1 = Build(doc1)
        build2 = Build(doc2)
        
        answer = build1.compare(build2)
        return MakoResponse("compare", answer = answer, build1 = build1, build2 = build2)

    if collection == "product":
      if resource is None:
        return MakoResponse("error", error="not implemented yet")
      else:
        buildsbyproduct = self.db.views.fennecResults.metadataByProduct(startkey=[resource, {}], endkey=[resource, 0], descending=True).items()
        return MakoResponse("product", buildsbyproduct=buildsbyproduct)

    if collection == "testtype":
      if resource is None:
        return MakoResponse("error", error="not implemented yet")
      else:
        buildsbytesttype = self.db.views.fennecResults.metadataByTesttype(
          startkey=[resource, {}], endkey=[resource, 0], descending=True).items()
        return MakoResponse("testtype", buildsbytesttype=buildsbytesttype)

    if collection == "platform":
      if resource is None:
        return MakoResponse("error", error="not implemented yet")
      else:
        buildsbyplatform = self.db.views.fennecResults.metadataByPlatform(
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
          builds = self.db.views.fennecResults.buildIdsByMetadata(
            startkey=[input[0], input[1], input[2], {}], 
            endkey=[input[0], input[1], input[2], 0], 
            descending=True).items()
          return MakoResponse("builds", builds=builds)
    if collection == "test":
      if resource is None:
        return MakoResponse("error", error="not implemented yet")
      else:
        results = self.db.views.fennecResults.tests(
          startkey=[resource, {}], 
          endkey=[resource, 0], 
          descending=True).items()
        return MakoResponse("test", results=results)
      
  def POST(self, request, collection = None, resource = None):
    if collection == "compare":
      if request['CONTENT_TYPE'] == "application/x-www-form-urlencoded":
        # if ('buildid1' in request.body) and ('buildid2' in request.body): # TODO: correctly check for blank input
        id1 = request.body['buildid1']
        id2 = request.body['buildid2']
        # else: 
          # return MakoResponse("error", error="inputs cannot be blank")
        
        doc1 = self.db.views.fennecResults.entireBuildsById(key = id1).items()
        doc2 = self.db.views.fennecResults.entireBuildsById(key = id2).items()
        
        if len(doc1) == 0 or len(doc2) == 0:
          return MakoResponse("error", error="input is not a valid build id")
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
    
    if len(doc) == 0:
      return None
    else:
      (key, value) = doc[0]
      product = value['product']
      os = value['os']
      testtype = value['testtype']
      timestamp = value['timestamp']
      
      similardocs = self.db.views.fennecResults.buildIdsByMetadata(
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
    
    if similardocs == None:
      return None
    else:
      if len(similardocs) < minlength:
        return None
      else:
        (key, value) = similardocs[previous]
        return value

class Build():
  def __init__(self, doc):
   
    (key, value) = doc[0]
    self.doc = value
    self.docid = self.doc['_id']
    self.buildid = self.doc['build']
    self.product = self.doc['product']
    self.os = self.doc['os']
    self.testtype = self.doc['testtype']
    self.timestamp = self.doc['timestamp']
    self.tests = self.doc['tests']

  def getTests(self):
    return TestsResult(self.tests)
    
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
              # prevlynotfails.append({'testfile': testfile, 'delta': result1['fail'] - result2['fail'], 'failnotes': result1['note'].split(', ')})
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

class TestsResult():
  def __init__(self, tests):
    self.numtestfiles = len(tests)
    items = tests.iteritems()
    
    self.totalfails = 0
    self.totalpasses = 0
    self.totaltodos = 0
    
    for (key, value) in items:
      self.totalfails = self.totalfails + value['fail']
      self.totalpasses = self.totalpasses + value['pass']
      self.totaltodos = self.totaltodos + value['todo']
    
    self.totaltests = self.totalfails + self.totalpasses + self.totaltodos
    self.tests = tests.iteritems()
    
class TestDelta():
  def __init__(self, name, notes, delta):
    self.name = ''
    self.failnotes = ''
    self.count = 0
  def parsefailnotes(self):
    return False

class Test():
  def __init__(self, testfile, result):
    self.testfile = testfile
    self.result = result
    self.totalfail = self.result['fail']
    self.totalpass = self.result['pass']
    self.totaltodo = self.result['todo']
    # self.notes = self.result['note'].split(',')
    self.notes = self.result['note']
  def totaltests():
    return self.totalfail + totalpass + totaltodo
  
# class ComparisonResult():
  # def __init__(self):
    # pass
  # def compare(self, build1, build2):
    # tests1 = build1['rows'][0]['value'][]
    # thisbuild = {}
    # thisbuild = build1['rows'][0]['value']
    # return thisbuild
    