from brasstacks import sitecompare
application = sitecompare.application
from webenv.rest import RestApplication

if __name__ == "__main__":
    class Stub(RestApplication):
        def GET(self, request, *args):
            return webenv.HtmlResponse('<html><head><title>Nope.</title></head><body>Nope.</body></html>')
    a = Stub()
    a.add_resource('sitecompare', application)
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8888, a)
    print "Serving on http://localhost:8888/sitecompare"
    httpd.serve_forever()