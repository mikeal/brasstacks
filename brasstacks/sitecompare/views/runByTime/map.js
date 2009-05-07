function(doc) {
  if (doc.type == "comparison-run") {
    emit(doc.starttime, doc);
  }
}



