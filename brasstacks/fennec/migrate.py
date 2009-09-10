import httplib2
import couchquery
import json
from threading import Thread
from wsgiref.simple_server import make_server
from time import sleep
from brasstacks import Stub

http = httplib2.Http()

def setup():
    from brasstacks import fennec
    olddb = couchquery.Database('http://localhost:5984/fennec_old')
    db = couchquery.Database('http://localhost:5984/fennec')
    db.sync_design_doc('fennec', fennec.design_doc)
    db.sync_design_doc('fennecFailures', fennec.failures_design_doc)
    a = Stub()
    a.add_resource('fennec', fennec.FennecApplication(db))
    global thread
    global httpd
    httpd = make_server('', 8888, a)
    thread = Thread(target=httpd.serve_forever)
    thread.start()
    sleep(1)
    return olddb, db

def migrate_doc(doc):
    print doc._id
    doc.pop('_id')
    doc.pop('_rev')
    resp, content = http.request('http://localhost:8888/fennec/api/testrun', method='POST', body=json.dumps(doc))
    print content

def migrate(db):
    for doc in db.views.all():
        if 'testtype' in doc:
            migrate_doc(doc)

if __name__ == "__main__":
    old, new = setup()
    migrate(old)
    while thread.isAlive():
        httpd.shutdown()
