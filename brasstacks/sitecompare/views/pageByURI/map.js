function(doc) {
  if (doc.type == 'page') {
    if (doc.uri) {
      emit(doc.uri, doc);
    }
  }
}
