import os, sys

try:
    import json as simplejson
except:
    import simplejson
from webenv import Response, HtmlResponse
from webenv.rest import RestApplication
from webenv.applications.file_server import FileServerApplication

from brasstacks import lookup
from models import TestRun

this_dir = os.path.abspath(os.path.dirname(__file__))

class TestRuns(RestApplication):
    def __init__(self, debug=True, views=None):
        super(TestRuns, self).__init__()
        self.debug = debug
        self.views = views
        
    def GET(self, request, testType=None, runID=None):
        if testType is None:
            tests_info = self.views.testRuns.allTests()
            return HtmlResponse(
                lookup.get_template('testrun_index.mko').render(
                    tests_info=tests_info, simplejson=simplejson)
                )
    
    def POST(self, request):
        obj = simplejson.loads(str(request.body))
        testrun = TestRun(**obj)
        testrun.save()
        response = Response(testrun._id)
        response.status = '201 Created'
        return response
        

class BrassTacksApplication(RestApplication):
    def __init__(self, debug=True, views=None):
        super(BrassTacksApplication, self).__init__()
        self.debug = debug
        self.views = views
        self.add_resource('tests', TestRuns(debug, views))
        self.add_resource('static', FileServerApplication(os.path.join(this_dir, 'static')))
        
