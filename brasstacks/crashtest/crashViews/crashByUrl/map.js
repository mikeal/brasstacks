function (doc) {
  if (doc.type == 'crash') {
    emit(doc.url, doc);
  }
}