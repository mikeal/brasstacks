function(doc) {
  if(doc.product && doc.os && doc.testtype) {
    emit([doc.product, doc.os, doc.testtype], 1);
  }
}
