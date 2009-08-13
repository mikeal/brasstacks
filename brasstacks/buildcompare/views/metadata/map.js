function(doc) {
  emit([doc.product, doc. os, doc.testtype, doc.timestamp], {'buildid': doc.build, 'product': doc.product, 'os': doc.os, 'testtype': doc.testtype, 'timestamp': doc.timestamp}
  );
}