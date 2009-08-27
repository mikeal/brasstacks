function (doc) {
  if (doc.testtype && doc.product == "Fennec") {
    for (testname in doc.tests) {
      // Add all attributes from document
      result = {};
      for (i in doc) {
        if (i != "tests") {
          result[i] = doc[i];
        }
      }
      // Add all test attributes
      test = doc.tests[testname];
      for (t in test) {
        result[t] = test[t];
      }
      emit([testname, doc.testtype, doc.os, (test.fail == 0), doc.timestamp], result);
    }
  }
}