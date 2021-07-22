from typing import Dict, List
import sys, getopt
import json

def parse_args(argv:List[str])->Dict[str, str]:
	try:
		opts, args = getopt.getopt(argv,'id',["cfg="])
	except getopt.GetoptError:
		print('opts error')
		sys.exit(-1)

	param = {}
	for opt, arg in opts:
		if opt == '-i':
			param['interactive_window'] = True
			if opt == '-d':
				param['detail_window'] = True
		if opt in ('--cfg', ):
			with open(arg, 'r') as jf:
				param['cfg'] =json.load(jf)
	return param