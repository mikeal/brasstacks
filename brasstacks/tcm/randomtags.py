import couchquery
import sys

db = couchquery.Database(sys.argv[-1])

all = db.views.all()

for doc in all:
    doc.tags = []

for i in range(len(all)):
    check1 = str(i)[-1]
    check2 = str(i)[-1] + str(i)[0]
    if check1 == '1':
        all[i].tags.append('addon')
    if check1 == '2' or check1 == '3' or check2 == '14':
        all[i].tags.append('bvt')
    if check1 == '7' or check1 == '4' or check2 == '29':
        all[i].tags.append('preferences')
    if check1 == '9' or check1 == '5' or check2 == '37':
        all[i].tags.append('preferences')
    if check1 == '7' or check2 == '32':
        all[i].tags.append('awesomebar')
    if check1 == '4' or check2 == '40':
        all[i].tags.append('l10n')
    if check1 == '3' or check1 == '5':
        all[i].tags.append('smoketest')

all.save()