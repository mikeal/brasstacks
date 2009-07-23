function (doc) {
  if (doc.type == "user") {
    if (doc.email) {
      emit(doc.email, doc);
    }
  }
}


