import csv
import json
import subprocess
import os
import glob
import json
import urllib

r = csv.reader(open('static/data/archive_data.tsv'), dialect='excel-tab')
fields = r.next()

out = []
for idx,line in enumerate(r):
	row = dict(zip(fields, line))
	row["_id"] = idx
	out.append(row)

json.dump(out, open('static/data/db.json', 'w'), indent=2)

# prepare images
# with open('static/data/db.json', 'r') as json_data:
# 	data = json.load(json_data)
# 	for doc in data:
# 		urllib.urlretrieve(doc['ICON'], 'static/images/' + doc['ID'] + '.jpg')


def scale(path):
	basename = os.path.basename(path).split(".")[0]
	outpath = os.path.join("static/images/icons", "%s-icon.jpg" % (basename))
	# subprocess.call(['convert', path, '-resize', '80x', '-crop', '80x45+0+0', '-quality', '92', outpath])
	subprocess.call(['convert', path, '-resize', '80x45', '-quality', '92', outpath])

from multiprocessing.pool import ThreadPool as Pool

data = glob.glob("static/images/*.jpg")

N_THREADS = 8
pool = Pool(N_THREADS)
pool.map(scale, data)
pool.close()
pool.join()

