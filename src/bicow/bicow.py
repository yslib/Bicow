import sys
import os
from typing import List
import numpy as np
import imageio
SOURCE_ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
from base.imgio import ImageBracket, open_image_as_bracket, Image
from base.paramtype import FloatParam
import bicow.backend.taichi.hdr_pipeline as ti_hdr

def bicow_init():
    ti_hdr.pipeline_init()

def bicow_shutdown():
    print('cc_shutdown')

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
    def __init__(self, image_bracket_list:List[ImageBracket]):
        self._image_brackets = image_bracket_list
        ti_hdr.pipeline_param_init()
        self._param_set:HDRParamSet = HDRParamSet()
        self.process(0)

    def process(self,index):
        if index < 0 or index >= len(self._image_brackets):
            return
        bracket = self._image_brackets[index]
        imgs = []
        shutter = []
        for img in bracket.images:
            imgs.append(img.data)
            shutter.append(img.meta['shutter'])
        ldr_image_stack = np.array(imgs)
        shutters = np.array(shutter)
        ti_hdr.pipeline_set_data(shutters, ldr_image_stack)
        return ti_hdr.pipeline_refine()

    def refine(self):
        return ti_hdr.pipeline_refine()

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
    output = cameray.process(0).data
    name = 'output.jpeg'
    print('save image: {}'.format(name))
    imageio.imsave(name,output)
    bicow_shutdown()
