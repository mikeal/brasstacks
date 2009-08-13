function(doc) {
  emit([doc.product, doc.os, doc.testtype, doc.timestamp], doc.build);
}