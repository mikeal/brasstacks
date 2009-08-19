function(doc) {
  emit(
    [doc.os, doc.timestamp], 
    {'buildid': doc.build, 'product': doc.product, 'os': doc.os, 'testtype': doc.testtype, 'timestamp': doc.timestamp}
  );
}
