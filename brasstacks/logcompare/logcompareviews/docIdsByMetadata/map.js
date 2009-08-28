function(doc) {
  if(doc.product && doc.os && doc.testtype && doc.timestamp) {
    emit([doc.product, doc.os, doc.testtype, doc.timestamp], doc._id);
  }
}
