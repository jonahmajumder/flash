from inspect import stack
import os, sys

def testfn():
	l = len(stack())
	print l
	print stack()[0]
	print stack()[l-1]
	if l<5:
		testfn()

print os.path.dirname(os.path.abspath(__file__))
