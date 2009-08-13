try:
    import json as simplejson
except:
    import simplejson

import httplib2
import markdown
import sys, os
import couchquery
import timeout

from brasstacks import tcm
litmus_uri = 'https://litmus.mozilla.org/json.cgi?testcase_id='

h = httplib2.Http()

startkey = 287
endkey = 9999

product_map = {"3":'Thunderbird',"1":"Firefox","2":"SeaMonkey","5":"Calendar",
               "6":"Rock your Firefox (Facebook application)",
               "8":"AMO (addons.mozilla.org)", "9":"Weave", "10":"Firebug",
               "11":"Fennec", "12":"SUMO (support.mozilla.com)",
               "13":"SFx (spreadfirefox.com)"}

if not os.path.isfile('invalid_pks.json'):
    f = open('invalid_pks.json', 'w')
    f.write('[7836]')
    f.flush()
    f.close()

skip = simplejson.load(open('invalid_pks.json', 'r'))

def invalid(pk):
    i = simplejson.load(open('invalid_pks.json', 'r'))
    i.append(pk)
    simplejson.dump(i, open('invalid_pks.json', 'w'))

@timeout.timeout(20)
def get_testcase(pk, db):
    resp, content = h.request(litmus_uri+str(pk))
    if len(content) is 0:
        invalid(pk)
        return False
    tc = simplejson.loads(content)
    # print simplejson.dumps(tc, sort_keys=True, indent=4)
    # print '+++++++++++++++++' 
    testcase = {'type':'tcm-testcase'}
    
    if tc["product_id"]["product_id"] not in product_map:
        raise Exception(str(pk) +' is not in product map. ' + tc["product_id"]["product_id"])
    testcase['product'] = product_map[tc["product_id"]["product_id"]]
    testcase['title'] = {"en-us": tc['summary']}
    
    
    
    testcase['creation_dt'] = tc['creation_date'].replace(' ','T')
    body = 'Steps\n-----\n\n' + tc['steps']
    if len(tc['expected_results']) is not 0:
        body += ('\n\nExpected Result\n---------------\n\n' + tc['expected_results'])
    testcase['description_raw'] = {'en-us' : body}
    testcase['description_rendered'] = {'en-us' : markdown.markdown(body)}
    testcase['tags'] = []
    
    check = db.views.tcm.casesByProductTitle(key=[testcase['product'],testcase['title']['en-us']])
    if len(check) is not 0:
        doc = check.rows[0]
        doc.update(testcase)
        if pk not in doc.litmus_pks:
            doc.litmus_pks.append(pk)
        db.save(doc)
        return "updated"
    else:
        testcase['litmus_pks'] = [pk]
        db.save(testcase)
        return True
        
    # if tc["branch_id"]["branch_id"] not in branch_map:
    #     print pk, 'is not in branch map.', tc["branch_id"]["branch_id"]
    #     return None
    
def pushterm(s):
    sys.stdout.write(s)
    sys.stdout.flush()    
    
if __name__ == "__main__":
    if sys.argv[-1].startswith("http"):
        uri = sys.argv[-1]
    else:
        uri = 'http://localhost:5984/tcm'
    print "Database is "+uri
    db = couchquery.Database(uri)
    db.sync_design_doc('tcm', tcm.design_doc)    
    
    check = db.views.tcm.casesByLitmus(descending=True, limit=1).rows
    if len(check) is not 0:
        print "Latest litmus test imported was "+str(check.keys()[0])
        startkey = check.keys()[0]
    else:
        print "Litmus pk query returned "+str(len(check))
    
    for key in range(startkey, endkey):
        if key not in skip:
            result = None
            while result is None:
                try:
                    result = get_testcase(key, db)
                except Exception, e:
                    pushterm('x')
            if result is True:
                pushterm('c')
            elif result is False:
                pushterm('i')
            elif result == 'updated':
                pushterm('u')
            else:
                pushterm(str(key))  
        else:
            pushterm('s')