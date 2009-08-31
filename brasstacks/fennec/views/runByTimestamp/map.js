function (doc) {
  if (doc.testtype && doc.product == "Fennec") {
    emit(doc.timestamp, doc);
  }
}