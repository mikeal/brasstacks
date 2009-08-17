function(doc) {
  if (doc.product == "product1" && doc.os == "platform1") {
    result = {fail: 0, pass: 0, todo: 0, note: ''};
    //emit(doc.build, doc.tests);
    for (test in doc.tests) {
      //emit(doc.build, doc.teststest);
      //emit(test, (doc.tests[test])[fail]);
      for (key in doc.tests[test]) {
        result[key] = doc.tests[test][key];
      }
      emit(test, result);
    }
  }   
}