import pystache

@map_function
def failmap(doc):
    if 'type' in doc and doc['type'] == 'failure-info':
        for testname in doc['fails']:
            test = doc['fails'][testname]
            if test['firstfailed']['_id'] == doc['run']['_id']:
                emit(doc['run']['timestamp'].split(' ')[0], 1)

@reduce_function
def reducer(values, rereduce=False):
    return sum(values)

begin = """
<html>
<body>
<script language="javascript" type="text/javascript" 
        src="/firefox/_couchdb/_design/failures/jquery.js"></script>
<script language="javascript" type="text/javascript" 
        src="/firefox/_couchdb/_design/failures/jquery.flot.navigate.js"></script>
<script language="javascript" type="text/javascript" 
        src="/firefox/_couchdb/_design/failures/jquery.flot.js"></script>
<div id="failure_table" class="failure_table"/> 
<table>
    <thead>
        <tr>
            <th>Day</th>
            <th>Failures</th>
        </tr>
    <thead>
    <tbody>
"""

table_row = """
<tr>
    <td>{{day}}</td>
    <td>{{failures}}</td>
</tr>
"""

end = """
    </tbody>
</table>
<script language="javascript" type="text/javascript">
$(function () {

var data = JSON.parse('{{{days}}}');
var days = [];
for (k in data) { days.push(k) };
days.sort();
var failures_line = [[data[k], k] for each(k in days)];



}
</script>

</body>
</html>
"""

class FailChart(ListView):
    def start(self, head, req):
        self.days = {}
        return [begin], {'headers':{'content-type':'text/html'}}
    def list_row(self, row):
        day = row['key']
        failures = row['value']
        self.days[day] = failures
        return [pystache.render(table_row, {'day':day,'failures':failures})]
    def list_end(self):
        return pystache.render(end, self.days)
