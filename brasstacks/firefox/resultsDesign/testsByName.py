import zlib

@map_function
def timestamp_result(doc):
    if 'type' in doc and doc['type'] == 'test-run':
        for test in doc['tests']:
            t = zlib.crc32(test['name'])
            emit([t, doc['timestamp']], [doc['_id'], test['result'], doc['os'], doc['build'], test['name']])

start = """
<html>
    <title>Test Info {{testname}}</title>
    <body>
        <style type="text/css">
        body {
          color:#222222;
          font-family:"Sabon LT Std","Hoefler Text","Palatino Linotype","Book Antiqua",serif;
          font-size:18px;
        }
        </style>

        <div class="header">
            Test Info {{testname}}
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


<div>Test History</div>
<table class="tablesorter">
  <thead>
    <tr>
      <th>timestamp</th>
      <th>result</th>
      <th>os</th>
      <th>build</th>
    <tr>
  </thead>
  <tbody>
"""

table_row = u"""
<tr>
  <td>{{timestamp}}</td>
  <td>{{result}}</td>
  <td>{{os}}</td>
  <td><a href="/firefox/testrunInfo/{{run_id}}">{{build}}</a></td>
<tr>
"""

footer = """
<div>Latest <a href="?limit=50">50</a>   <a href="?limit=100">100</a>   <a href="?limit=250">250</a>   <a href="?limit=500">500</a>   <a href="?limit=1000">1000</a></div>
"""

import pystache

class TestnameList(ListView):
    pass_map = {True:'pass',False:'failed'}
    def start(self, head, req):
        self.i = 0
        return [''], {'headers':{'content-type':'text/html'}}
    def list_row(self, row):
        r = []
        if self.i is 0:
            r.append(pystache.render(start, {'testname':row['value'][4]}))
        x = {'timestamp':row['key'][1],
             'result'   :self.pass_map[row['value'][1]],
             'os'       :row['value'][2],
             'run_id'   :row['value'][0],
             'build'    :row['value'][3],
             }
        r.append(pystache.render(table_row, x))
        self.i += 1
        return r
        
    def list_end(self):
        return ['</tbody></table></body></html>']