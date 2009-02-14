function (doc) {
  if (doc.testType != undefined) {
    emit(doc._id, doc);
  }
}