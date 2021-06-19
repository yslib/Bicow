import taichi as ti
import numpy as np

ti_ldr_image_stack = None
ti_shutters = None
ti_weight_map_stack = None
output = None

Zmin = 0.05
Zmax = 0.95

K = 0.18
B = 0.95

@ti.func
def w_uniform(z)->ti.Vector:
	return ti.Vector([1.0, 1.0, 1.0]) * (z >= Zmin and z<=Zmax)

@ti.func
def gaussian(x)->ti.Vector:
	return ti.exp(-4.0 * ((x-0.5)**2)/0.25)

@ti.func
def w_gaussian(z)->ti.Vector:
	return gaussian(z) * (z >= Zmin and z <= Zmax)

@ti.func
def w_tent(z)->ti.Vector:
	return min(z, 1.0-z) * (z >= Zmin and z <= Zmax)

@ti.func
def w_photo(z, t)->ti.Vector:
	pass

@ti.func
def w(z):
	a = z/65535.0
	# return w_uniform(a)
	# return w_tent(a)
	# return w_tent(z.normalized())
	return w_gaussian(a)
	# return ti.Vector([128,128,128])

@ti.func
def sum_of_weight(n, i,j):
	sum = ti.Vector([0.0,0.0,0.0])
	for ind in range(n):
		sum += w(ti_ldr_image_stack[ind,i,j])
	return sum

@ti.func
def sum_of_weighted_radiance_log(n, i, j):
	sum = ti.Vector([0.0,0.0,0.0])
	for ind in range(n):
		val = ti_ldr_image_stack[ind,i,j]
		sum += w(val) * (ti.log(val) - ti.log(ti_shutters[ind]))
	return sum

@ti.func
def sum_of_weighted_radiance_linear(n, i, j):
	sum = ti.Vector([0.0,0.0,0.0])
	for ind in range(n):
		val = ti_ldr_image_stack[ind,i,j] + 1
		sum += w(val) * (val/ti_shutters[ind])
	return sum

@ti.func
def log_hdr(n, output):
	for i,j in output:
		no = sum_of_weighted_radiance_log(n, i, j)
		de = sum_of_weight(n,i, j)
		output[i,j] = ti.exp(no / de)
		if any(de == 0):
			if de[0] == 0:
				output[i, j][0] = 0
			if de[1] == 0:
				output[i, j][1] = 0
			if de[2] == 0:
				output[i, j][2] = 0

@ti.func
def linear_hdr(n,output):
	for i, j in output:
		no = sum_of_weighted_radiance_linear(n, i, j)
		de = sum_of_weight(n, i, j)
		output[i,j] = no / de
		if any(de == 0):
			if de[0] == 0:
				output[i, j][0] = 0
			if de[1] == 0:
				output[i, j][1] = 0
			if de[2] == 0:
				output[i, j][2] = 0

@ti.func
def max_intensity(image):
	res = ti.Vector([0.0,0.0,0.0])
	for i, j in image:
		res = ti.max(res, image[i, j])
	return res * B

@ti.func
def geometric_mean(image):
	sum = 0.0 # ti.Vector([0.0, 0.0, 0.0])
	inv_n = 1.0/(image.shape[0] * image.shape[1] * 1.0)
	for i,j in image:
		sum += inv_n * ti.log(image[i, j].dot(ti.Vector([0.6,0.3,0.1])) + 1.0)
	return ti.exp(sum)

@ti.func
def max_val(image):
	res = ti.Vector([0,0,0])
	for i,j in image:
		res = ti.max(res,image[i,j])
	return res


@ti.kernel
def hdr_comp(x:ti.f32):
	# composition
	# log_hdr(n, output)
	n = 3
	linear_hdr(n,output)
	# tone mapping
	gm = geometric_mean(output)
	mi = max_intensity(output)
	for i, j in output:
		scaled = (output[i,j]/gm) *K
		# output[i, j] = (scaled * (1.0 + scaled/(mi**2)))/(1.0 + scaled) * 255.0
		output[i, j] = scaled/(1.0+scaled) * 255.0

	print(gm, mi)
	# debug, generate weight map
	for k,j,i in ti_weight_map_stack:
		ti_weight_map_stack[k,i,j] = w(ti_ldr_image_stack[k,i, j]) * 255


def pipeline(shutters ,ldr_image_stack, size):
	ti.init(arch=ti.gpu)
	global output,ti_ldr_image_stack,ti_weight_map_stack,ti_shutters
	n = 3
	output = ti.Vector.field(size[2], ti.i32, shape=(size[0], size[1]))
	ti_weight_map_stack = ti.Vector.field(size[2], ti.i32, shape=(size[0],size[1] ,n))
	ti_ldr_image_stack = ti.Vector.field(size[2], ti.i32, shape=(n,size[0],size[1]))
	ti_shutters = ti.field(ti.f32, shape=n)

	ti_ldr_image_stack.from_numpy(ldr_image_stack);
	ti_shutters.from_numpy(shutters)
	hdr_comp(n)
	return output