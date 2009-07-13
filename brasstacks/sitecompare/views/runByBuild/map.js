function(doc) {
  if (doc.type == "comparison-run") {
    emit(doc.release_docid, doc);
    emit(doc.nightly_docid, doc);
  }
}



