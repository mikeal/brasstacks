function(doc) {
  if(doc.tests && doc.product && doc.os && doc.testtype) {
    emit([doc.product, doc.os, doc.testtype, doc.timestamp], [doc.tests, doc._id]);
  }
}
