import unittest
from couchquery import Database
from logcompare import LogCompareApplication

db = Database("http://pythonesque.org:5984/fennec_test")
logcompare_application = LogCompareApplication(db)

class TestViews(unittest.TestCase):
  def setUp(self):
    print "setup"
    
  def test_productCounts(self):
    products = db.views.fennecResults.productCounts(reduce = True, group = True).items()
    self.assertTrue(len(products) > 0)

class TestPages(unittest.TestCase):
  def setUp(self):
    print "setup again"
    
  def test_index(self):
    self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
