import subprocess
import os
import glob

def scale(path):
    basename = os.path.basename(path).split(".")[0]
    outpath = os.path.join("jpg", "%s-320x.jpg" % (basename))
    medpath = os.path.join("jpg", "%s-60x.jpg" % (basename))
    minipath = os.path.join("jpg", "%s-20x.jpg" % (basename))

    subprocess.call(['convert', path, '-resize', '320x', '-crop', '320x3000+0+0', '-quality', '80', outpath])
    subprocess.call(['convert', path, '-resize', '20x',  '-crop', '20x500+0+0', '-quality', '60', minipath])
    subprocess.call(['convert', path, '-resize', '60x', '-crop', '60x1000+0+0', '-quality', '75', medpath])

from multiprocessing.pool import ThreadPool as Pool

data = glob.glob("images/*.jpg")

N_THREADS = 8
pool = Pool(N_THREADS)
pool.map(scale, data)
pool.close()
pool.join()

