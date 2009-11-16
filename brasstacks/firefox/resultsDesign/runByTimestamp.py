@map_function
def by_timestamp(doc):
    if 'type' in doc and doc['type'] == 'test-run':
        emit(doc['timestamp'], doc)

