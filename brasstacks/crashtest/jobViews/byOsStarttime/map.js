function (doc) {
  if (doc.type == "job") {
    emit([doc.os, doc.starttime], doc);
  }
}