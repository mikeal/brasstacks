@map_function
def failure_by_id(doc):
    if 'type' in doc and doc['type'] == 'failure-info':
        emit(doc['run']['timestamp'], doc)
