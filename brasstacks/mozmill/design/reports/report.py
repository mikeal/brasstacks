try:
    import simplejson as json
except:
    import json

import uuid
import pystache
import os

@update_function
def new_report(doc, req):
    doc = json.loads(req['body'])
    doc['_id'] = str(uuid.uuid1()).replace('-','')
    return doc, doc['_id']

@show_function
def show_report(doc, req):
    passed = 0
    failed = 0
    for test in doc['tests']:
        passed += test['passed']
        failed += test['failed']

    info = {"appName" : doc['app.name'],
            "appVersion" : doc['app.version'],
            "platformVersion" : doc['platform.version'],
            "locale" : doc['locale'],
            "osName" : doc['sysinfo']['os.name'],
            "osVersion" : doc['sysinfo']['os.version.number'],
            "testPath" : doc['testPath'],
            "start" : doc['starttime'],
            "end" : doc['endtime'],
            "passes" : str(passed),
            "fail" : str(failed),
            }
    html = pystache.render(start, info)

    for test in doc['tests']:
        filename = test['filename'].replace(os.path.dirname(doc['testPath']), '')

        for passed in test['passes']:
            row = {
                'class' : "pass",
                'filename' : filename,
                'name' : test['name'],
                'test' : passed['function'],
                'comment' : ""
            }
            html += pystache.render(table_test, row)
        for failed in test['fails']:
            row = {
                'class' : "fail",
                'filename' : filename,
                'name' : test['name'],
                'test' : failed.get('exception', {}).get('message','')
            }
            html += pystache.render(table_test, row)

    html += "</table>"
    html += "</body></html>"
    return {'body':html, 'headers':{'content-type':'text/html'}}

start = u"""
<html>
  <head>
    <title>Test-run Report</title>
    <style>
      table {
        border : 1px solid #555;
        padding : 0;
      }
      td {
        border: 1px solid #555;
      }
      .pass {
        background: #8f8;
      }
      
      .fail {
        background: #f88;
      }
    </style>
  </head>
  <body>
    <h1>Test-run Report</h1>
    <div><a href="../../_list/summary/summary">Back</a> to summary page.</div>
    <h2>Information</h2>
    <table>
    <tr>
     <td>Application:</td><td>{{appName}} {{appVersion}} ({{platformVersion}}, {{locale}})</td>
    </tr><tr>
      <td>Platform:</td><td>{{osName}} {{osVersion}}</td>
    </tr><tr>
      <td>Test path:</td><td>{{testPath}}</td>
    </tr><tr>
      <td>Duration:</td><td>{{start}} - {{end}}</td>
    </tr><tr>
      <td>Passes / Fail:</td><td>{{passes}} / {{fail}}</td>
    </tr>
    </table>
    <h2>Results</h2>
    <table>
"""

table_test = u"""
<tr class="{{class}}">
<td>{{class}}</td>
<td>{{filename}}</td>
<td>{{name}}</td>
<td>{{test}}</td>
<tr>
"""
