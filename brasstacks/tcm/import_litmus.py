import simplejson
import httplib2

uri = 'https://litmus.mozilla.org/json.cgi?testcase_id='

h = httplib2.Http()

# startkey = 287
startkey = 4819

product_map = {"3":'Thunderbird',"1":"Firefox","2":"SeaMonkey","5":"Calendar",
               "6":"Rock your Firefox (Facebook application)",
               "8":"AMO (addons.mozilla.org)"}

def get_testcase(pk):
    try:
        resp, content = h.request(uri+str(pk))
    except:
        print pk, "failed in http"
    if len(content) is 0:
        print pk, 'is not a JSON object.'
        return True
    tc = simplejson.loads(content)
    # print simplejson.dumps(tc, sort_keys=True, indent=4)
    # print '+++++++++++++++++'
    testcase = {}
    testcase['creation_dt'] = tc['creation_date'].replace(' ','T')
    body = 'Steps\n-----\n\n' + tc['steps']
    if len(tc['expected_results']) is not 0:
        body += ('\n\nExpected Result\n---------------\n\n' + tc['expected_results'])
    testcase['description'] = {'en-us' : body}
    if tc["product_id"]["product_id"] not in product_map:
        print pk, 'is not in product map. ', tc["product_id"]["product_id"]
        return None
    # if tc["branch_id"]["branch_id"] not in branch_map:
    #     print pk, 'is not in branch map.', tc["branch_id"]["branch_id"]
    #     return None
    testcase['product'] = product_map[tc["product_id"]["product_id"]]
    testcase['title'] = tc['summary']
    # if len(tc['subgroups']) is not 0:
    #     print 'subgroups', tc['subgroups']
    # if len(tc['testgroups']) is not 0:
    #     print 'testgroups', tc['testgroups']
    testcase['litmus_pk'] = pk
    return True
    
if __name__ == "__main__":
    key = startkey
    while get_testcase(key) is True:
        key += 1
