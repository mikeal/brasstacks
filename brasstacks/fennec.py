import os
try:
  import json as simplejson
except ImportError:
  import simplejson
    
from datetime import datetime
from markdown import markdown

from webenv import HtmlResponse
from mako.template import Template
from webenv.rest import RestApplication

template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fennec_templates')
design_doc = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fennec_views')



class MakoResponse(HtmlResponse):
  def __init__(self, name, **kwargs):
    self.body = Template(filename=os.path.join(template_dir, name+'.mko')).render(**kwargs)
    self.headers = []

class FennecApplication(RestApplication):
  def __init__(self, db):
    super(FennecApplication, self).__init__()
    self.db = db

  def GET(self, request, collection=None, resource=None):

    if collection is None:
      # products = 0 # self.db.views.metadata.products(reduce = True, group = True)
      # testtypes = 0 # self.db.views.metadata.testtypes(reduce = True, group = True)
      # oses = 0 # self.db.views.metadata.operatingSystems(reduce = True, group = True)
      # metadata = 0 # self.db.views.metadata.displayMetadata(reduce = True)
      # summary = 0 # self.db.views.results.summary(reduce = True, group = True)
      # all = 0 # self.db.views.results.allData(key = 'sampletest')
      # return MakoResponse("index", products = products, metadata = metadata, testtypes = testtypes, oses = oses, summary = summary, all = all)
      return MakoResponse("index")
      
    # if collection == "builds":
      # if resource is None:
          # List of last 100 builds by timestamp
          # pass
      # else:
          # Test info for specific build
          # build = self.db.views.results.allData(key = resource)
          # return MakoResponse("builds", build = build)

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
            return MakoResponse("compare", doc1 = answer, doc2 = doc2)

    # if collection == "product":
      # if resource is None:
        # products = set(self.db.views.metadata.products(reduce=False).rows.keys())
        # return MakoResponse("products", products=products)
      # else:
        # tests = self.db.views.fennecBrasstacks.testsByProduct(key=resource).rows
        # return MakoResponse("product", tests=tests)

    # if collection == "testtype":
      # pass
    # if collection == "platform":
      # pass
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
        
        id1 = request.body['buildid1']
        id2 = request.body['buildid2'] # TODO: if either is blank, code breaks
        
        doc1 = self.db.views.results.allData(key = "20090729070913")['rows']
        doc2 = self.db.views.results.allData(key = "20090728200853")['rows']
        
        build1 = Build(doc1)
        build2 = Build(doc2)
        
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
        
        return MakoResponse("compare", 
          answer = simplejson.dumps(answer, indent=2, sort_keys=True), 
          doc1 = doc1[0]['value']['tests'], 
          doc2 = doc2[0]['value']['tests'])
  
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
    self.docId = doc[0]['value']['_id']
    self.buildId = doc[0]['value']['build']
    self.product = doc[0]['value']['product']
    self.os = doc[0]['value']['os']
    self.testtype = doc[0]['value']['testtype']
    self.timestamp = doc[0]['value']['timestamp']
    self.tests = doc[0]['value']['tests']

  def compare(self, doc):
    
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
    x=[]
    
    tests1 = self.tests
    tests2 = doc.tests
    
    for testfile1 in tests1:
      
      if testfile1 not in tests2:
        newtestfiles.append(testfile1)
      else:
        result1 = tests1[testfile1]
        result2 = tests2[testfile1]

        sum1 = result1['fail'] + result1['pass'] + result1['todo']
        sum2 = result2['fail'] + result2['pass'] + result2['todo']
        
        if sum1 == sum2: 
          if result1['fail'] == result2['fail'] and result1['pass'] == result2['pass'] and result1['todo'] == result2['todo']:
            stabletests.append(testfile1)
          else:
            if result1['fail'] > result2['fail']:
              prevlynotfails.append(testfile1)
            if result1['pass'] > result2['pass']:
              prevlynotpasses.append(testfile1)
            if result1['todo'] > result2['todo']:
              prevlynottodos.append(testfile1)
        elif sum1 < sum2:
          if result1['fail'] < result2['fail']:
            missingfails.append(testfile1)
          if result1['pass'] < result2['pass']:
            missingpasses.append(testfile1)
          if result1['todo'] < result2['todo']:
            missingtodos.append(testfile1)
        else:
          if result1['fail'] > result2['fail']:
            newfails.append(testfile1)
          if result1['pass'] > result2['pass']:
            newpasses.append(testfile1)
          if result1['todo'] > result2['todo']:
            newtodos.append(testfile1)

        del tests2[testfile1]
    
    for remainingtestfile in tests2:
      missingtestfiles.append(remainingtestfile)
    
    result = {}
    result['newtestfiles'] = newtestfiles
    result['missingtestfiles'] = missingtestfiles
    result['testing'] = x
    
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
    self.testcount = 0
    self.tests = 0

class TestDelta():
  def __init__(self, name, notes, delta):
    self.name = ''
    self.failnotes = ''
    self.count = 0
  def parsefailnotes(self):
    return False

# class ComparisonResult():
  # def __init__(self):
    # pass
  # def compare(self, build1, build2):
    # tests1 = build1['rows'][0]['value'][]
    # thisbuild = {}
    # thisbuild = build1['rows'][0]['value']
    # return thisbuild
    