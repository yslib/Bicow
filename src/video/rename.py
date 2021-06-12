import cv2
import numpy as np
import sys
import os

if __name__ == '__main__':
    argc = len(sys.argv)
    path ='./'
    ind = 0
    if argc > 1:
        path = sys.argv[1]
    if argc > 2:
        ind = int(sys.argv[2])
    
    print('rename dir: {}'.format(path))
    
    for f in os.listdir(path):
        oldname = os.path.join(path,f)
        if os.path.isfile(oldname) == True:
            ind += 1
            newname = 'IMG_{:0>4d}.JPG'.format(ind)
            newname = os.path.join(path,newname)
            print('Rename {} to {} -- {}'.format(oldname,newname, ind))
            os.rename(oldname,newname)