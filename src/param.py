from typing import Dict, List
import sys, getopt
import json

def parse_args(argv:List[str])->Dict[str, str]:
	try:
		opts, args = getopt.getopt(argv,'i:o',["json"])
	except getopt.GetoptError:
		print('opts error')
		sys.exit(-1)

	param = {}
	for opt, arg in opts:
		if opt == '-i':
			param['file'] = arg
		if opt in ('--json', ):
			with open(arg, 'r') as jf:
				param =json.load(jf)
			break
	return param