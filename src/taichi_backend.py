from numpy.core.fromnumeric import shape
import taichi as ti
from taichi.lang.impl import default_cfg

ti_ldr_image_stack = None
ti_shutters = None
ti_weight_map_stack = None
ti_output_show = None
ti_output = None


K = None
B = None

Zmin = None
Zmax = None

CHANNEL_MAX_NUM = 65536.0

@ti.func
def w_uniform(z) -> ti.Vector:
    return ti.Vector([1.0, 1.0, 1.0]) * (z >= Zmin and z <= Zmax)

@ti.func
def gaussian(x) -> ti.Vector:
    return ti.exp(-4.0 * ((x-0.5)**2)/0.25)

@ti.func
def w_gaussian(z) -> ti.Vector:
    return gaussian(z) * (z >= Zmin and z <= Zmax)

@ti.func
def w_tent(z) -> ti.Vector:
    return min(z, 1.0-z) * (z >= Zmin and z <= Zmax)

@ti.func
def w_photo(z, t) -> ti.Vector:
    pass

@ti.func
def w(z):
    a = z/65535.0
    # return w_uniform(a)
    # return w_tent(a)
    # return w_tent(z.normalized())
    # return w_gaussian(a)
    return ti.Vector([1.0,1.0,1.0])
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
    return res * B[None]


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
    linear_hdr(n, ti_output)

    # tone mapping
    gm = geometric_mean(ti_output)
    mi = max_intensity(ti_output)
    print(mi)
    mi = K[None]/gm * mi

    for i, j in ti_output:
        scaled = (ti_output[i, j]/gm) * K[None]
        ti_output[i, j] = (scaled * (1.0 + scaled/(mi**2)))/(1.0 + scaled) * 255.0
        # ti_output[i, j] = scaled/(1.0+scaled) * 255.0

    # print(gm,mi)

    # debug, generate weight map
    for k, j, i in ti_weight_map_stack:
        ti_weight_map_stack[k, i, j] = w(ti_ldr_image_stack[k, i, j]) * 255


@ti.func
def resize(output_image,input_image):

    scale_i = input_image.shape[1] * 1.0 / output_image.shape[0] # rotate
    scale_j = input_image.shape[0] * 1.0 / output_image.shape[1]

    original_height = input_image.shape[0]

    scale = ti.Vector([scale_i, scale_j])
    P = ti.Vector([0, 0])
    for I in ti.grouped(output_image):
        P = ti.cast(I * scale, ti.i32)
        P[0], P[1] = original_height - P[1], P[0] # rotate and flip up and down for displaying
        output_image[I] = input_image[P]


@ti.kernel
def convert_to_rgb8():
    resize(ti_output_show, ti_output)
    for i,j in ti_output_show:
        ti_output_show[i,j] = ti_output_show[i,j] / 255.0

def create_ti_variables(shape):
    global ti_output, ti_ldr_image_stack, ti_weight_map_stack, ti_shutters, ti_output_show
    global K, B, Zmin, Zmax

    n = shape[0]  # number of images in stack
    channel = shape[3]  # pixel channel
    size = (shape[1], shape[2])  # image size

    ti_output = ti.Vector.field(channel, ti.i32, shape=(size[0], size[1]))
    ti_weight_map_stack = ti.Vector.field(
        channel, ti.i32, shape=(n, size[0], size[1]))
    ti_ldr_image_stack = ti.Vector.field(
        channel, ti.i32, shape=(n, size[0], size[1]))
    ti_shutters = ti.field(ti.f32, shape=n)

    K = ti.field(ti.f32, shape=())
    B = ti.field(ti.f32, shape=())

    Zmin = ti.field(ti.f32, shape=())
    Zmax = ti.field(ti.f32, shape=())


def initialize_ti_varibles(ldr_image_stack, shutters):
    global ti_output, ti_ldr_image_stack, ti_weight_map_stack, ti_shutters, ti_output_show
    global K, B, Zmin, Zmax

    ti_ldr_image_stack.from_numpy(ldr_image_stack)
    ti_shutters.from_numpy(shutters)
    Zmin[None] = 0.05
    Zmax[None] = 0.95

    K[None] = 0.18
    B[None] = 0.95

def pipeline(shutters, ldr_image_stack, preview_window):
    ti.init(arch=ti.gpu, default_fp = ti.f64)

    global ti_output, ti_ldr_image_stack, ti_weight_map_stack, ti_shutters, ti_output_show
    global K, B, Zmin, Zmax

    shape = ldr_image_stack.shape  # (n, width, height, channel)
    create_ti_variables(shape)

    n = shape[0]
    channel = shape[3]

    """
	You can not modify or create any Taichi-related varibles after accessing ti.field.
	So all creation must be done before any assignment
	"""

    if preview_window:
        window_size = (1920,1080)
        gui = ti.GUI('Cameray: The Best HDR Image Compositor in Binjiang District', window_size)
        ti_output_show = ti.Vector.field(channel, ti.f32, shape=window_size)
        initialize_ti_varibles(ldr_image_stack,shutters)

        # GUI widget varibles

        global K, B
        slider_k = gui.slider('Key', 0.0, 2.0, 0.01)
        slider_b = gui.slider('Burn', 0.0, 1.0, 0.01)
        slider_k.value = K[None]
        slider_b.value = B[None]

        while gui.running:
            K[None] = slider_k.value
            B[None] = slider_b.value
            hdr_comp(n)
            convert_to_rgb8()
            gui.set_image(ti_output_show)
            gui.show()
    else:
        initialize_ti_varibles(ldr_image_stack,shutters)
        hdr_comp(n)