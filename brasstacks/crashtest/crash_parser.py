import sys
import couchquery

db = couchquery.Database('http://localhost:5984/crashtest')

bad_lines = []
bad_results = []

def parse_line(line):
    try:
        (signature,	url, uuid_url, client_crash_date, date_processed, last_crash, product,	
         version, build, branch, os_name, os_version, cpu_name, address, bug_list,	
         user_comments,) = line.split('\t')
    except:
        bad_lines.append(line)
        output('e')
        return
    
    doc = {'signature':signature, 'url':url, 'type':'crash',
           'uuid_url':uuid_url, 'client_crash_date':client_crash_date, 
           'date_processed':date_processed, 'last_crash':last_crash, 
           'product':product, 'version':version, 'build':build, 'branch':branch, 
           'os_name':os_name, 'os_version':os_version, 'cpu_name':cpu_name, 
           'address':address, 'bug_list':bug_list,	'user_comments':user_comments}
    return doc

def output(s):
    sys.stdout.write(s)
    sys.stdout.flush()

def parse(f):
    doc_buffer = []
    count = 0
    line = f.readline()
    while len(line) is not 0:
        doc = parse_line(line)
        if doc is not None:
            doc_buffer.append(doc)
        if len(doc_buffer) == 1000:
            info = db.create(doc_buffer)
            for result in info:
                if "error" in result:
                    bad_results.append(result)
                    output('x')
            count += 1000
            output('.')
            doc_buffer = []
        line = f.readline()
    info = db.create(doc_buffer)
    for result in info:
        if "error" in result:
            bad_results.append(result)
            output('x')
    count += len(doc_buffer)
    print "Created "+str(count)+" Documents"
    print "Failed to parse lines"
    for line in bad_lines:
        print line
    print "Failed to create Documents"
    for result in bad_results:
        print result
    
if __name__ == "__main__":
    parse(open(sys.argv[-1], 'r'))