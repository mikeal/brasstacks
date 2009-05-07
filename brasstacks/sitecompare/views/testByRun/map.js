function(doc) {
  if (doc.type == "comparison-test") {
    emit(doc["run-id"], doc);
  }
}



