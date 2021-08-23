import taichi as ti

ti.init()

m = ti.Matrix([[2,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
v = ti.Vector([1,0,0,1])

print(m @ v)