function (doc) {
  if (doc.email_notifications) {
    for each(n in doc.email_notifications) {
      if (n.email) {
        emit(n.email, doc);
      }
    }
  }
}