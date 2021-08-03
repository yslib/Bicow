import taichi as ti
from typing import List

# declare ti param

ti_window_size = None
ti_sub_window_size = None
ti_sub_window_layout = None

ti_ldr_image_stack = None
ti_shutters = None
ti_weight_map_stack = None
ti_canvas = None
ti_hdr_image = None

ti_K = None
ti_B = None

ti_Zmin = None
ti_Zmax = None

CHANNEL_MAX_NUM = 65535.0

def zmin_cb(val):
    global ti_Zmin
    print('value update in taichi::zmin_cb()')
    ti_Zmin[None] = val

def zmax_cb(val):
    global ti_Zmax
    print('value update in taichi::zmax_cb()')
    ti_Zmax[None] = val

def K_cb(val):
    global ti_K
    print('value update in taichi::K_cb()')
    ti_K[None] = val

def B_cb(val):
    global ti_B
    ti_B[None] = val
    print('value update in taichi::B_cb()')

def pipeline_param_init():
    print('taichi_backend.pipeline_param_init')
    global ti_K, ti_B, ti_Zmin, ti_Zmax
    ti_K = ti.field(ti.f32, shape=())
    ti_B = ti.field(ti.f32, shape=())
    ti_Zmin = ti.field(ti.f32, shape=())
    ti_Zmax = ti.field(ti.f32, shape=())

    ti_Zmin[None] = 0.05
    ti_Zmax[None] = 0.95

    ti_K[None] = 0.18
    ti_B[None] = 0.95


@ti.func
def w_uniform(z) -> ti.Vector:
    return ti.Vector([1.0, 1.0, 1.0]) * (z >= ti_Zmin and z <= ti_Zmax)

@ti.func
def gaussian(x) -> ti.Vector:
    return ti.exp(-4.0 * ((x-0.5)**2)/0.25)

@ti.func
def w_gaussian(z) -> ti.Vector:
    return gaussian(z) * (z >= ti_Zmin and z <= ti_Zmax)

@ti.func
def w_tent(z) -> ti.Vector:
    return min(z, 1.0-z) * (z >= ti_Zmin and z <= ti_Zmax)

@ti.func
def w_photo(z, t) -> ti.Vector:
    pass

@ti.func
def w(z):
    a = z/CHANNEL_MAX_NUM
    # return w_uniform(a)
    # return w_tent(a)
    # return w_tent(z.normalized())
    return w_gaussian(a)
    # return ti.Vector([1.0,1.0,1.0])
    # return ti.Vector([128,128,128])


@ti.func
def sum_of_weight(n, i, j):
    sum = ti.Vector([0.0, 0.0, 0.0])
    for ind in range(n):
        sum += w(ti_ldr_image_stack[ind, i, j])
    return sum



@ti.func
def sum_of_weighted_radiance_log(n, i, j):
    sum = ti.Vector([0.0, 0.0, 0.0])
    for ind in range(n):
        val = ti_ldr_image_stack[ind, i, j]
        sum += w(val) * (ti.log(val) - ti.log(ti_shutters[ind]))
    return sum


@ti.func
def sum_of_weighted_radiance_linear(n, i, j):
    sum = ti.Vector([0.0, 0.0, 0.0])
    for ind in range(n):
        val = ti_ldr_image_stack[ind, i, j] + 1
        sum += w(val) * (val/ti_shutters[ind])
    return sum


@ti.func
def log_hdr(n, output):
    for i, j in output:
        no = sum_of_weighted_radiance_log(n, i, j)
        de = sum_of_weight(n, i, j)
        output[i, j] = ti.exp(no / de)
        if any(de == 0):
            if de[0] == 0:
                output[i, j][0] = 0
            if de[1] == 0:
                output[i, j][1] = 0
            if de[2] == 0:
                output[i, j][2] = 0


@ti.func
def linear_hdr(n, output):
    for i, j in output:
        no = sum_of_weighted_radiance_linear(n, i, j)
        de = sum_of_weight(n, i, j)
        output[i, j] = no / de
        if any(de == 0):
            if de[0] == 0:
                output[i, j][0] = 0
            if de[1] == 0:
                output[i, j][1] = 0
            if de[2] == 0:
                output[i, j][2] = 0


@ti.func
def max_intensity(image):
    res = ti.Vector([0.0, 0.0, 0.0])
    for i, j in image:
        res = ti.max(res, image[i, j])
    return res * ti_B[None]


@ti.func
def geometric_mean(image):
    sum = 0.0  # ti.Vector([0.0, 0.0, 0.0])
    inv_n = 1.0/(image.shape[0] * image.shape[1] * 1.0)
    for i, j in image:
        sum += inv_n * \
            ti.log(image[i, j].dot(ti.Vector([0.6, 0.3, 0.1])) + 1.0)
    return ti.exp(sum)


@ti.func
def max_val(image):
    res = ti.Vector([0, 0, 0])
    for i, j in image:
        res = ti.max(res, image[i, j])
    return res

@ti.kernel
def hdr_comp(n: ti.template()):
    # composition
    # log_hdr(n, ti_output)
    linear_hdr(n, ti_hdr_image)

    # tone mapping
    gm = geometric_mean(ti_hdr_image)
    mi = max_intensity(ti_hdr_image)
    print(mi)
    mi = ti_K[None]/gm * mi

    for i, j in ti_hdr_image:
        scaled = (ti_hdr_image[i, j]/gm) * ti_K[None]
        ti_hdr_image[i, j] = (scaled * (1.0 + scaled/(mi**2)))/(1.0 + scaled) * 255.0
        # ti_output[i, j] = scaled/(1.0+scaled) * 255.0

    # print(gm,mi)

    # debug, generate weight map
    for k, i, j in ti_weight_map_stack:
        ti_weight_map_stack[k, i, j] = w(ti_ldr_image_stack[k, i, j])


@ti.kernel
def convert_to_display():
    scale_i = ti_hdr_image.shape[1] * 1.0 / ti_sub_window_size[0]
    scale_j = ti_hdr_image.shape[0] * 1.0 / ti_sub_window_size[1]
    original_height = ti_hdr_image.shape[0]
    scale = ti.Vector([scale_i, scale_j])
    P = ti.Vector([0, 0])

    sub_windows = 0

    for i in range(ti_sub_window_size[0]):
        for j in range(ti_sub_window_size[1]):
            I = ti.Vector([i, j])
            P = ti.cast(I * scale, ti.i32)
            P[0], P[1] = original_height - P[1], P[0] # rotate and flip up and down
            ti_canvas[I] = ti_hdr_image[P] / 255.0  # hdr for display

    sub_windows += 1

    for k in range(ti_weight_map_stack.shape[0]):
        ind = k + sub_windows
        offset = ti.Vector([ind%ti_sub_window_layout[0], ind//ti_sub_window_layout[0]]) * ti_sub_window_size
        for i in range(ti_sub_window_size[0]):
            for j in range(ti_sub_window_size[1]):
                I = ti.Vector([i, j])
                P = ti.cast(I * scale, ti.i32)
                P[0], P[1] = original_height - P[1], P[0] # rotate and flip up and down
                ti_canvas[I + offset] = ti_weight_map_stack[k, P[0],P[1]]

    sub_windows += 3


def create_ti_variables(shape):
    global ti_hdr_image, ti_ldr_image_stack, ti_weight_map_stack, ti_shutters, ti_canvas
    global ti_K, ti_B, ti_Zmin, ti_Zmax

    n = shape[0]  # number of images in stack
    channel = shape[3]  # pixel channel
    size = (shape[1], shape[2])  # image size

    ti_hdr_image = ti.Vector.field(channel, ti.i32, shape=(size[0], size[1]))
    ti_weight_map_stack = ti.Vector.field(
        channel, ti.f32, shape=(n, size[0], size[1]))
    ti_ldr_image_stack = ti.Vector.field(
        channel, ti.i32, shape=(n, size[0], size[1]))
    ti_shutters = ti.field(ti.f32, shape=n)


def initialize_ti_varibles(ldr_image_stack, shutters):
    global ti_hdr_image, ti_ldr_image_stack, ti_weight_map_stack, ti_shutters, ti_canvas
    global ti_K, ti_B, ti_Zmin, ti_Zmax

    ti_ldr_image_stack.from_numpy(ldr_image_stack)
    ti_shutters.from_numpy(shutters)



def pipeline_init():
    ti.init(arch=ti.gpu, default_fp = ti.f64, device_memory_fraction=0.3)

def pipeline(shutters:List[int], ldr_image_stack, preview_window:bool):

    shape = ldr_image_stack.shape  # (n, width, height, channel)
    create_ti_variables(shape)

    n = shape[0]
    channel = shape[3]

    """
	You can not modify or create any Taichi-related varibles after accessing ti.field.
	So all creation must be done before any assignment
	"""

    sub_window_size = (400,300)
    sub_window_layout = (4, 1)
    window_size = (sub_window_size[0] * sub_window_layout[0], sub_window_size[1] * sub_window_layout[1])
    global ti_canvas, ti_window_size, ti_sub_window_layout,ti_sub_window_size
    if preview_window:
        gui = ti.GUI('Cameray: The Best HDR Image Compositor in Binjiang District', window_size)
        ti_canvas = ti.Vector.field(channel, ti.f32, shape=window_size)
        ti_window_size = ti.Vector([*window_size])
        ti_sub_window_layout = ti.Vector([*sub_window_layout])
        ti_sub_window_size = ti.Vector([*sub_window_size])

        initialize_ti_varibles(ldr_image_stack, shutters)

        # GUI widget varibles

        global ti_K, ti_B
        slider_k = gui.slider('Key', 0.0, 2.0, 0.01)
        slider_b = gui.slider('Burn', 0.0, 1.0, 0.01)
        slider_k.value = ti_K[None]
        slider_b.value = ti_B[None]

        while gui.running:
            ti_K[None] = slider_k.value
            ti_B[None] = slider_b.value
            hdr_comp(n)
            convert_to_display()
            gui.set_image(ti_canvas)
            gui.show()
    else:
        ti_canvas = ti.Vector.field(channel, ti.f32, shape=window_size)
        ti_window_size = ti.Vector([*window_size])
        ti_sub_window_layout = ti.Vector([*sub_window_layout])
        ti_sub_window_size = ti.Vector([*sub_window_size])
        initialize_ti_varibles(ldr_image_stack, shutters)
        hdr_comp(n)
        convert_to_display()

    return ti_canvas
