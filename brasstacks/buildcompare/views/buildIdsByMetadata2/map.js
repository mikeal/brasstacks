function(doc) {
  emit([doc.timestamp, doc.product, doc.os, doc.testtype], doc.build);
}
