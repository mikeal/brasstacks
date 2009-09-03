function(doc) {
  if(doc.tests && doc.product && doc.os && doc.testtype) {
    for(test in doc.tests) {
      result = {};
      for(key in doc.tests[test]) {
        result[key] = doc.tests[test][key] 
      }
      emit([test, doc.product, doc.os, doc.testtype, doc.timestamp], [result, doc._id]);
    }
  }
}
