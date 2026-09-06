#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Copyright © 2025 Shinichiro Ikeda
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import re
from functools import reduce
from enum import IntEnum


#================================================================================
# Exceptions
#================================================================================

# Base class for exceptions
class Error(Exception):
	def __init__(self,*p):
		# 例外発生時の例外名からパッケージ名を除く
		# pegase.primitive.Error -> pegase.Error
		self.__class__.__module__ = __package__

# DefinitionError(message [,left_recursion])
class DefinitionError(Error):
	def __str__(self):
		if self.args[0] == 'left recursion detected':
			recursions = self.args[1]
			for A,r in recursions.items():
				self.add_note(f'  {A}: {r}')
		return self.args[0]


# ParseError(message [,Stream])
class ParseError(Error):
	def __str__(self):
		if len(self.args) >= 2 and isinstance(self.args[1],Stream):
			s = self.args[1]
			start = s._stream[:max(s._stream[:s._hwm].rfind('\n'),0)].rfind('\n')+1
			end = len(s._stream) if s._stream[s._hwm:].find('\n') < 0 else s._hwm+s._stream[s._hwm:].find('\n')
			linepos = s._hwm - 1 - s._stream[:s._hwm].rfind('\n')
			s_no = len(re.findall('\n',s._stream[:start]))+1
			e_no = len(re.findall('\n',s._stream[:s._hwm]))+1
			self.add_note(f'Syntax error around line {s_no if s_no == e_no else str(s_no)+" to "+str(e_no)}:')
			self.add_note(f'{s._stream[start:end]}')
			self.add_note(f'{" "*linepos}^')
		return self.args[0]


#================================================================================
# Verbose Level
#================================================================================
class Verbose(IntEnum):
	SILENT = 0
	PROGRESS = 1
	MUMBLE = 2
	DEBUG = 3


#================================================================================
# Constructing Operators
#================================================================================

#----------------------------------------
# ε			Empty String
#----------------------------------------
def _empty_string():
	def _(s):
#DEBUG
		if s.G.verbose >= Verbose.DEBUG:
			print(f'  - _empty_string')
		return ''
	return _

#----------------------------------------
# ' '		Literal String
# " "		Literal String
#----------------------------------------
def _literal_string(pattern):
	assert len(pattern) > 2 and ((pattern[0] == "'" and pattern[-1] == "'") or (pattern[0] == '"' and pattern[-1] == '"')), '_literal_string pattern must be enclosed in quotes or double quotes:'+str(pattern)
	pattern = pattern.replace('\\n','\n').replace('\\r','\r').replace('\\t','\t').replace("\\'","'").replace('\\"','"').replace('\\[','[').replace('\\]',']').replace('\\\\','\\')
	def _(s):
		result = None
		if s.stream()[:len(pattern[1:-1])] == pattern[1:-1]:
			result = s.stream()[:len(pattern[1:-1])]
			s.forward(len(pattern[1:-1]))
#DEBUG
			if s.G.verbose >= Verbose.DEBUG:
				print(f'  * _literal_string      : stream:{repr(result)} length:{len(pattern[1:-1])} pattern:{repr(pattern)}')
		else:
			if s.G.verbose >= Verbose.DEBUG:
				print(f'    _literal_string      : stream:{repr(s.stream()[:10])} length:{len(pattern[1:-1])} pattern:{repr(pattern)}')
		return result
	return _

#----------------------------------------
# [ ]		Character Class
#----------------------------------------
def _character_class(pattern):
	assert len(pattern) > 2 and pattern[0] == '[' and pattern[-1] == ']', '_character_class pattern should be enclosed in "[" and "]":'+str(pattern)
	p = re.compile(pattern)
	def _(s):
		result = None
		m = p.match(s.stream())
		if m:
			s.forward(m.end())
			result = [m.group()]
#DEBUG
			if s.G.verbose >= Verbose.DEBUG:
				print(f'  * _characger_class     : stream:{repr(result)} length:{len(pattern)} pattern:{repr(pattern)}')
		else:
			if s.G.verbose >= Verbose.DEBUG:
				print(f'    _character_class     : stream:{repr(s.stream()[:10])} length:{len(pattern)} pattern:{repr(pattern)}')
		return result
	return _

#----------------------------------------
# .			Any Character
#----------------------------------------
def _any_character(pattern):
	assert pattern == '.', '_any_character pattern should be ".":'+str(pattern)
	def _(s):
		result = None
		if len(s.stream()) > 0:
			result = [s.stream()[0]]
			s.forward(1)
			if s.G.verbose >= Verbose.DEBUG:
				print(f'  * _any_character       : stream:{repr(result)} length:{len(pattern)} pattern:{repr(pattern)}')
		else:
			if s.G.verbose >= Verbose.DEBUG:
				print(f'    _any_character       : stream:{repr(s.stream()[:10])} length:{len(pattern)} pattern:{repr(pattern)}')
		return result
	return _

#----------------------------------------
# e?		Optional
#----------------------------------------
def _optional(e):
	def _(s):
#DEBUG
		if s.G.verbose >= Verbose.DEBUG:
			print(f'  - _optional')
		x = e(s)
		return x or []
	return _

#----------------------------------------
# e*		Zero-or-more
#----------------------------------------
def _zero_or_more(e):
	def _(s):
#DEBUG
		if s.G.verbose >= Verbose.DEBUG:
			print(f'  - _zero_or_more')
		result = []
		while True:
			x = e(s)
			if x is None:
				break
			else:
				result += x
		return result
	return _

#----------------------------------------
# e+		One-or-more
#----------------------------------------
def _one_or_more(e):
	def _(s):
#DEBUG
		if s.G.verbose >= Verbose.DEBUG:
			print(f'  - _one_or_more')
		result = []
		while True:
			x = e(s)
			if x is None:
				break
			else:
				result += x
		return result if len(result) > 0 else None
	return _

#----------------------------------------
# &e		And-redicate
#----------------------------------------
def _and_predicate(e):
	def _(s):
#DEBUG
		i = s.cursor()
		if s.G.verbose >= Verbose.DEBUG:
			print(f'&   _and_predicate       : at {i}')
		x = e(s)
		if x is None:
			result = None
		else:
			result = []
		s.backtracking(i)
		if s.G.verbose >= Verbose.DEBUG:
			print(f'<&  _and_predicate       : result = {result}, backtracing to {i} stream:{repr(s._stream[i:i+10])}')
		return result
	return _

#----------------------------------------
# !e		Not-predicate
#----------------------------------------
def _not_predicate(e):
	def _(s):
#DEBUG
		i = s.cursor()
		if s.G.verbose >= Verbose.DEBUG:
			print(f'!   _not_predicate       : at {i}')
		x = e(s)
		if x is None:
			result = []
		else:
			result = None
		s.backtracking(i)
		if s.G.verbose >= Verbose.DEBUG:
			print(f'<!  _not_predicate       : result = {result}, backtracing to {i} stream:{repr(s._stream[i:i+10])}')
		return result
	return _

#----------------------------------------
# e1 e2		Sequence
#----------------------------------------
def _sequence(*es):
#DEBUG
#	print('*** _sequence *es:',*es)
	def _(s):
#DEBUG
		result = []
		i = s.cursor()
		if s.G.verbose >= Verbose.DEBUG:
			print(f'.   _sequence   _        : at {i} ',['e'+str(i+1) for i,_ in enumerate(es)])
		for e in es:
			x = e(s)
			if x is None:
				result = None
				s.backtracking(i)
				if s.G.verbose >= Verbose.DEBUG:
					print(f'<   _sequence            : backtracing to {i} stream:{repr(s._stream[i:i+10])}')
				break
			else:
				result += x
#		if s.G.verbose >= Verbose.MUMBLE:
#			if result is None:
#				print(f'<   _sequence            : backtracing to {i} stream:{repr(s._stream[i:i+10])}')
#			elif len(result) == 0:
#				print(f'    _sequence     result :', result)
#			else:
#				print(f'    _sequence     result :', reduce(lambda x,y: x[:-1] + [''.join([x[-1],y])] if isinstance(x[-1],str) and isinstance(y,str) else x + [y], result[1:], [result[0]]))
		return result if result is None or len(result) == 0 else reduce(lambda x,y: x[:-1] + [''.join([x[-1],y])] if isinstance(x[-1],str) and isinstance(y,str) else x + [y], result[1:], [result[0]])
	return _

#----------------------------------------
# e1 / e2	Prioritized Choice
#----------------------------------------
def _prioritized_choice(*es):
#DEBUG
#	print('*** _prioritized_choice *es:',*es)
	def _(s):
#DEBUG
		if s.G.verbose >= Verbose.DEBUG:
			print(f'  - _prioritized_choice  :',['e'+str(i+1) for i,_ in enumerate(es)])
		result = None
		i = s.cursor()
		for e in es:
			x = e(s)
			if x is None:
				pass
			else:
				result = x
				break
		return result
	return _

#----------------------------------------
# A <- e	Definition
#----------------------------------------
def _definition(A,e,ex):
#DEBUG
#	print('*** _definition A <- e:',A,e)
	_A = '_' + A
	def _(s):
#DEBUG
		if s.G.verbose >= Verbose.DEBUG:
			print(f'    _definition _ A <- e : {A} <- {ex}')
		x = e(s)
		if _A not in s.G.VN:
			# VNにAが定義されていない場合、Aのクラス定義を生成してVNに登録する
			s.G.VN[_A] = type(_A,s.G.parent,{})
#VERBOSE
		if x is not None and s.G.verbose >= Verbose.MUMBLE:
			print(f' ** _definition _ A <- e : {A} <- {x}')
		return x if x is None else [s.G.VN[_A](x)]
	return _

#----------------------------------------
# R(A)		Rules
#----------------------------------------
def _rules(A):
#	print('*** _rules A:',A)
	def _(s):
#DEBUG
		if s.G.verbose >= Verbose.MUMBLE:
			print(f'  - _rules      _ A      : {A}')
		return s.G.R[A](s)
	return _

#================================================================================
# "readable rules" to expressions conversion
#================================================================================
def _expression(expr):
	f,*p = expr
	match f:
		case '_empty_string':
			x = _empty_string()
		case '_literal_string':
			x = _literal_string(*p)
		case '_character_class':
			x = _character_class(*p)
		case '_any_character':
			x = _any_character(*p)
		case '_optional':
			x = _optional(_expression(*p))
		case '_zero_or_more':
			x = _zero_or_more(_expression(*p))
		case '_one_or_more':
			x = _one_or_more(_expression(*p))
		case '_and_predicate':
			x = _and_predicate(_expression(*p))
		case '_not_predicate':
			x = _not_predicate(_expression(*p))
		case '_sequence':
			x = _sequence(*[_expression(e) for e in p])
		case '_prioritized_choice':
			x = _prioritized_choice(*[_expression(e) for e in p])
		case '_definition':
			A,e = p
			x = _definition(A,_expression(e),e)
		case '_rules':
			x = _rules(*p)
		case _:
			raise DefinitionError(f'Unrecognized primitive: {f}')
	return x

#================================================================================
# Stream Class
#================================================================================
class Stream:
	def __init__(self,stream,G):
		self._stream = stream
		self._cursor = 0
		self._hwm = 0
		self.G = G

	def __repr__(self):
		return "{1}.{0.__class__.__name__}({0._stream})".format(self,__package__)

	def stream(self):
		return self._stream[self._cursor:]

	def cursor(self):
		return self._cursor

	def forward(self,i):
		self._cursor += i
		self._hwm = max(self._cursor,self._hwm)

	def backtracking(self,i):
		self._cursor = i

# EOF
