function(doc) {
  if (doc.type != undefined) {
    emit(doc.type, doc);
  }
}



