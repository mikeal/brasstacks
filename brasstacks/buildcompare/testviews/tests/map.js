function(doc) {
  result = {};
  for(test in doc.tests) {
    for(key in doc.tests[test]) {
      result[key] = doc.tests[test][key];
    }
    emit([test, doc.timestamp], [doc.product, doc.os, doc.testtype, result]);
  }
}
