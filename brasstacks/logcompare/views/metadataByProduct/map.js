function(doc) {
  emit([doc.product, doc.timestamp], [doc.build, doc.product, doc.os, doc.testtype, doc.timestamp]);
}
