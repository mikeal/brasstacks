function(doc) {
  if (doc.type == 'comparison-test') {
    if (doc.result.images_differ) {
      emit(doc.uri, doc.result.difference);
    } else {
      emit(doc.uri, 0)
    }
  }
}



