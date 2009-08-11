function (doc) {
  if (doc.type == 'tcm-testcase') {
    emit([doc.product, doc.creation_dt], doc);
  }
}