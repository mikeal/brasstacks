@map_function
def signature_map(doc):
    if 'signature' in doc and doc['signature']:
        emit(doc['signature'], [doc['url'], doc['os_version']])

@reduce_function
def red(keys, values, length):
    x = {}
    for i in range(length):
        x.setdefault(keys[i], []).append(values[i])
    return x

@rereduce_function
def rered(values):
    res = {}
    for x in values:
        res.update(x)
    return res