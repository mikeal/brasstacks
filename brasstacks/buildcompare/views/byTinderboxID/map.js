function(doc) {
  if (doc.tinderboxID) {
    emit(doc.tinderboxID, doc.tinderboxID);
  }
}
