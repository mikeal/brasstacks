function(doc) {
  emit([doc.os, doc.timestamp], [doc.build, doc.product, doc.os, doc.testtype, doc.timestamp]);
}
