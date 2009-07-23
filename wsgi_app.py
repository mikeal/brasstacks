import brasstacks
import couchquery
from brasstacks import sitecompare

application = brasstacks.application
site_compare = sitecompare.SiteCompareApplication(couchquery.CouchDatabase("http://localhost:5984/sitecompare"))
application.add_resource('sitecompare', site_compare)
