import json
import subprocess
import os
from multiprocessing.pool import ThreadPool as Pool

N_THREADS = 8
data = json.load(open("static/db.json"))

def render(row):
    print 'render ', row["_id"], row["SOURCE"]
    subprocess.call([
        'phantomjs', 'screenshots.js', str(row['_id']), row['SOURCE']])
    print 'done ', row['_id']


# render(data[2])

pool = Pool(N_THREADS)
pool.map(render, data)
pool.close()
pool.join()
