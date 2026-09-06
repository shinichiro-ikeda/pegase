#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Copyright © 2025 Shinichiro Ikeda
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from functools import reduce


def _format_ast(ast,indent=0):
	if len(ast.value) == 1 and isinstance(ast.value[0],str):
		result = f'{" "*indent}{ast.__class__.__name__}({repr(ast.value[0])})\n'
	else:
#		result = f'{" "*indent}{ast.__class__.__name__}(\n' + \
#				 reduce(lambda x,n: x + f'{" "*(indent+4)}{repr(n)}\n' if isinstance(n,str) else x + _format_ast(n,indent+4), [''.join(ast.value)] if len(ast.value) > 0 and all([isinstance(v,str) for v in ast.value]) else ast.value, '') + \
#				 f'{" "*indent})\n'
		result = f'{" "*indent}{ast.__class__.__name__}(\n' + \
				 reduce(lambda x,n: x + f'{" "*(indent+4)}{repr(n)}\n' if isinstance(n,str) else x + _format_ast(n,indent+4), ast.value, '') + \
				 f'{" "*indent})\n'
	return result


#================================================================================
# A Class
#================================================================================
class A:
	def __init__(self,value):
		self.value = value

	def __repr__(self):
		return f'{self.__class__.__name__}({repr(self.value)})'

	def evaluate(self):
		return reduce(lambda x,y: x + y if isinstance(y,str) else x + y.evaluate(),self.value,'')

	def format(self):
		return _format_ast(self)[:-1]

# EOF
