import os
import smtplib
from email.mime.text import MIMEText

from webenv.rest import RestApplication
from webenv import HtmlResponse
import couchquery

me = "noreply@mikealrogers.com"

this_dir = os.path.abspath(os.path.dirname(__file__))

def send_email(to, subject, text):
    msg = MIMEText(text)
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = to

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP()
    if type(to) is not list:
        to = [to]
    s.sendmail(me, to, msg.as_string())
    s.quit()

# class TicketApplication(RestApplication):
#     def __init__(self, dburl):
#         super(self, RestApplication).__init__(self)
#         self.db = couchquery.CouchDatabase(dburl)
#         # self.db.sync_design_doc("tickets", os.path.join(this_dir, 'ticketviews'))
#     
#     def GET(self, request, uuid):
#         ticket = self.db.get(uuid)
#         return self.resolve(ticket)
#         
#     def POST(self, request):
#         self.create(request.body)
#     def PUT(self, request):
#         self.create(request.boyd)
# 
# class EmailNoficationVerificationApplication(RestApplication):
#     def resolve(self, ticket):
#         user = self.db.views.brasstacks.usersByEmail(key=ticket.email).rows[0]        
#         user.email_verified = True
#         self.db.save(user)
#         notifications = self.db.views.brasstacks.emailNotificationsByEmail(key=ticket.email)
#         for doc in notifications:
#             for n in [n for n in doc.email_notifications if doc.email == ticket.email]:
#                 doc.email_notifications.remove(n) 
#                 n.verified = True
#                 doc.email_notifications.append(n)
#             self.db.save(doc)
#         return HtmlResponse(self.verified_html)
#     
#     email_subject = "Notification verification"
#     email_message = "Before receiving notifications you will need to verify you email address.\n\n"
#     base_url = "http://brasstacks.mozilla.com/verify/email/"
#     verified_html = "<html><head>Verified!</head><body><h2>You have been verified!</h2></body></html>"
#     creation_html = "<html><head>Verification Email Sent!</head><body><h2>We have sent an email to be verified. You will need to verify your email address before we can send you notifications.</h2></body></html>"
#     
#     def create(self, body):
#         if hasattr(body, 'form'):
#             email = body.form['email']
#             info = self.db.create({"type":"ticket", "tickettype":"email", "email":email})
#             msg = self.email_message+"Simply open "+self.base_url+info['id']
#             send_email(email, self.email_notification, msg)
#             return HtmlResponse(self.creation_html)





