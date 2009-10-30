import os
from datetime import datetime
from urllib import urlencode

from webenv import HtmlResponse, Response303, Response
from webenv.rest import RestApplication
from mako.lookup import TemplateLookup
try:
    import json
except:
    import simplejson as json

this_directory = os.path.abspath(os.path.dirname(__file__))
crashes_design_doc = os.path.join(this_directory, 'crashViews')
jobs_design_doc = os.path.join(this_directory, 'jobViews')
results_design_doc = os.path.join(this_directory, 'resultViews')

lookup = TemplateLookup(directories=[os.path.join(this_directory, 'templates')], encoding_errors='ignore', input_encoding='utf-8', output_encoding='utf-8')

class MakoResponse(HtmlResponse):
    def __init__(self, name, **kwargs):
        template = lookup.get_template(name+'.mko')
        kwargs['json'] = json
        self.body = template.render_unicode(**kwargs).encode('utf-8', 'replace')
        self.headers = []
        
class JSONResponse(Response):
    content_type = 'application/json'
    def __init__(self, obj):
        self.body = json.dumps(obj)
        self.headers = []

class CrashTestAPIApplication(RestApplication):
    def __init__(self, crashdb, resultdb):
        super(CrashTestAPIApplication, self).__init__()
        self.crashdb = crashdb
        self.resultdb = resultdb
        
    def POST(self, request, method):
        if method == "getJob":
            info = json.loads(str(request.body))
            rows = self.resultdb.views.jobs.byOsStarttime(startkey=[info['os'],{}], descending=True,
                                                          endkey=[info['os'], None], limit=1)
            if len(rows) is not 0:
                latest = rows[0]
                startkey = latest.urls[-1]
            else:
                startkey = None
            rows = self.crashdb.views.crashes.url(limit=4000, startkey=startkey, group=True, stale="ok")
            info['urls'] = rows.keys()
            info['startkey'] = startkey
            info['buildinfo'] = {"branch":"1.9.1", "debug":True}
            info['status'] = "running"
            info['type'] = "job"
            info['starttime'] = datetime.now().isoformat()
            
            docinfo = self.resultdb.create(info)
            job = self.resultdb.get(docinfo['id'])
            return JSONResponse(job)
        if method == "result":
            job = json.loads(str(request.body))
            assert 'results' in job
            assert job['status'] == 'done'
            job['endtime'] = datetime.now().isoformat()
            info = self.resultdb.update(job)
            self.resultdb.views.results.byUrl(limit=0)
            return JSONResponse(info)

class CrashTestApplication(RestApplication):
    def __init__(self, crashdb, resultdb):
        super(CrashTestApplication, self).__init__()
        self.crashdb = crashdb
        self.resultdb = resultdb
        self.add_resource('api', CrashTestAPIApplication(crashdb, resultdb))
        
    def GET(self, request, collection=None, resource=None):
        if collection is None:
            limit = request.query.get('limit', 100)
            crashes = self.crashdb.views.crashes.url(limit=limit, group=True, stale="ok")
            jobs = self.resultdb.views.jobs.byStarttime(limit=10, descending=True, stale="ok")
            return MakoResponse('index', crashes=crashes, jobs=jobs, urlencode=urlencode)
        if collection == 'url':
            if resource is not None:
                if resource == 'nourl':
                    resource = ''
                crashes = self.crashdb.views.crashes.crashByUrl(key=resource, stale="ok")
                return MakoResponse('url', url=resource, crashes=crashes.values())
        if collection == 'crash':
            if resource is None:
                # crashes index
                pass
            else:
                return MakoResponse('crash', crash=self.crashdb.get(resource))
        if collection == 'job':
            if resource is None:
                # jobs index
                pass
            else:
                return MakoResponse('job', job=self.resultdb.get(resource))
            
