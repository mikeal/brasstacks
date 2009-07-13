function (doc) {
  if (doc.type == "productBuild" && doc.productType == "firefox") {
    emit(doc.buildid, doc);
  } 
}

