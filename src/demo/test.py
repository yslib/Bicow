import numpy as np
import taichi as ti
from realistic import RealisticCamera
ti.init(excepthook=True)

cam = RealisticCamera((400,400), [0.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0])

@ti.kernel
def run():
    print('front z: ', cam.front_z())
    print('lens z: ', cam.rear_z())

    for i in ti.static(range(3)):
        x = 0.1 + i * 0.1
        so = ti.Vector([x, 0.0, 2000.0])
        sd = ti.Vector([0.0, 0.0, -1.0])
        fo = ti.Vector([x, 0.0, cam.rear_z() - 1.0])
        fd = ti.Vector([0.0,0.0,1.0])
        ok1, o1, d1 = cam.gen_ray_from_scene(so, sd)
        ok2, o2, d2 = cam.gen_ray_from_film(fo, fd)
        tf = -o1.x / d1.x
        tf2 = -o2.x / d2.x
        #print(ok1, (o1 + tf * d1).z, o1, d1, tf)
        print(ok2, (o2 + tf2 * d2).z, o2, d2, tf2)

    fz1,pz1, fz2, pz2 = cam.compute_thick_lens_approximation()
    print('fz1, pz1, fz2, pz2: ', fz1, pz1, fz2, pz2)
    print('first focal length, second focal length', cam.get_focal_length())

run()