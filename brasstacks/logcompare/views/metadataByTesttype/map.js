function(doc) {
  emit([doc.testtype, doc.timestamp], [doc.build, doc.product, doc.os, doc.testtype, doc.timestamp]);
}
