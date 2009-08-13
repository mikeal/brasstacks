function(doc) {
  emit([doc.product, doc.os, doc.testtype], 1);
  
  emit([doc.product], 1);
  emit([doc.os], 1);
  emit([doc.testtype], 1);
  
  emit("all", 1);
}
