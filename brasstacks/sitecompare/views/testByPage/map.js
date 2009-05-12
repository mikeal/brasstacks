function(doc) {
  if (doc.type == "comparison-test") {
    emit([doc['page-id'], doc.timestamp], doc);
  }
}

