import os
try:
  import json as simplejson
except ImportError:
  import simplejson
    
from datetime import datetime
from markdown import markdown

from webenv import HtmlResponse
from mako.template import Template
from mako.lookup import TemplateLookup
from webenv.rest import RestApplication

template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates')
design_doc = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'views')



class MakoResponse(HtmlResponse):
  def __init__(self, name, **kwargs):
    # mylookup = TemplateLookup()
    # self.body = Template(filename=os.path.join(template_dir, name+'.mko'), lookup=mylookup).render(**kwargs)
    self.body = Template(filename=os.path.join(template_dir, name+'.mko')).render(**kwargs)
    self.headers = []

class BuildCompareApplication(RestApplication):
  def __init__(self, db):
    super(BuildCompareApplication, self).__init__()
    self.db = db

  def GET(self, request, collection=None, resource=None):

    if collection is None:
      products = self.db.views.metadata.products(reduce = True, group = True)['rows']
      testtypes = self.db.views.metadata.testtypes(reduce = True, group = True)['rows']
      oses = self.db.views.metadata.operatingSystems(reduce = True, group = True)['rows']
      # metadata = 0 # self.db.views.metadata.displayMetadata(reduce = True)
      summary = self.db.views.results.summary(reduce = True, group = True)['rows']
      # all = 0 # self.db.views.results.allData(key = 'sampletest')
      # return MakoResponse("index", products = products, metadata = metadata, testtypes = testtypes, oses = oses, summary = summary, all = all)
      return MakoResponse("index", products = products, testtypes = testtypes, oses = oses, summary = summary)
      
    if collection == "build":
      if resource is None:
        return MakoResponse("error", error="no build id input is given")
      else:
        build = Build(self.db.views.results.allData(key = resource)['rows'])
        buildtests = build.getTests()
        return MakoResponse("build", build = build, buildtests = buildtests)

    if collection == "compare":
      if resource is None:
        return MakoResponse("error", error="no input is given")
      else:
        doc1 = self.db.views.results.allData(key=resource)['rows']
        if doc1 == []:
          return MakoResponse("error", error="build id cannot be found")
        else:
          buildid2 = self.findPrevious(doc1)
          if buildid2 == None:
            return MakoResponse("error", error="this build has no prior builds")
          else:
            doc2 = self.db.views.results.allData(key=buildid2)['rows']
            
            build1 = Build(doc1)
            build2 = Build(doc2)
            
            answer = build1.compare(build2)
            return MakoResponse("compare", answer = answer, doc1 = build1, doc2 = build2)

    if collection == "product":
      if resource is None:
        return MakoResponse("error", error="not implemented yet")
        # products = set(self.db.views.metadata.products(reduce=False).rows.keys())
        # return MakoResponse("products", products=products)
      else:
        buildsbyproduct = self.db.views.metadata.displayMetadataByProduct(
          startkey=[resource, {}, {}],
          endkey=[resource, 0, 0],
          descending=True)['rows']
        return MakoResponse("product", buildsbyproduct=buildsbyproduct)

    if collection == "testtype":
      return MakoResponse("error", error="not implemented yet")
    if collection == "platform":
      return MakoResponse("error", error="not implemented yet")
    # if collection == "tests":
      # if resource is None:
        # # List of last 100 tests by timestamp
        # pass
      # else:
        # test = self.db.get(resource)
        # # This is crap code, it's just there to show the whole object
        # return MakoResponse("test", test=test)
  
  def POST(self, request, collection = None, resource = None):
    if collection == "compare":
      if request['CONTENT_TYPE'] == "application/x-www-form-urlencoded":
        
        if ('buildid1' in request.body) and ('buildid2' in request.body): # TODO: correctly check for blank input
          id1 = request.body['buildid1']
          id2 = request.body['buildid2']
        else: 
          return MakoResponse("error", error="inputs cannot be blank")
          
        doc1 = self.db.views.results.allData(key = id1)['rows'] # "20090729070913"
        doc2 = self.db.views.results.allData(key = id2)['rows'] # "20090728200853"
        
        build1 = Build(doc1)
        build2 = Build(doc2)
        
        if (doc1 == []) or (doc2 == []):
          return MakoResponse("error", error="input is not a valid build id")
        else: 
          answer = build1.compare(build2)
        # if doc1['rows'] != [] and doc2['rows'] != []:
          # build1 = Build(doc1)
          # build2 = Build(doc2)
          # if build1.newer(build2):
            # answer = build1.compare(build2)
          # else:
            # answer = build2.compare(build1)
          # compare which one is newer build1.newer(build2)
          # answer = build1.compare(build2)
          # answer = 'both'
        # elif doc1['rows'] != [] or doc2['rows'] != []:
          # if doc1['rows'] != []:
            # # self.findPrevious(doc1)
            # answer = 'doc1'
          # else:
            # # answer = ComparisonResult(build2, findPrevious(build2))
            # answer = 'doc2'
        # else:
            # answer = 'None'
        
        return MakoResponse("compare", answer = answer, doc1 = build1, doc2 = build2)
  
  def findPrevious(self, doc):
    
    # querying must return two results: the current and its previous
    minlength = 2
    
    # when sorted in reverse-chronological order from the current build, 
    # the index of the previous build is 1
    previous = 1
    
    # max limit of the results
    maxlength = 10
    
    if doc == []:
      return None
    else:
      product = doc[0]['value']['product']
      os = doc[0]['value']['os']
      testtype = doc[0]['value']['testtype']
      timestamp = doc[0]['value']['timestamp']
      
      similardocs = self.db.views.metadata.metadataAsKeys(
        startkey=[product, os, testtype, timestamp], 
        endkey=[product, os, testtype, 0], 
        descending=True, 
        limit=maxlength)

      if len(similardocs['rows']) < minlength:
        return None
      else:
        return similardocs['rows'][previous]['value']
        
class Build():
  def __init__(self, doc):
   
    self.doc = doc[0]['value']
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
            stabletests.append(testfile)
          else:
            if result1['fail'] > result2['fail']:
              prevlynotfails.append(testfile)
            if result1['pass'] > result2['pass']:
              prevlynotpasses.append(testfile)
            if result1['todo'] > result2['todo']:
              prevlynottodos.append(testfile)
        
        elif sum1 < sum2:
          if result1['fail'] < result2['fail']:
            missingfails.append(testfile)
          if result1['pass'] < result2['pass']:
            missingpasses.append(testfile)
          if result1['todo'] < result2['todo']:
            missingtodos.append(testfile)
        
        else:
          if result1['fail'] > result2['fail']:
            newfails.append(testfile)
          if result1['pass'] > result2['pass']:
            newpasses.append(testfile)
          if result1['todo'] > result2['todo']:
            newtodos.append(testfile)

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
    self.notes = self.result['note'].split(',')
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
    