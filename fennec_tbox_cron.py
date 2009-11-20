try:
    import json
except:
    import simplejson as json
import urllib
import re
import datetime
from couchquery import Database
from couchquery import CouchDBException
import httplib2
import log_parser

http = httplib2.Http()
tbox_url = 'http://tinderbox.mozilla.org/showbuilds.cgi?tree=Mobile&json=1&noignore=1'

def save(data):    
    saved = False
    starttime = datetime.datetime.now()
    resp, content = http.request('http://localhost/fennec/api/testrun', method='POST',
                                 body=json.dumps(data), headers={'content-type':'application/json'})
    print content
    finishtime = datetime.datetime.now()
    print finishtime - starttime
    saved = True
    return saved

def getTinderboxData():
    jsonurl = urllib.urlopen(tbox_url)

    #Hack to remove the 'tinderbox_data =' from the front
    data = jsonurl.read().split("=", 1)
    jsonurl.close()

    #Hack to replace the " in the json with ', and replace the original ' with "
    data = data[1].strip("\n; ").replace("\"", "\\\"").replace("'", "\"").replace("\\\"", "'")
    result = json.loads(data)
    if 'Error' in result:
        return "Error found in result"
    return result

def parseFile(tbox_id):
    result = log_parser.LogParser().parseLog(tbox_id)
    if (result != None):
        print "saving: " + tbox_id
        save(result)


def main():
    db = Database('http://localhost:5984/fennec_results')
    data = getTinderboxData()
    testName = re.compile('((reftest)|(crashtests)|(xpcshell))')

    build_table = data['build_table']
    build = build_table[0]

    for build in build_table:
        for b in [b for b in build if type(b) is not int]:
            for k in b:
                if (k == "buildname" and testName.search(b[k])):
                    print "checking out buildname: " + b[k]
                    tbox_id = b['logfile']
                    if len(db.views.fennec.byTinderboxID(key=tbox_id)) is 0:
                        parseFile(tbox_id)
                    else:
                        print 'skipping '+tbox_id

class Cache(dict):
    def __init__(self, *args, **kwargs):
        super(Cache, self).__init__(*args, **kwargs)
        setattr(self, 'del', lambda *args, **kwargs: dict.__delitem__(*args, **kwargs) )
    get = lambda *args, **kwargs: dict.__getitem__(*args, **kwargs)
    set = lambda *args, **kwargs: dict.__setitem__(*args, **kwargs)
      
if __name__ == "__main__":
  result = main()

