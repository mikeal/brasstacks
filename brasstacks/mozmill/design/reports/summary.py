import pystache

@map_function
def summary_map(doc):
    if 'type' in doc and doc['type'] == 'mozmill-test':
        emit(doc['endtime'], [doc['_id'],doc['sysinfo']['os.name'], 
                              doc['appInfo.platformVersion'], doc['buildid'],
                              doc['testPath'], len(doc['tests'])])

begin = """<html>
<head><title>{{title}}</title></head>
<body>
<table>
    <thead>
        <tr>
            <th>endtime</th>
            <th>os</th>
            <th>os version</th>
            <th>buildid</th>
            <th>testpath</th>
            <th>total tests</th>
        </tr>
    </thead>
    <tbody>
"""
table_row = """
<tr>
    <td><a href="http://localhost:5984/mozmill/_design/reports/_show/report/{{id_}}">{{endtime}}</a></td>
    <td>{{os}}</td>
    <td>{{os_version}}</td>
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
        return [''], {'headers':{'content-type':'text/html'}}
    def handle_row(self, row):
        doc = row['value']
        endtime = row['key']
        row_info = {"id_"  :doc[0],
                    "os"   :doc[1],
                    "os_version": doc[2],
                    "buildid": doc[3],
                    "testpath": doc[4],
                    "total_tests": str(doc[5]),
                    "endtime":endtime,
                   }
        h = []
        if self.index is 0:
            h.append(pystache.render(begin, {"title":"Summary"}))
        h.append(pystache.render(table_row, row_info))
        return h
    def end(self):
        return [end]