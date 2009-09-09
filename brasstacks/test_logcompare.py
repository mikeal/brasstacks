# http://docs.python.org/library/unittest.html
import unittest
import couchquery
from couchquery import Database
from couchquery import Httplib2Client
import logcompare
from logcompare import LogCompareApplication
from logcompare import Then
from logcompare import mockdata

db = Database("http://pythonesque.org:5984/logcompare")
logcompare_application = LogCompareApplication(db)

# setting up database
# testdb_url = "http://happyhans:happyhanshappyhans@happyhans.couch.io/test-logcompare"
# couchquery.createdb(testdb_url)
# testdb = Database(testdb_url)
# testdb.sync_design_doc("logcompare", logcompare.design_doc)
# print testdb.views.logcompare.runCounts(reduce = True, group = True).items()

# deleting database
# couchquery.deletedb(testdb_url)

testdb_url = "http://happyhans:happyhanshappyhans@happyhans.couch.io/test-logcompare"
# testdb = Database(testdb_url)
# print testdb
# couchquery.createdb(testdb_url)





    
class TestViews(unittest.TestCase):
    def setUp(self):
        couchquery.createdb(testdb_url)
        self.testdb = Database(testdb_url)
        self.testdb.sync_design_doc("logcompare", logcompare.design_doc)

    def tearDown(self): 
        couchquery.deletedb(testdb_url)
        
    def test_runCounts(self):
        
        product = 'Fennec'
        os = 'Maemo'
        testtype = 'crashtests'
        count = 3
        
        # create documents where for a specific number of them the product, os, and testype are specified
        for i in range(0, count):
            mockdata.create_doc(self.testdb, product=product, os=os, testtype=testtype)
        for i in range(0, 10):
            mockdata.create_doc(self.testdb)
            
        counts = self.testdb.views.logcompare.runCounts(reduce = True, group = True).items()
        for key, value in counts:
            if key == [product, os, testtype]:
                self.failUnlessEqual(value, count, "Value should be equal to the count for a combination of product, os, testtype")

class TestWebPages(unittest.TestCase):
  def setUp(self):
    print "setup again"
    
  def test_index(self):
    self.assertTrue(True)

class TestAssertions(unittest.TestCase):
    def setUp(self):
        print "setup"
    
    def test_index(self):
        self.assertTrue(True)
    
    def tearDown(self):
        print "tear down"

if __name__ == '__main__':
    unittest.main()


