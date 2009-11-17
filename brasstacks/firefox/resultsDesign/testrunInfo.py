import pystache
import zlib
    
start = """
<html>
    <title>Test Run Info {{buildname}} {{testtype}}</title>
    <body>
        <style type="text/css">
        body {
          color:#222222;
          font-family:"Sabon LT Std","Hoefler Text","Palatino Linotype","Book Antiqua",serif;
          font-size:18px;
          text-align:center;
        }
        </style>

        <div class="header">
            Build Info {{buildname}}
        </div>
        <br>
        <table class="infotable">
            <tr><td class="tdname">product</td><td class="tdvalue">{{product}}</td></tr>
            <tr><td class="tdname">OS</td><td class="tdvalue">{{os}}</td></tr>
            <tr><td class="tdname">timestamp</td><td class="tdvalue">{{timestamp}}</td></tr>
            <tr><td class="tdname">passed</td><td class="tdvalue">{{total_passed}}</td></tr>
            <tr><td class="tdname">failed</td><td class="tdvalue">{{total_failed}}</td></tr>
            <tr><td class="tdname">testtype</td><td class="tdvalue">{{testtype}}</td></tr>
        </table>
        
        <br><br>

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
          padding-left:5%;
          padding-right:5%;
        }
        </style>


<div class="header">Tests</div>
<table class="tablesorter">
  <thead>
    <tr>
      <th>name</th>
      <th>passed</th>
      <th>failed</th>
      <th>todo</th>
      <th>note</th>
    <tr>
  </thead>
  <tbody>
"""
table_row = u"""
<tr class="{{class}}">
  <td><a href="/firefox/testInfo/{{namehash}}">{{name}}</a></td>
  <td>{{passed}}</td>
  <td>{{failed}}</td>
  <td>{{todo}}</td>
  <td>{{note}}</td>
<tr>
"""

class_map = {True:"passed",False:"failed"}

@show_function
def build_info(doc, req):
    info = {"buildname"    :doc['build'],
            "product"      :doc['product'],
            "os"           :doc['os'],
            "timestamp"    :doc['timestamp'],
            "total_passed" :str(doc['pass_count']),
            "total_failed" :str(doc['fail_count']),
            "testtype"     :doc['testtype'],
            }
    
    t = pystache.render(start, info)
    for testname, test in doc['tests'].items():
        row = {"passed"  :str(test['pass']), 
               "failed"  :str(test['fail']), 
               "todo"    :str(test['todo']), 
               "note"    :str(test['note']),
               "name"    :testname,
               "namehash":zlib.crc32(testname),
               "class":class_map[test['fail'] == 0]
               }
        t += pystache.render(table_row, row)
    t += '</tbody></table></body></html>'
    
    return {'body':t, 'headers':{'content-type':'text/html'}}