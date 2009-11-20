@map_function
def tinderbox_id(doc):
    if 'tinderboxID' in doc:
        emit(doc['tinderboxID'], doc['tinderboxID'])

# function(doc) {
#   if (doc.tinderboxID) {
#     emit(doc.tinderboxID, doc.tinderboxID);
#   }
# }
