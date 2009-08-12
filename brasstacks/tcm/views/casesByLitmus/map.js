function (doc) {
  if (doc.type == 'tcm-testcase' && doc.litmus_pks) {
    for each(i in doc.litmus_pks) {
      emit(i, doc);
    }
  }
}