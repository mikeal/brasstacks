function (doc) {
  if (doc.type == 'fennec-failure-info') {
    for (testname in doc.fails) {
      test = doc.fails[testname];
      if (test['firstfailed']['_id'] == doc.run._id) {
        emit(doc.run.timestamp, {"run":doc.run, "testname":testname, "testinfo":test});
      }
    }
  }
}