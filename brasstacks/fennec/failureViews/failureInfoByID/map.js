function (doc) {
  if (doc.type == 'fennec-failure-info') {
    emit(doc.run._id, doc);
  }
}