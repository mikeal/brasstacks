import pystache

@map_function
def summary_map(doc):
    if 'type' in doc and doc['type'] == 'mozmill-test':
        emit(doc['starttime'], [doc['_id'],
                              doc['sysinfo']['os.name'] + ' ' + doc['sysinfo']['os.version.number'], 
                              doc['app.version'], doc['app.buildID'],
                              doc['testPath'], len(doc['tests']), doc['app.name']])

begin = """<html>
  <head>
    <title>{{title}}</title>
    <style>
      table {
        border-spacing: 0;
        padding : 0;
      }
      td, th {
        margin: 0;
        border: 1px solid #555;
      }
    </style>
</head>
<body>
<table>
    <thead>
        <tr>
            <th>start time</th>
            <th>os</th>
            <th>product</th>
            <th>version</th>
            <th>buildid</th>
            <th>testpath</th>
            <th>total tests</th>
        </tr>
    </thead>
    <tbody>
"""
table_row = """
<tr>
    <td><a href="../../_show/report/{{id_}}">{{starttime}}</a></td>
    <td>{{os}}</td>
    <td>{{product}}</td>
    <td>{{version}}</td>
    <td>{{buildid}}</td>
    <td>{{testpath}}</td>
    <td>{{total_tests}}</td>
<tr>
"""

end = """
</tbody></table></body></html>
"""

class Summary(ListView):
    def start(self, head, req):
        return [''], {'headers':{'Content-Type':'text/html'}}
    def handle_row(self, row):
        doc = row['value']
        starttime = row['key']
        row_info = {"id_"  :doc[0],
                    "os"   :doc[1],
                    "version": doc[2],
                    "buildid": doc[3],
                    "testpath": doc[4],
                    "total_tests": str(doc[5]),
                    "starttime":starttime,
                    "product":doc[6]
                   }
        h = []
        if self.index is 0:
            h.append(pystache.render(begin, {"title":"Summary"}))
        h.append(pystache.render(table_row, row_info))
        return h
    def end(self):
        return [end]
