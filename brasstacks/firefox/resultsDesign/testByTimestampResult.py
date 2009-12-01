@map_function
def timestamp_result(doc):
    if 'type' in doc and doc['type'] == 'test-run':
        result = {}
        for i in doc:
            if i != 'tests':
                result[i] = doc[i]
        for test in doc['tests']:
            emit([test['name'], doc['testtype'], doc['product'], doc['os'], test['result'], doc['timestamp']], result)
