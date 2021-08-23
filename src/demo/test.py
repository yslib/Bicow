import numpy as np
import taichi as ti
from realistic import RealisticCamera
ti.init(excepthook=True)

cam = RealisticCamera((400,400), [0.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0])

@ti.kernel
def run():
    print('aaaaaaa')
    a, b = cam.get_lenses_focal_length()
    print('bbbbbb')
    print('focal length: ', a,b)

run()