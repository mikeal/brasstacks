function (doc) {
  if (doc.os) {
    emit(doc.os, 1)
  }
}