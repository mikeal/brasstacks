function (doc) {
  if (doc.type == 'fennec-test-run') {
    emit(doc.timestamp, doc);
  }
}