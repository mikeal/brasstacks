import notifications
from webenv.rest import RestApplication
from webenv import HtmlResponse

boiler = "You will need to verify your email address.\n\nPlease open this url in your browser: "

class Users(object):
    def __init__(self, db):
        self.db = db
    def get_user_by_email(self, email):
        rows = self.db.views.brasstacks.usersByEmail(key=email)
        if len(rows) is 0:
            return self.create_anonymous_user(email)
        else:
            return rows[0]
    def create_anonymous_user(self, email):
        info = self.db.create({"email":email, "verified":False, "anonymous":True, "email_verified":False, "type":"user"})
        notifications.send_email(email, "Verify email", boiler+"http://brasstacks.mozilla.com/users/email_verify/"+info['id'])
        return self.db.get(info['id'])
        
class UsersApplication(RestApplication):
    def __init__(self, db):
        super(UsersApplication, self).__init__()
        self.db = db
    def GET(self, request, collection=None, resource=None):
        if collection == "email_verify":
            user = self.db.get(resource)
            user.email_verified = True
            self.db.update(user)
            return HtmlResponse("<html><title>Verified!</title><body>Congradulations, you have verfied this email address.</body></html>")

