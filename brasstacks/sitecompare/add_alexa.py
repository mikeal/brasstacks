import os, sys

import httplib2
import simplejson
from brasstacks import sitecompare

this_dir = os.path.abspath(os.path.dirname(__file__))
alexa_file = os.path.join(this_dir, 'alexa.csv')

http = httplib2.Http()

def add_alexa(couch_url):

    for site in (x.replace(' ','').split(',')[-1] for x in open(alexa_file).read().splitlines() if not x.startswith('#')):
        resp, content = http.request("http://brasstacks.mozilla.com/sitecompare/pages", "POST", body=simplejson.dumps({"uri":"http://"+site}), headers={"CONTENT-TYPE":"application/json"})
        print resp.status, content

if __name__ == '__main__':
    add_alexa(sys.argv[-1])