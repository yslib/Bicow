import cv2
import numpy as np
import sys
import os

if __name__ == '__main__':

    argc = len(sys.argv)
    path ='./'
    if argc > 1:
        path = sys.argv[1]

    imgs = []
    resl = None
    resl = (1366 ,768)
    for root, dirs, files in os.walk(path, topdown=False):
        files = list(filter(lambda x: x.endswith('.png'), files))
        files = sorted(files, key=lambda x: int(x.split('.')[0][4:]))
        print("after sorted: ",files)
        total = len(files)
        print('Reading {} image(s) in {}'.format(total, path))
        ind = 0
        for f in files:
            print("Read {} of {} images -- %{}".format(ind + 1,total, float(ind+1)/total * 100))
            p = os.path.join(path,f)
            img = cv2.imread(p)
            if img is None:
                print('Failed to read img {}'.format(f))
                continue
            img = cv2.resize(img,resl)
            imgs.append(img)
            ind += 1

        break


    print('Start to compose video {}...{} '.format(resl, len(imgs)))
    fps = 24
    vw = cv2.VideoWriter(r'D:/video/sunset_1.avi',cv2.VideoWriter_fourcc(*'MJPG'),fps,resl)
    total = len(imgs)
    ind = 0
    for img in imgs:
        print('progress: {} of {} at %{}\n'.format(ind+1,total, float(ind+1)/total) * 100)
        vw.write(img)
        ind += 1

    vw.release()

