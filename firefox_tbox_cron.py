try:
    import json
except:
    import simplejson as json
import urllib
import types
import re
import datetime
import fnmatch
from couchquery import Database
import httplib2

http = httplib2.Http()

# data format
# dataStructure = {
  # "buildid": build,
  # "product": product,
  # "os": opsys,
  # "testtype": testtype,
  # "timestamp": str(date),
  # "tests": [test1, test2, test3, ...]
# }

# testStructure = {
  # testname: {
    # "pass": passcount,
    # "fail": failcount,
    # "todo": todocount,
    # "note": [note1, note2, note3, ...]
# }

#crashtest- line status: 'REFTEST TEST-*', parsing build step: 'parse crashtest log'
#reftest- line status: 'REFTEST TEST-*', parsing build step: 'parse reftest log'
#xpcshell- line status: 'TEST-*', parsing build step: 'parse xpcshell log'

reftestHarness = re.compile(r'REFTEST TEST-((FAIL)|(PASS)|(UNEXPECTED-FAIL)|(TIMEOUT)|(KNOWN-FAIL)|(UNEXPECTED-PASS))')
xpcshellHarness = re.compile(r'TEST-((FAIL)|(PASS)|(UNEXPECTED-FAIL)|(TIMEOUT)|(KNOWN-FAIL)|(UNEXPECTED-PASS))')
reParsing = re.compile(r'parse ((crashtest)|(reftest)|(xpcshell)) log')
reStatus = ''

tbox_url = 'http://tinderbox.mozilla.org/showbuilds.cgi?tree=Mobile&json=1&noignore=1'
logroot = "http://tinderbox.mozilla.org/showlog.cgi?log=Mobile/"
tbox_ids = []

# global variables
tests = dict()

def _getBuild(text):
    label = r'tinderbox: build: '
    regex = re.compile(label + r'.*')
    result = regex.search(text)
    if result != None:
        return (result.group(0))[len(label):len(result.group(0))]
    else:
        return 'no-info'
  
# bug: BUILDID appears twice with different values in the log
def getBuildId(text):
    label = r'BuildID='
    regex = re.compile(label + r'.*')
    result = regex.search(text)
    if result != None:
        return (result.group(0))[len(label):len(result.group(0))]
    else:
        return 'no-info'

def getProduct(text):
    label = r'Name='
    regex = re.compile(label + r'.*')
    result = regex.search(text)
    if result != None:
        return (result.group(0))[len(label):len(result.group(0))]
    else:
        return 'no-info'

def getOs(text):
    return (re.split(' +', _getBuild(text)))[0]

def getTestType(text):
    splitted = re.split(' +', _getBuild(text))
    return splitted[len(splitted)-1]

# cannot handle blank test file when exception occurred
# some notes appear on the line below:
# TEST-PASS | /media/mmc1/release/xpcshell/tests/test_uriloader_exthandler/unit/test_handlerService.js | [run_test : 147] true == true
# NEXT ERROR TEST-UNEXPECTED-FAIL | /media/mmc1/release/xpcshell/tests/test_uriloader_exthandler/unit/test_handlerService.js | 0 == 3 - See following stac$
# JS frame :: /media/mmc1/release/xpcshell/head.js :: do_throw :: line 181
# JS frame :: /media/mmc1/release/xpcshell/head.js :: do_check_eq :: line 211
# JS frame :: /media/mmc1/release/xpcshell/tests/test_uriloader_exthandler/unit/test_handlerService.js :: run_test :: line 154
# JS frame :: /media/mmc1/release/xpcshell/head.js :: _execute_test :: line 125
# JS frame :: -e :: <TOP_LEVEL> :: line 1
# TEST-INFO | (xpcshell/head.js) | exiting test
  # <<<<<<<
# TEST-PASS | /media/mmc1/release/xpcshell/tests/test_uriloader_exthandler/unit/test_punycodeURIs.js | test passed
def getTestDetail(text):
    global reStatus

    line = text.split('|')
    match = reStatus.search(line[0])
    if (match):
        outcome = match.group(0)
    else:
        return

    pathname = line[1].strip()
    pieces = pathname.split('/')
    if 'reftest' in pieces:
        index = pieces.index('reftest') + 1
        name = "/".join(pieces[index:])
    elif 'xpcshell' in pieces:
        index = pieces.index('xpcshell') + 1
        name = "/".join(pieces[index:])
    else:
        name = pathname
    p = f = t = 0

    #TODO: make this either 'REFTEST TEST-PASS' or 'TEST-PASS'
#    if outcome == 'REFTEST TEST-PASS':
    if outcome == 'REFTEST TEST-PASS':
        p = 1
        if name not in tests:
            tests[name] = dict({'pass': p, 'fail': f, 'todo': t, 'note': []})
        else:
            tests[name]['pass'] = tests[name]['pass'] + p

    #TODO: make this either 'REFTEST TEST-KNOWN-FAIL' or 'TEST-KNOWN-FAIL'
    elif outcome == 'REFTEST TEST-KNOWN-FAIL':
        t = 1
        if name not in tests:
            tests[name] = dict({'pass': p, 'fail': f, 'todo': t, 'note': []})
        else:
            tests[name]['todo'] = tests[name]['todo'] + t
    else:
        f = 1
        if name.strip() != "":
            if name not in tests:
                tests[name] = dict({'pass': p, 'fail': f, 'todo': t, 'note': []})
            else:
                tests[name]['fail'] = tests[name]['fail'] + f

def parseLog(tbox_id):
    global reStatus, reftestHarness, xpcshellHarness

    doc = {}
    contentAll = ''
    url = logroot + tbox_id + "&fulltext=1"
    try:
        inFile = urllib.urlopen(url)
    except IOError:
        print "Can't open " + url
    else:
        contentAll = inFile.read()
        inFile.close()

    if reParsing.search(contentAll) != None:
        tests.clear()

    doc = {
        "build": getBuildId(contentAll),
        "product": getProduct(contentAll),
        "os": getOs(contentAll),
        "testtype": getTestType(contentAll),
        "tinderboxID": tbox_id}

    reStatus = ''
    if (doc["testtype"] == "reftest" or doc["testtype"] == "crashtests"):
        reStatus = reftestHarness
    elif (doc["testtype"] == "xpcshell"):
        reStatus = xpcshellHarness

    if (reStatus == ''):
        return
    
    buildSteps = contentAll.split("BuildStep ended")
    for step in buildSteps:
        if reParsing.search(step):
            contentByLine = step.split("\n")
            for line in contentByLine:
                if reStatus.search(line) != None:
                    getTestDetail(line)
            break

    doc['tests'] = tests
    doc['timestamp'] = str(datetime.datetime.now())
  
    print "Done parsing " + url
    return doc
  
def save(data):    
    saved = False
    starttime = datetime.datetime.now()
    resp, content = http.request('http://localhost/firefox/api/testrun', method='POST',
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
    result = parseLog(tbox_id)
    if (result != None):
        print "saving: " + tbox_id
        save(result)


def main():
    db = Database('http://localhost:5984/firefox')
    
    data = getTinderboxData()
#HACK: Temporarily removing xpcshell until tinderbox has this fixed
#    testName = re.compile('((reftest)|(crashtests)|(xpcshell))')
    testName = re.compile('((reftest)|(crashtests))')

    build_table = data['build_table']
    build = build_table[0]

    for build in build_table:
        for b in [b for b in build if type(b) is not int]:
            for k in b:
                if (k == "buildname" and testName.search(b[k])):
                    print "checking out buildname: " + b[k]
                    tbox_id = b['logfile']
                    if len(db.views.results.byTinderboxID(key=tbox_id)) is 0:
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

