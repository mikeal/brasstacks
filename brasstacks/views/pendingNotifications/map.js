function (doc) {
  if (!doc.notifications_sent) {
    if (doc.email_notifications) {
      emit("email", doc);
    }
  }
}