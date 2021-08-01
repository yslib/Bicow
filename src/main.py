from typing import Dict, List, Any, Tuple
import numpy as np
import sys
import param
import rawpy
import os
import taichi_backend
import imageio

SOURCE_PATH = os.path.dirname(__file__)


def open_raw(filename):
    import io
    import subprocess

    proc = subprocess.Popen("dcraw -i -v {}".format(filename),
                            shell=True, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    out = io.StringIO(out.decode())
    lines = out.readlines()
    meta = {}
    for p in lines:
        if p.startswith('Shutter: '):
            val = p[9:-5]
            meta['shutter'] = eval(val)

    with rawpy.imread(filename) as raw:
        rgb = raw.postprocess(
            gamma=(1, 1), no_auto_bright=True, output_bps=16, use_auto_wb=True)

    return meta, rgb


if __name__ == '__main__':
    # main(sys.argv)
    raw_low = 'data/sunset_low.CR2'
    raw_nml = 'data/sunset_nml.CR2'
    raw_high = 'data/sunset_high.CR2'
    param_dict = param.parse_args(sys.argv)

    param_dict = param.parse_args(sys.argv)
    cfg = param_dict.get('cfg', {})
    if param_dict.get('interactive', False):
        pass

    img1_param, img_rbg1 = open_raw(raw_low)
    img2_param, img_rbg2 = open_raw(raw_nml)
    img3_param, img_rbg3 = open_raw(raw_high)

    ldr_image_stack = np.array([img_rbg1, img_rbg2, img_rbg3])
    shutters = np.array(
        [img1_param['shutter'], img2_param['shutter'], img2_param['shutter']])

    print(ldr_image_stack.shape, shutters)
    output = taichi_backend.pipeline(shutters, ldr_image_stack, preview_window=True)

    name = 'output.jpeg'
    print('save image: {}'.format(name))
    imageio.imsave(name,output.to_numpy())
