from numpy.core.fromnumeric import shape
import taichi as ti

low_img = None
nml_img = None
high_img = None
output = None

img_arr = []

@ti.kernel
def hdr_comp(ind: ti.template()):
	a = img_arr[ind]
	for i, j in output:
		output[i, j] = (low_img[i,j] + nml_img[i,j] + high_img[i, j])/3.0

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
		hdr_comp(frame)
		res = output.to_numpy()
		output_imgs.append(res)

	return output_imgs