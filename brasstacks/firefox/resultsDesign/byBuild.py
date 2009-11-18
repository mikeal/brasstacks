@map_function
def by_timestamp(doc):
    if 'type' in doc and doc['type'] == 'test-run':
        d = [ doc['timestamp'], doc['_id'], doc['build'], doc['product'], doc['pass_count'], 
              doc['fail_count'], doc['os'], doc['testtype'] ]
        emit(doc['build'], d)