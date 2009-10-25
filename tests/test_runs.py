import os

try:
    import json
except:
    import simplejson as json

import httplib2

http = httplib2.Http()

this_dir = os.path.abspath(os.path.dirname(__file__))

def test_create_run():
    testrun = json.loads(open(os.path.join(this_dir, 'mozmill-testrun-sample'), 'r').read())
    response, content = http.request('http://localhost:8888/tests', 'POST', 
                                     body=simplejson.dumps(testrun),
                                     headers={'Content-Type': 'application/json'})
    assert response.status == 201
