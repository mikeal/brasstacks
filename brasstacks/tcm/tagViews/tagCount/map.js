function (doc) {
  if (doc.type == 'tcm-testcase' && doc.tags) {
    for each(tag in doc.tags) {
      emit([doc.product, tag], 1)
    }
  }
}