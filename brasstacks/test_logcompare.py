import unittest
import couchquery
from couchquery import Database
from logcompare import LogCompareApplication
from logcompare import Then

db = Database("http://pythonesque.org:5984/logcompare")
logcompare_application = LogCompareApplication(db)

testdb_url = "http://happyhans:happyhanshappyhans@happyhans.couch.io/test-logcompare"

couchquery.createdb(testdb_url)
testdb = Database(testdb_url)
testdb.sync_design_doc("logcompare", logcompare.design_doc)
print testdb.views.logcompare.runCounts(reduce = True, group = True).items()

couchquery.deletedb(testdb_url)

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
  
class TestViews(unittest.TestCase):
  def setUp(self):
    print "setup"
    
  def test_productCounts(self):
    runs = db.views.logcompare.runCounts(reduce = True, group = True).items()
    print runs
    print Then("2009-07-17 21:01:24.431250").approximately
    self.assertTrue(len(runs) > 0)

class TestWebPages(unittest.TestCase):
  def setUp(self):
    print "setup again"
    
  def test_index(self):
    self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
    
class TestParser(unittest.TestCase):
  def setUp(self):
    print "setup again"
    
  def test_index(self):
    self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
