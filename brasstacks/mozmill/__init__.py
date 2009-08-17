from webenv.rest import RestApplication
from webenv import Response

try:
    import json
except:
    import simplejson as json
    
class MozmillApplication(RestApplication):
    def __init__(self, db):
        self.db = db
        super(MozmillApplication, self).__init__()
    
    def POST(self, request, collection=None):
        if collection == 'report':
            obj = json.loads(str(request.body))
            result = self.db.create(obj)
            response = Response(json.dumps(result))
            response.content_type = 'application/json'
            return response