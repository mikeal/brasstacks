function (doc) {
  if (doc.testType != undefined) {
    emit([doc.testType, doc.buildid], doc)
  }
}