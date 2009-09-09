function (doc) { 
  if(doc.timestamp && doc.build && doc.product && doc.os && doc.testtype && doc.tests) {
    emit([doc.build, doc.timestamp, doc.product, doc.os, doc.testtype, doc._id], doc.tests);
  }
}
