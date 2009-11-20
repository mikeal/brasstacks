@map_function
def signature_map(doc):
    if 'signature' in doc and doc['signature']:
        emit([doc['signature'], doc['os_name'], doc['version'][:3]], doc['url'])

@reduce_function
def red(values):
    return values

@rereduce_function
def rered(values):
    return [i for i in [v for v in values]]
