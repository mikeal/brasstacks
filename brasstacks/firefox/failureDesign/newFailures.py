import zlib

@map_function
def new_failure(doc):
    if 'type' in doc and doc['type'] == 'failure-info':
        for testname in doc['fails']:
            test = doc['fails'][testname]
            if test['firstfailed']['_id'] == doc['run']['_id']:
                emit(doc['run']['timestamp'], {'run':doc['run'],'testname':testname,'testinfo':test})
start = """
<html>
    <title>New Test Failures</title>
    <body>
        <style type="text/css">
        body {
          color:#222222;
          font-family:"Sabon LT Std","Hoefler Text","Palatino Linotype","Book Antiqua",serif;
          font-size:18px;
        }
        </style>

        <div class="header">
            New Failures
        </div>
        
        <style type="text/css">
        .testtype {
          color:#0000FF;
        }
        .passed {
          color:#00FF00;
        }
        .failed {
          color:#FF0000;
        }
        .run-info {
          text-align:center;
        }
        h2 {
          text-align:center;
        }
        td {
          text-align:center;
        }
        </style>


"""

day_head = """
<div>{{day}}</div>
<table class="tablesorter">
  <thead>
    <tr>
      <th>testtype</th>
      <th>name</th>
      <th>product</th>
      <th>os</th>
      <th>time</th>
      <th>build</th>
      <th>last success</th>
    <tr>
  </thead>
  <tbody>
"""

table_row = u"""
<tr>
  <td>{{testtype}}</td>
  <td><a href="/firefox/testInfo/{{testhash}}">{{testname}}</a></td>
  <td>{{product}}</td>
  <td>{{os}}</td>
  <td>{{timestamp}}</td>
  <td><a href="/firefox/testrunInfo/{{run_id}}">{{build}}</a></td>
  <td>{{lastsuccess}}</td>
<tr>
"""

footer = """
<div>Latest <a href="?descending=true&limit=50">50</a>   <a href="?descending=true&limit=100">100</a>   <a href="?descending=true&limit=250">250</a>   <a href="?descending=true&limit=500">500</a>   <a href="?descending=true&limit=1000">1000</a></div>
"""


import pystache

class NewFailures(ListView):
    def start(self, head, request):
        self.days = []
        return [start], {'headers':{'content-type':'text/html'}}
    def list_row(self, row):
        t = []
        day = row['value']['run']['timestamp'].split(' ')[0]
        if day not in self.days:
            if len(self.days) is not 0:
                t.append("</tbody></table>")
            t.append(pystache.render(day_head,{'day':day}))
            self.days.append(day)
        test = row['value']
        r = { 'testtype':   test['run']['testtype'],
              'testhash':   str(zlib.crc32(test['testname'])),
              'testname':   test['testname'],
              'os':         test['run']['os'],
              'timestamp':  test['run']['timestamp'].split('.')[0],
              'run_id':     test['run']['_id'],
              'build':      test['run']['build'],
              'lastsuccess': test['testinfo']['lastsuccess'] or 'never',
              'product':    test['run']['product'],
             }
        
        s = pystache.render(table_row,r)
        t.append(s)
        return t
    def list_end(self):
        return ['</tbody></table>', footer, '</body></html>']

