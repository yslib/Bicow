import taichi as ti

ti.init()

a = ti.Vector([-1.2, 0.0])
b = ti.Vector([0.0, 0.0])
c = ti.Vector([-1.0, 3.0])


print(all(a < b))