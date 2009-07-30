import os
try:
    import json as simplejson
except ImportError:
    import simplejson
    
from markdown import markdown

from webenv import HtmlResponse
from mako.template import Template
from webenv.rest import RestApplication

template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fennec_templates')
design_doc = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fennec_views')

def findPrevious(build):
  return build

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
            products = self.db.views.metadata.products(reduce = True, group = True)
            testtypes = self.db.views.metadata.testtypes(reduce = True, group = True)
            oses = self.db.views.metadata.operatingSystems(reduce = True, group = True)
            metadata = self.db.views.metadata.displayMetadata(reduce = True)
            summary = self.db.views.results.summary(reduce = True, group = True)
            all = self.db.views.results.allData(key = 'sampletest')
            return MakoResponse("index", 
              products = products, 
              metadata = metadata, 
              testtypes = testtypes, 
              oses = oses, 
              summary = summary, 
              all = all)
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
          
          buildid1 = request.body['buildid1']
          buildid2 = request.body['buildid2']
          
          build1 = Build(self.db.views.results.allData(key = buildid1))
          build2 = Build(self.db.views.results.allData(key = buildid2))
          
          if build1['rows'] != [] and build2['rows'] != []:
            answer = build1.compare(build2)
            # answer = 'both'
          elif build1['rows'] != [] or build2['rows'] != []:
            if build1['rows'] != []:
              # answer = ComparisonResult(build1, findPrevious(build1))
              answer = 'doc1'
            else:
              # answer = ComparisonResult(build2, findPrevious(build2))
              answer = 'doc2'
          else:
              answer = 'None'
          
          return MakoResponse("compare", doc1 = answer, doc2 = build2)

class Build():
  def __init__(self, doc):
    self.doc = doc['rows'][0]['value'];
    self.docId = doc['rows'][0]['value']['_id']
    self.buildId = doc['rows'][0]['value']['build']
    self.product = doc['rows'][0]['value']['product']
    self.os = doc['rows'][0]['value']['os']
    self.testtype = doc['rows'][0]['value']['testtype']
    self.tests = doc['rows'][0]['value']['tests']
    # compareToPrevious(doc)

  def compare(doc = None):
    
    if doc is None:
      #compare to previous
      thatbuild = Build(findPrevious(self.doc))
      pass
    else:
      #compare to doc
      thatbuild = Build(doc)
      pass
    
    newtests = []
      for testfile1 in tests1:
        testfile2 = tests2.find(testfile1)
        if testfile2 is None:
          newtests.add(testfile1)
        else:
          if (sumoftests(testfile1) == sumoftests(testfile2)):
            
          elif (sumoftests(testfile1) < sumoftests(testfile2)):
            
          else:
            
# class ComparisonResult():
  # def __init__(self):
    # pass
  # def compare(self, build1, build2):
    # tests1 = build1['rows'][0]['value'][]
    # thisbuild = {}
    # thisbuild = build1['rows'][0]['value']
    # return thisbuild
    