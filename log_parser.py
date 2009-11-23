import urllib
import re
import datetime
import sys
import copy

class LogParser():

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

    reReftest = ''
    reCrashtest = ''
    reXpcshell = ''
    reParsing = ''
    logroot = ''

    def __init__(self, product="mobile"):
        if (product == "mobile"):
            self.reReftest = re.compile('.*testtype=reftest.*')
            self.reCrashtest = re.compile('.*testtype=crashtest.*')
            self.reXpcshell = re.compile('.*testtype=xpcshell.*')
            self.reParsing = re.compile(r'python maemkit-chunked.py')
            self.logroot = "http://tinderbox.mozilla.org/showlog.cgi?log=Mobile/"
        else:
            self.reReftest = re.compile('.*=symbols reftest/tests/layout/reftests/reftest.list.*')
            self.reCrashtest = re.compile('.*=symbols reftest/tests/testing/crashtest/crashtests.list.*')
            self.reXpcshell = re.compile('.*manifest=xpcshell/tests/all-test-dirs.list.*')
            self.reParsing = re.compile(r'python|bash')
            self.logroot = "http://tinderbox.mozilla.org/showlog.cgi?log=Firefox-Unittest/"

    def _getBuild(self, text):
        label = r'tinderbox: build: '
        regex = re.compile(label + r'.*')
        result = regex.search(text)
        if result != None:
            return (result.group(0))[len(label):len(result.group(0))]
        else:
            return 'no-info'
  
    # bug: BUILDID appears twice with different values in the log
    def getBuildId(self, text):
        label = r'BuildID='
        regex = re.compile(label + r'.*')
        result = regex.search(text)
        if result != None:
            return (result.group(0))[len(label):len(result.group(0))]
        else:
            return 'no-info'

    def getProduct(self, text):
        label = r'Name='
        regex = re.compile(label + r'.*')
        result = regex.search(text)
        if result != None:
            return (result.group(0))[len(label):len(result.group(0))]
        else:
            return 'no-info'

    def getOs(self, text):
        return (re.split(' +', self._getBuild(text)))[0]

    def getTestType(self, text):
        if (self.reReftest.search(text)):
            return "reftest"
        elif (self.reCrashtest.search(text)):
            return "crashtest"
        elif (self.reXpcshell.search(text)):
            return "xpcshell"
        return None

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
    def getTestDetail(self, text):

        line = text.split('|')
        match = self.reStatus.search(line[0])
        if (match):
            outcome = match.group(0)
            if (outcome.split(' ')[0] == "REFTEST"):
                outcome = outcome.split(' ')[1]
        else:
            return

        pathname = line[1].strip()
        pieces = pathname.replace('\\', '/').split('/')
        if 'reftest' in pieces:
            index = pieces.index('reftest') + 1
            name = "/".join(pieces[index:])
        elif 'xpcshell' in pieces:
            index = pieces.index('xpcshell') + 1
            name = "/".join(pieces[index:])
        else:
            name = pathname

        if ((name.strip() != "") and (name not in self.tests)):
            self.tests[name] = dict({'pass': 0, 'fail': 0, 'todo': 0, 'note': []})

        if outcome == 'TEST-PASS':
            self.tests[name]['pass'] += 1

        elif outcome == 'TEST-KNOWN-FAIL':
            self.tests[name]['todo'] += 1
        else:
            self.tests[name]['fail'] +=  1

    def parseLog(self, tbox_id):

        retVal = []
        doc = {}
        contentAll = ''
        url = self.logroot + tbox_id + "&fulltext=1"
        try:
            inFile = urllib.urlopen(url)
        except IOError:
            print "Can't open " + url
        else:
            contentAll = inFile.read()
            inFile.close()

        doc = {
            "build": self.getBuildId(contentAll),
            "product": self.getProduct(contentAll),
            "os": self.getOs(contentAll),
            "testtype": self.getTestType(contentAll),
            "tinderboxID": tbox_id}

        self.reStatus = ''

        buildSteps = contentAll.split("BuildStep ended")
        for step in buildSteps:
            if self.reParsing.search(step):
                doc = copy.copy(doc)
                doc["testtype"] = self.getTestType(step)
                if (doc["testtype"] <> None):
                    if (doc["testtype"] == "reftest" or doc["testtype"] == "crashtest"):
                        self.reStatus = self.reftestHarness
                    elif (doc["testtype"] == "xpcshell"):
                        self.reStatus = self.xpcshellHarness

                    if (self.reStatus <> ''):
                        retVal.append(self.parseBuildStep(doc, step))
        
        return retVal

    def parseBuildStep(self, doc, step):
        mydoc = {}
        mydoc["build"] = doc["build"]
        mydoc["product"] = doc["product"]
        mydoc["os"] = doc["os"]
        mydoc["tinderboxID"] = doc["tinderboxID"]
        mydoc["testtype"] = doc["testtype"]
        self.tests = {}

        contentByLine = step.split("\n")
        for line in contentByLine:
            if self.reStatus.search(line) != None:
                 self.getTestDetail(line)
                 mydoc["tests"] = self.tests
                 mydoc["timestamp"] = str(datetime.datetime.now())

                 #HACK: to only count 1 test/check for each test file
                 if (mydoc["testtype"] == "xpcshell"):
                     for test in mydoc['tests']:
                         if (mydoc['tests'][test]['fail'] >= 1):
                             mydoc['tests'][test] = dict({'pass': 0, 'fail': 1, 'todo': 0, 'note': []})
                         else:
                             mydoc['tests'][test] = dict({'pass': 1, 'fail': 0, 'todo': 0, 'note': []})
        return mydoc

def main():

    if (len(sys.argv) <= 1):
        print "usage: " + sys.argv[0] + " [<product>] <tinderbox_id>"
        print "       <product> = mobile|firefox- mobile is default"
        print "\nexample: " + sys.argv[0] + " mobile 1258685405.1258695209.5922.gz"
        print "\nexample: " + sys.argv[0] + " firefox 1258743503.1258747166.27999.gz"
        return

    product = ''
    tboxid = ''
    if (len(sys.argv) == 2):
        product = "mobile"
        tboxid = sys.argv[1]
    elif(len(sys.argv) == 3):
        product = sys.argv[1]
        tboxid = sys.argv[2]
    else:
        print "invalid # of args"
        return

    result = LogParser(product).parseLog(tboxid)
    print result

if __name__ == "__main__":
  result = main()

