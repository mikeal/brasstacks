import os
import random
import simplejson as json
import datetime
import couchquery

# data format
# dataStructure = {
  # "buildid": build, 
  # "product": product,
  # "os": opsys,
  # "testtype": testtype,
  # "timestamp": str(date),
  # "tests": [test1, test2, test3, ...]
  # "tinderboxID": tinderbox id
# }

# testStructure = {
  # testname: {
    # "pass": passcount,
    # "fail": failcount,
    # "todo": todocount,
    # "notes": [note1, note2, note3, ...]
# }

def create_db_data(db, **kwargs):
    
    if 'doccount' in kwargs:
        doccount = kwargs['doccount']
    else:
        doccount = random.randint(40, 70)
    
    if 'minnumtests' in kwargs and 'maxnumtests' in kwargs:
        minnumtests = kwargs['minnumtests']
        maxnumtests = kwargs['maxnumtests']
    else:
        minnumtests = 100
        maxnumtests = 500
    
    doctype = 'sample-doc-for-testing-and-dev'
    products = ['Fennec', 'Firefox']
    platforms = ['Maemo-n810', 'WinMo'] #, 'Linux', 'Mac']
    testtypes = ['crashtests', 'mochitests'] #, 'xpcshell', 'reftests']
    
    # create documents
    for i in range(0, doccount):
        
        # create metadata
        buildstructure = {}

        buildstructure['build'] = random.randint(999000, 999999)
        buildstructure['product'] = random.choice(products)
        buildstructure['os'] = random.choice(platforms)
        buildstructure['testtype'] = random.choice(testtypes)
        buildstructure['timestamp'] = str(datetime.datetime.now())
        buildstructure['document'] = doctype
        buildstructure['tinderboxID'] = random.choice([-1, str(datetime.datetime.now())])
        
        # create tests
        tests = {}
        offset = random.randrange(1, 5)
        testcount = random.randint(minnumtests, maxnumtests)
        for x in range(0, testcount):
            failcount = random.randint(0, 10)
            todocount = random.randint(0, 3)
            notes = []
            for y in range(0, (failcount + todocount)):
                notes.append("Message!")
            tests['test_' + str(offset + x) + '.js'] = {
                'pass': random.randint(0, 5),
                'fail': failcount,
                'todo': todocount,
                'note': notes
            }
        buildstructure['tests'] = tests
        db.create(buildstructure)
        
def create_doc(db, **kwargs):
    # create metadata
    buildstructure = {}
    buildstructure['document'] = 'sample-doc-for-testing-and-dev'
    
    if 'build' in kwargs:
        buildstructure['build'] = kwargs['build']
    else:
        buildstructure['build'] = 123456
    
    if 'product' in kwargs:
        buildstructure['product'] = kwargs['product']
    else:
        buildstructure['product'] = 'MyProduct'
    
    if 'os' in kwargs:
        buildstructure['os'] = kwargs['os']
    else:
        buildstructure['os'] = 'MyOS'
    
    if 'testtype' in kwargs:
        buildstructure['testtype'] = kwargs['testtype']
    else:
        buildstructure['testtype'] = 'MyTesttype'
    
    if 'tinderboxID' in kwargs:
        buildstructure['tinderboxID'] = kwargs['tinderboxID']
    else:
        buildstructure['tinderboxID'] = str(datetime.datetime.now())
    
    if 'tests' in kwargs:
        buildstructure['tests'] = kwargs['tests']
    else:
        # create one test file
        tests = {}
        failcount = random.randint(0, 10)
        todocount = random.randint(0, 3)
        notes = []
        for i in range(0, (failcount + todocount)):
            notes.append("Message!")
        tests['sample_test.js'] = { 'pass': random.randint(0, 5), 'fail': failcount, 'todo': todocount, 'note': notes }
        buildstructure['tests'] = tests
    
    buildstructure['timestamp'] = str(datetime.datetime.now())
    
    db.create(buildstructure)
    
def main():
  
  document = 'sample_doc_for_testing_and_dev'
  products = ['Fennec', 'Firefox']
  platforms = ['Maemo-n810', 'WinMo'] #, 'Linux', 'Mac']
  testtypes = ['crashtests', 'mochitests'] #, 'xpcshell', 'reftests']
  build = timestamp = ''
  
  # db = couchquery.Database("http://pythonesque.org:5984/logcompare", cache=Cache())
  db = couchquery.Database("http://happyhans:happyhanshappyhans@happyhans.couch.io/logcompare", cache=Cache())
  # create documents
  doccount = random.randint(40, 70)
  for i in range(0, doccount):
    
    # create metadata
    buildstructure = {}

    buildstructure['build'] = random.randint(999000, 999999)
    buildstructure['product'] = random.choice(products)
    buildstructure['os'] = random.choice(platforms)
    buildstructure['testtype'] = random.choice(testtypes)
    buildstructure['timestamp'] = str(datetime.datetime.now())
    buildstructure['document'] = document
    buildstructure['tinderboxID'] = random.choice([-1, str(datetime.datetime.now())])
    
    # create tests
    tests = {}
    offset = random.randrange(1, 5)
    testcount = random.randint(100, 500)
    for x in range(0, testcount):
      failcount = random.randint(0, 10)
      todocount = random.randint(0, 3)
      notes = []
      for y in range(0, (failcount + todocount)):
        # notes.append("This test should have returned TRUE but returned FALSE")
        notes.append("Message!")
      tests['test_' + str(offset + x) + '.js'] = {
        'pass': random.randint(0, 5),
        'fail': failcount,
        'todo': todocount,
        'note': notes
      }
    print json.dumps(buildstructure, indent=2)
    buildstructure['tests'] = tests
  
    # outputFile = "C:/_Code/python/outputdata" + str(i) + ".html"
    # outFile = open(outputFile, 'w')
    # outFile.write(json.dumps(buildstructure, indent=2))
    # outFile.close()  
    
    db.create(buildstructure)
  
  print "done uploading results"

class Cache(dict):
    def __init__(self, *args, **kwargs):
        super(Cache, self).__init__(*args, **kwargs)
        setattr(self, 'del', lambda *args, **kwargs: dict.__delitem__(*args, **kwargs) )
    get = lambda *args, **kwargs: dict.__getitem__(*args, **kwargs)
    set = lambda *args, **kwargs: dict.__setitem__(*args, **kwargs)
    
if __name__ == "__main__":
  result = main()