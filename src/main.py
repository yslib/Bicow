from typing import Dict, List, Any, Tuple
import cv2 as cv
import numpy as np
import sys
import param
import rawpy
import os
import taichi_backend
import imageio

SOURCE_PATH = os.path.dirname(__file__)

def main(argv: List[str])->None:
    param_dict = param.parse_args(argv)
    print(param_dict)
    if param_dict.get('file', None) is None:
        print('No input image file')
        sys.exit(-1)

    img = cv.imread(param_dict['file'], cv.IMREAD_UNCHANGED)
    """
    IMREAD_UNCHANGED
    IMREAD_GRAYSCALE
    IMREAD_COLOR
    IMREAD_ANYDEPTH
    IMREAD_ANYCOLOR
    """
    print(img.shape, img.dtype, img.min(), img.max())

def open_raw(filename):
    import io
    import subprocess

    proc = subprocess.Popen("dcraw -i -v {}".format(filename),shell=True,stdout=subprocess.PIPE)
    out, err = proc.communicate()
    out = io.StringIO(out.decode())
    lines = out.readlines()
    meta = {}
    for p in lines:
        if p.startswith('Shutter: '):
            val = p[9:-4]
            meta['shutter'] =eval(val)

    with rawpy.imread(filename) as raw:
        rgb = raw.postprocess(gamma=(1,1), no_auto_bright=True, output_bps=16, use_auto_wb=True)

    return meta, rgb




if __name__ == '__main__':
    # main(sys.argv)

    raw_low = '../data/sunset_low.CR2'
    raw_nml = '../data/sunset_nml.CR2'
    raw_high = '../data/sunset_high.CR2'


    low = []
    low.append(tuple(open_raw(raw_low)))
    nml = []
    nml.append(tuple(open_raw(raw_nml)))
    high = []
    high.append(tuple(open_raw(raw_high)))

    print(low[0][1].shape)

    imgs = taichi_backend.pipeline(nml,low,high, size=(4180, 6264, 3))
    ind = 0
    for img in imgs:
        name = 'img_{}.jpeg'.format(ind)
        ind += 1
        print('save image: {}'.format(name))
        imageio.imsave(name,img)