function(doc) {
  for(test in doc.tests) {
    result = {};
    for(key in doc.tests[test]) {
      result[key] = doc.tests[test][key] 
    }
    if(result['fail'] > 0) {
      emit([test, doc.timestamp], [result, doc.build]);
    }
  }
}
