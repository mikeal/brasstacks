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
      
    if collection == "builds":
      if resource is None:
          # List of last 100 builds by timestamp
          pass
      else:
          # Test info for specific build
          build = self.db.views.results.allData(key = resource)
          # build = resource
          return MakoResponse("builds", build = build)

    if collection == "compare":
      if resource is None:
        products = set(self.db.views.metadata.products(reduce=False).rows.keys())
        return MakoResponse("products", products=products)
      else:
        tests = self.db.views.fennecBrasstacks.testsByProduct(key=resource).rows
        return MakoResponse("product", tests=tests)
    
    # if collection == "products":
      # if resource is None:
        # products = set(self.db.views.metadata.products(reduce=False).rows.keys())
        # return MakoResponse("products", products=products)
      # else:
        # tests = self.db.views.fennecBrasstacks.testsByProduct(key=resource).rows
        # return MakoResponse("product", tests=tests)
    
    # if collection == "testtypes":
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
        id2 = request.body['buildid2'] # if either is blank, code breaks
        
        doc1 = self.db.views.results.allData(key = id1) 
        doc2 = self.db.views.results.allData(key = id2)
        
        similardocs = self.db.views.metadata.metadataAsKeys(key = [product, os, testtype], limit = 10)
        
        # if doc1['rows'] != [] and doc2['rows'] != []:
          # build1 = Build(doc1)
          # build2 = Build(doc2)
          # if build1.newer(build2):
            # build1.compare(build2)
          # else:
            # build2.compare(build1)
          # # compare which one is newer build1.newer(build2)
          # answer = build1.compare(build2)
          # # answer = 'both'
        # elif doc1['rows'] != [] or doc2['rows'] != []:
          # if doc1['rows'] != []:
            # # answer = ComparisonResult(build1, findPrevious(build1))
            # answer = 'doc1'
          # else:
            # # answer = ComparisonResult(build2, findPrevious(build2))
            # answer = 'doc2'
        # else:
            # answer = 'None'
        
        return MakoResponse("compare", doc1 = self.findPrevious(doc1))
  
  def findPrevious(self, doc):
    product = doc['rows'][0]['value']['product']
    os = doc['rows'][0]['value']['os']
    testtype = doc['rows'][0]['value']['testtype']
    similardocs = self.db.views.metadata.metadataAsKeys(limit = 10) # key = [product, os, testtype]
    return similardocs
        
class Build():
  def __init__(self, doc):
    self.doc = doc['rows'][0]['value'];
    self.docId = doc['rows'][0]['value']['_id']
    self.buildId = doc['rows'][0]['value']['build']
    self.product = doc['rows'][0]['value']['product']
    self.os = doc['rows'][0]['value']['os']
    self.testtype = doc['rows'][0]['value']['testtype']
    self.timestamp = doc['rows'][0]['value']['timestamp']
    self.tests = doc['rows'][0]['value']['tests']
    # compareToPrevious(doc)

  def compare(self, doc = None):
    
    if doc is None:
      #compare to previous
      #thatbuild = Build(findPrevious(self.doc))
      pass
    else:
      #compare to doc
      thatbuild = Build(doc)
      pass
    
    # newtests = {}
    
    # for testfile1 in tests1:
      
      # testfile2 = tests2.find(testfile1)
      
      # if testfile2 is None:
        # newtests.add(testfile1)
      
      # else:
        # if sumoftests(testfile1) == sumoftests(testfile2):
          # if testfile1.morefail(testfile2):
            # prevlynotfails.add(testfile1)
          # elif testfile1.morepass(testfile2):
            # prevlynotpasses.add(testfile1)
          # elif testfile1.moretodo(testfile2):
            # prevlynottodos.add(testfile1)
          # else:
            # stabletests.add(testfile1)
        
        # elif (sumoftests(testfile1) < sumoftests(testfile2)):
          
        # else:
    
    # for remainingtest in tests2:
      # missingtests.add(remainingtest)
  
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

  def previous(self, doc):
    return False

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
    