import taichi as ti

def taichi_init():
    ti.init(arch=ti.gpu,packed=True,device_memory_fraction=0.5)

def taichi_shutdown():
    pass
