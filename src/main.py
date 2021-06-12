from typing import Dict, List
import cv2 as cv
import numpy as np
import sys
import param

def main(argv:List[str])->None:
	param_dict = param.parse_args(argv)
	print(param_dict)
	if param_dict.get('file', None) is None:
		print('No input image file')
		sys.exit(-1)

	img = cv.imread(param_dict['file'], cv.IMREAD_UNCHANGED)
	"""
	IMREAD_UNCHANGED
	IMREAD_GRAYSCALE
	IMREAD_COLOR
	IMREAD_ANYDEPTH
	IMREAD_ANYCOLOR
	"""
	print(img.shape,img.dtype,img.min(),img.max())

if __name__ == '__main__':
	main(sys.argv)