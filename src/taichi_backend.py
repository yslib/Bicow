from numpy.core.fromnumeric import shape
from numpy.lib.ufunclike import isneginf
import taichi as ti
from taichi.core.util import in_docker
from taichi.lang.ops import exp, log, max
import numpy as np
import imageio

low_img = None
nml_img = None
high_img = None
output = None
w1_img = None
w2_img = None
w3_img = None

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
def sum_of_weight(i,j):
	res = w(low_img[i,j]) + w(nml_img[i,j]) + w(high_img[i,j])
	return res

@ti.func
def sum_of_weighted_radiance_log(i, j, t1:ti.f32, t2:ti.f32, t3:ti.f32):
	val1 = low_img[i, j]
	val2 = nml_img[i, j]
	val3 = high_img[i, j]
	a = w(val1) * (ti.log(val1) - ti.log(t1)) + w(val2) * (ti.log(val2) - ti.log(t2)) + w(val3) * (ti.log(val3) - ti.log(t3))
	return a

@ti.func
def sum_of_weighted_radiance_linear(i, j, t1,t2,t3):
	val1 = low_img[i, j] + 1
	val2 = nml_img[i, j] + 1
	val3 = high_img[i, j] + 1
	a = w(val1) * (val1/t1) + w(val2) * (val2/t2) + w(val3) * (val3/t3)
	return a

@ti.func
def log_hdr(output, t1,t2,t3):
	for i,j in output:
		no = sum_of_weighted_radiance_log(i, j, t1,t2,t3)
		de = sum_of_weight(i, j)
		output[i,j] = ti.exp(no / de)
		if any(de == 0):
			if de[0] == 0:
				output[i, j][0] = 0
			if de[1] == 0:
				output[i, j][1] = 0
			if de[2] == 0:
				output[i, j][2] = 0

@ti.func
def linear_hdr(output, t1,t2,t3):
	for i,j in output:
		no = sum_of_weighted_radiance_linear(i, j, t1, t2, t3)
		de = sum_of_weight(i, j)
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
		res = max(res, image[i, j])
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
		res = max(res,image[i,j])
	return res


@ti.kernel
def hdr_comp(ind: ti.template(), t1:float, t2:float, t3:float):
	# composition
	# log_hdr(output,t1,t2,t3)
	linear_hdr(output,t1,t2,t3)

	# debug, generate weight map
	for i,j in output:
		w1_img[i,j] = w(low_img[i, j]) * 255
		w2_img[i,j] = w(nml_img[i, j]) * 255
		w3_img[i,j] = w(high_img[i, j]) * 255

	# tone mapping
	gm = geometric_mean(output)
	mi = max_intensity(output)
	print(gm, mi)

	for i, j in output:
		scaled = (output[i,j]/gm) *K
		# output[i, j] = (scaled * (1.0 + scaled/(mi**2)))/(1.0 + scaled) * 255.0
		output[i, j] = scaled/(1.0+scaled) * 255.0

def pipeline(nml, low, high, size):
	ti.init(arch=ti.gpu)
	global low_img, nml_img, high_img, output, w1_img, w2_img, w3_img

	frame = len(nml)
	low_img = ti.Vector.field(size[2], ti.i32, shape=(size[0],size[1]))
	nml_img = ti.Vector.field(size[2], ti.i32, shape=(size[0],size[1]))
	high_img = ti.Vector.field(size[2], ti.i32, shape=(size[0],size[1]))
	w1_img = ti.Vector.field(size[2], ti.i32, shape=(size[0],size[1]))
	w2_img = ti.Vector.field(size[2], ti.i32, shape=(size[0],size[1]))
	w3_img = ti.Vector.field(size[2], ti.i32, shape=(size[0],size[1]))

	output = ti.Vector.field(size[2], ti.i32, shape=(size[0], size[1]))

	output_imgs = []

	for ind in range(frame):
		low_img.from_numpy(low[ind][1])
		nml_img.from_numpy(nml[ind][1])
		high_img.from_numpy(high[ind][1])
		hdr_comp(frame, low[ind][0]['shutter'] * 1, nml[ind][0]['shutter'] * 1,high[ind][0]['shutter'] * 1)
		res = output.to_numpy()
		output_imgs.append(res)
		imageio.imsave("w1_map.jpeg", w1_img.to_numpy())
		imageio.imsave("w2_map.jpeg", w2_img.to_numpy())
		imageio.imsave("w3_map.jpeg", w3_img.to_numpy())

	return output_imgs