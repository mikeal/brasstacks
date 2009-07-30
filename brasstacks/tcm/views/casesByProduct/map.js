function (doc) {
  if (doc.type == "tcm-testcase") {
    emit(doc.product, doc);
  }
}