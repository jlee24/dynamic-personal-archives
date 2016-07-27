import csv
import json

r = csv.reader(open('static/data/Engelbart Archives.tsv'), dialect='excel-tab')
fields = r.next()

out = []
for idx,line in enumerate(r):
    row = dict(zip(fields, line))
    row["_id"] = idx
    out.append(row)

json.dump(out, open('static/data/db.json', 'w'), indent=2)