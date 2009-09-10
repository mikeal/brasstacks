function (doc) {
  if (doc.type == 'fennec-test-run') {
    result = {};
    for (i in doc ) {
      if (i != "tests" && i != "failed_test_names" && i != "passed_test_names")  {
        result[i] = doc[i];
      }
    }
    for each(testname in doc.failed_test_names) {
      emit([testname, doc.testtype, doc.os, false, doc.timestamp], result);
    }
    for each(testname in doc.passed_test_names) {
      emit([testname, doc.testtype, doc.os, true, doc.timestamp], result);
    }
  }
}