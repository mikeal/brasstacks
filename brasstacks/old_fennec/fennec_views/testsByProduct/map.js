function (doc) {
  if (doc.testtype && doc.product) {
    emit(doc.product, [doc.testtype, doc]); 
  }
}

