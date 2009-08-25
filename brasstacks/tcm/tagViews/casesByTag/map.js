function (doc) {
  if (doc.type == 'tcm-testcase') {
    for each(tag in doc.tags) {
      emit([tag, doc.product], doc);
    }
  }
}