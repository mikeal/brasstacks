function(doc) {
  for(test in doc.tests) {
    emit(doc.build, test);
  }
}