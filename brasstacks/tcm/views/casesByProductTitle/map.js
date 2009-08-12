function (doc) {
  if (doc.type == 'tcm-testcase') {
    for (i in doc.title) {
      emit([doc.product, doc.title[i]], doc);
    }
  }
}
