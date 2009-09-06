function (doc) { 
  if(doc.timestamp && doc.build && doc.product && doc.os && doc.testtype && doc.tests) {
    emit([doc.product, doc.os, doc.testtype, doc.timestamp, doc.build, doc._id], doc.tests);
  }
}
