import sys
import os
from typing import List, Tuple
import numpy as np
import imageio

SOURCE_ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
from base.imgio import ImageBracket, open_image_as_bracket, Image
from base.paramtype import FloatParam

from bicow.backend.taichi.taichi_setup import taichi_init
import bicow.backend.taichi.taichi_hdr_pipeline as ti_hdr

def bicow_init():
    taichi_init()

def bicow_shutdown():
    print('bicow_shutdown')

class HDRParamSet:
    """
    This object must be initialized after taichi backend initialization
    """
    k = FloatParam('k',0.0, 1.0, ti_hdr.K_cb)
    b = FloatParam('b',0.0, 1.0, ti_hdr.B_cb)
    zmin = FloatParam('zmin', 0.0,1.0, ti_hdr.zmin_cb)
    zmax = FloatParam('zmax', 0.0,1.0, ti_hdr.zmax_cb)

    def __init__(self):
        self.k = 0.18
        self.b = 0.95
        self.zmin = 0.05
        self.zmax = 0.95

class BicowHDR:
    def __init__(self, size:Tuple[int, int]):
        ti_hdr.init_param()
        self._param_set:HDRParamSet = HDRParamSet()
        self._data:np.ndarray = None
        self._size = size

    def __del__(self):
        ti_hdr.free()

    def set_data(self, image_bracket:ImageBracket):
        bracket = image_bracket
        imgs = []
        shutter = []
        for img in bracket.images:
            imgs.append(img.data)
            shutter.append(img.meta['shutter'])
        ldr_image_stack = np.array(imgs)
        shutters = np.array(shutter)
        ti_hdr.set_data(shutters, ldr_image_stack)

    def refine(self):
        self._data = ti_hdr.refine()

    def get_processed_data(self):
        """
        Returns the processed data
        """
        return self._data

    @property
    def param(self):
        return self._param_set



if __name__ == '__main__':
    bicow_init()

    raw_low = SOURCE_ROOT_DIR + '/../data/sunset_low.CR2'
    raw_nml = SOURCE_ROOT_DIR + '/../data/sunset_nml.CR2'
    raw_high = SOURCE_ROOT_DIR + '/../data/sunset_high.CR2'
    filenames = [raw_low, raw_nml, raw_high]
    print(filenames)
    brackets = open_image_as_bracket(filenames)
    cameray = BicowHDR(brackets)
    output = cameray.set_data(0).data
    name = 'output.jpeg'
    print('save image: {}'.format(name))
    imageio.imsave(name,output)
    bicow_shutdown()