@map_function
def timestamp_result(doc):
    if 'type' in doc and doc['type'] == 'test-run':
        result = {}
        for i in doc:
            if i != 'tests' and i != 'failed_test_names' and i != 'passed_test_names':
                result[i] = doc[i]
        for testname in doc['failed_test_names']:
            emit([testname, doc['testtype'], doc['product'], doc['os'], False, doc['timestamp']], result)
        for testname in doc['passed_test_names']:
            emit([testname, doc['testtype'], doc['product'], doc['os'], True, doc['timestamp']], result)

