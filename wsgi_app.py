import brasstacks
import couchquery
from brasstacks import sitecompare
from brasstacks import users
application = brasstacks.application
site_compare = sitecompare.SiteCompareApplication(couchquery.CouchDatabase("http://localhost:5984/sitecompare"))
application.add_resource('sitecompare', site_compare)
users_application = users.UsersApplication(db)
application.add_resource('users', users_application)
