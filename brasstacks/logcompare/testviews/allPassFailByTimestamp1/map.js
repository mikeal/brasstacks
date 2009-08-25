/*function(doc) {
  result = {};
  for(test in doc.tests) {
    for(key in doc.tests[test]) {
      //if((key == 'fail') && (doc.tests[test][key] > 0)) {
      //  result[key] = doc.tests[test][key];
      //}
      result[key] = doc.tests[test][key] 
    }
    if(result['fail'] > 0) {
      emit([test, doc.timestamp], result);
    }
  }
}*/

function(doc) {
  for(test in doc.tests) {
    result = {};
    for(key in doc.tests[test]) {
      result[key] = doc.tests[test][key] 
    }
    if(result['fail'] > 0) {
      emit([test, true, doc.timestamp], result);
    }
    else {
      emit([test, false, doc.timestamp], result);
    }
  }
}
