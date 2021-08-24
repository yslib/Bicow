import numpy as np
import taichi as ti
from realistic import RealisticCamera
ti.init(excepthook=True)

cam = RealisticCamera((400,400), [0.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0])

@ti.kernel
def run():
    x = 0.01
    so = ti.Vector([x, 0.0, 2000.0])
    sd = ti.Vector([0.0,0.0,-1.0])
    print(cam.get_lenses_focal_length())

run()