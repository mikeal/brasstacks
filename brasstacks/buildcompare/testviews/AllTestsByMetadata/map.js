function(doc) {
  //if(doc.product == "product1" && doc.os == "platform1") {
    result = {};
    for(test in doc.tests) {
      for(key in doc.tests[test]) {
        result[key] = doc.tests[test][key];
      }
      emit([test, doc.product, doc.os, doc.testtype], result);
    }
  //}   
}
