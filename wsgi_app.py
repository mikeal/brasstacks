import brasstacks
from brasstacks import sitecompare

application = brasstacks.application
application.add_resource('sitecompare', sitecompare.application)