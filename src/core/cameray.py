import sys
import os
SOURCE_ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT_DIR = os.path.dirname(SOURCE_ROOT_DIR)
sys.path.append(SOURCE_ROOT_DIR)
sys.path.append('.')
from typing import List
import numpy as np
from base.imgio import ImageBracket, open_image_as_bracket, Image
import taichi_backend
import imageio
from base.paramtype import FloatParam

class HDRParamSet:
    """
    This object must be initialized after taichi backend initialization
    """
    k = FloatParam('k',0.0, 1.0, taichi_backend.K_cb)
    b = FloatParam('b',0.0, 1.0, taichi_backend.B_cb)
    zmin = FloatParam('zmin', 0.0,1.0, taichi_backend.zmin_cb)
    zmax = FloatParam('zmax', 0.0,1.0, taichi_backend.zmax_cb)

    def __init__(self):
        self.k = 0.18
        self.b = 0.95
        self.zmin = 0.05
        self.zmax = 0.95

class CamerayHDR:
    def __init__(self, image_bracket_list:List[ImageBracket]):
        self._image_brackets = image_bracket_list
        taichi_backend.pipeline_param_init()
        self._param_set:HDRParamSet = HDRParamSet()

    def process(self,index):
        if index < 0 or index >= len(self._image_brackets):
            return
        bracket = self._image_brackets[index]
        imgs = []
        shutter = []
        for img in bracket.images:
            imgs.append(img.data)
            print(img)
            shutter.append(img.meta['shutter'])
        ldr_image_stack = np.array(imgs)
        shutters = np.array(shutter)
        output = taichi_backend.pipeline(shutters, ldr_image_stack, preview_window=False)
        return Image('', output.to_numpy())

    @property
    def param(self):
        return self._param_set


def cc_init():
    taichi_backend.pipeline_init()

def cc_shutdown():
    print('cc_shutdown')

if __name__ == '__main__':
    cc_init()

    raw_low = SOURCE_ROOT_DIR + '/../data/sunset_low.CR2'
    raw_nml = SOURCE_ROOT_DIR + '/../data/sunset_nml.CR2'
    raw_high = SOURCE_ROOT_DIR + '/../data/sunset_high.CR2'
    filenames = [raw_low, raw_nml, raw_high]
    print(filenames)
    brackets = open_image_as_bracket(filenames)
    cameray = CamerayHDR(brackets)
    output = cameray.process(0).data
    name = 'output.jpeg'
    print('save image: {}'.format(name))
    imageio.imsave(name,output)
