import json
import uuid

@update_function
def new_report(doc, req):
    doc = json.loads(req['body'])
    doc['_id'] = str(uuid.uuid1()).replace('-','')
    return doc, doc['_id']

@show_function
def show_report(doc, req):
    html = '<html><head><title>Change Me</title></head><body>Change Me!</body></html>'
    return {'body':html, 'headers':{'content-type':'text/html'}}