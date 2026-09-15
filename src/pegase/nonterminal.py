#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Querre: nonterminal.py
#
# Copyright © 2025 Shinichiro Ikeda
#
# This software is released under the MIT license.
# see https://opensource.org/licenses/MIT


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
