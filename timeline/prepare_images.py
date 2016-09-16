import subprocess
import os
import glob

def scale(path):
    basename = os.path.basename(path).split(".")[0]
    outpath = os.path.join("static/images/icons/", "%s-icon.jpg" % (basename))

    subprocess.call(['convert', path, '-resize', '40x', '-crop', '40x22.5+0+0', outpath])

from multiprocessing.pool import ThreadPool as Pool

data = glob.glob("static/images/*.jpg")

N_THREADS = 8
pool = Pool(N_THREADS)
pool.map(scale, data)
pool.close()
pool.join()

