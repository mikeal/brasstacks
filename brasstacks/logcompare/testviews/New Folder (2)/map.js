function(doc) {
  result = {};
  for(test in doc.tests) {
    for(key in doc.tests[test]) {
      if((key == 'fail') && (doc.tests[test][key] > 0)) {
        emit(doc.build, test);
      } 
    }
  }
}