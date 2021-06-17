from numpy.core.fromnumeric import shape
import taichi as ti
from taichi.core.util import in_docker
from taichi.lang.ops import exp, log, max

low_img = None
nml_img = None
high_img = None
output = None

Zmin = 0.05 * 65535
Zmax = 0.95 * 65535

K = 0.15
B = 0.95

@ti.func
def w_uniform(z)->ti.Vector:
	res = ti.Vector([0,0,0])
	res[0] = 1 if z[0] >= Zmin and z[0] <= Zmax else 0
	res[1] = 1 if z[1] >= Zmin and z[1] <= Zmax else 0
	res[2] = 1 if z[2] >= Zmin and z[2] <= Zmax else 0
	return res

@ti.func
def gaussian(x:ti.f32)->ti.f32:
	return ti.exp(-4.0 * ((x-0.5)**2)/0.25)

@ti.func
def w_gaussian(z)->ti.Vector:
	res = ti.Vector([0.0,0.0,0.0])
	res[0] = gaussian(z[0]/65535.0) if z[0] >= Zmin and z[0] <= Zmax else 0.0
	res[1] = gaussian(z[1]/65535.0) if z[1] >= Zmin and z[1] <= Zmax else 0.0
	res[2] = gaussian(z[2]/65535.0) if z[2] >= Zmin and z[2] <= Zmax else 0.0
	return res

@ti.func
def w(z):
	# return w_uniform(z)
	# return w_gaussian(z)
	return ti.Vector([1.0, 1.0, 1.0])

@ti.func
def sum_of_weighted_intensity(i,j)->ti.f32:
	return w(low_img[i,j]) + w(nml_img[i,j]) + w(high_img[i,j])

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
		de = sum_of_weighted_intensity(i, j)
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
		no = sum_of_weighted_radiance_linear(i, j, t1,t2,t3)
		de = sum_of_weighted_intensity(i, j)
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
def geometric_mean(image)->ti.f32:
	sum = ti.Vector([0.0, 0.0, 0.0])
	for i,j in image:
		sum += ti.log(image[i, j] + 1.0)
	sum /= (image.shape[0] * image.shape[1] * 1.0)
	return ti.exp(sum)

@ti.kernel
def hdr_comp(ind: ti.template(), t1:float, t2:float, t3:float):
	# composition
	log_hdr(output,t1,t2,t3)
	# linear_hdr(output,t1,t2,t3)

	# tone mapping
	gm = geometric_mean(output)
	mi = max_intensity(output)
	print(gm, mi)

	for i, j in output:
		i_hdr_bar = K/gm * output[i,j]
		output[i, j] = (i_hdr_bar * (1 + i_hdr_bar/(mi**2)))/(1 + i_hdr_bar) * 255

def pipeline(nml, low, high, size):
	ti.init(arch=ti.gpu)
	global low_img, nml_img, high_img, output, img_arr

	frame = len(nml)
	img_arr = [None for i in range(10)]
	low_img = ti.Vector.field(size[2], ti.i32, shape=(size[0],size[1]))
	nml_img = ti.Vector.field(size[2], ti.i32, shape=(size[0],size[1]))
	high_img = ti.Vector.field(size[2], ti.i32, shape=(size[0],size[1]))
	output = ti.Vector.field(size[2], ti.i32, shape=(size[0], size[1]))
	output_imgs = []

	for ind in range(frame):
		low_img.from_numpy(low[ind][1])
		nml_img.from_numpy(nml[ind][1])
		high_img.from_numpy(high[ind][1])
		hdr_comp(frame, low[ind][0]['shutter'] * 0.1, nml[ind][0]['shutter'] * 0.1,high[ind][0]['shutter'] * 0.1)
		res = output.to_numpy()
		output_imgs.append(res)

	return output_imgs