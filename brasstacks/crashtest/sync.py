import os
from couchquery import Database

def main():
    db = Database('http://localhost:5984/crashtest')
    db.sync_design_doc('pyCrash', os.path.join(os.path.dirname(__file__), 'design'), language="python")
    
if __name__ == "__main__":
    main()