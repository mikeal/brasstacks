function(doc) {
  if (doc.type == "comparison-run") {
    if (doc.comparison_type) {
      emit([doc.comparison_type, doc.starttime], doc);
    } else {
      emit(["releaseVSnightly", doc.starttime], doc);
    }
  }
}



