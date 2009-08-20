function(doc) {
  //emit("all", 1);
  emit(doc.product, 1);
  emit(doc.os, 1);
  emit(doc.testtype, 1);
  emit([doc.product, doc.os, doc.testtype], 1);
  //emit([doc.product, doc.os], 1);
  //emit([doc.testtype, doc.os], 1);
  //emit([doc.product, doc.testtype], 1);
}