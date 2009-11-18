import pystache

start = """
<html>
    <title>{{head}}</title>
    <body>
        <style type="text/css">
        body {
          color:#222222;
          font-family:"Sabon LT Std","Hoefler Text","Palatino Linotype","Book Antiqua",serif;
          font-size:18px;
        }
        </style>

        <div class="header">{{head}}</div>
        <br>

        <style type="text/css">
        .testtype {
          color:#0000FF;
        }
        .passed {
          background-color:#5EDA9E;
        }
        .failed {
          background-color:#FF4040;
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
        .tdname {
          font-weight:bold;
          text-align:right;
          width:45%;
        }
        .tdvalue {
          text-align:left;
          width:45%;
        }
        table {
          text-align:center;
          width:90%;
          padding-left:5%;
          padding-right:5%;
        }
        .header {
          width:90%;
          font-weight:bold;
          text-align:center;
          padding-left:5%;
          padding-right:5%;
        }
        </style>

<div class="header">{{table_name}}</div>
<table>
  <thead>
    <tr>
      <th>timestamp</th>
      <th>build</th>
      <th>name</th>
      <th>testtype</th>
      <th>passed</th>
      <th>failed</th>
      <th>product</th>
      <th>os</th>
    <tr>
  </thead>
  <tbody>
"""

table_row = u"""
<tr class="{{class}}">
  <td>{{timestamp}}</td>
  <td><a href="/firefox/buildInfo/{{build}}">{{build}}</a></td>
  <td><a href="/firefox/testrunInfo/{{run_id}}">{{name}}</a></td>
  <td>{{testtype}}</td>
  <td>{{passed}}</td>
  <td>{{failed}}</td>
  <td>{{product}}</td>
  <td>{{os}}</td>
<tr>
"""

footer = """
<div>Latest <a href="?limit=50&descending=true">50</a>   <a href="?limit=100&descending=true">100</a>   <a href="?limit=250&descending=true">250</a>   <a href="?limit=500&descending=true">500</a>   <a href="?limit=1000&descending=true">1000</a></div>
"""

class_map = {True:"passed",False:"failed"}

class TestrunList(ListView):
    pass_map = {True:'pass',False:'failed'}
    def start(self, head, req):
        mapper = req['path'][-1]
        if mapper == 'runByTimestamp':
            head = 'Firefox Test Results'
            table_name = 'Latest Test Runs'
        elif mapper == 'byBuild':
            head = 'Firefox Test Results for '+req['query']['key']
            table_name = 'Test Runs'
        info = {'head':head,'table_name':table_name}
        return [pystache.render(start, info)], {'headers':{'content-type':'text/html'}}
    def list_row(self, row):
        doc = row['value']
        x = {'timestamp' :doc[0].split('.')[0],
             'run_id'    :doc[1],
             'build'     :doc[2],
             'name'      :doc[2]+'-'+doc[3]+'-'+doc[7],
             'testtype'  :doc[7],
             'passed'    :str(doc[4]),
             'failed'    :str(doc[5]),
             'product'   :doc[3],
             'os'        :doc[6],
             'class'     :class_map[doc[5] is 0],
             }
        return [pystache.render(table_row, x)]
        
    def list_end(self):
        return ['</tbody></table>', footer, '</body></html>']