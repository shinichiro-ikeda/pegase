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
from .nonterminal import A
from .primitive import ParseError


#================================================================================
# Persing Expression Grammar VN
#================================================================================
class peg(A):
	def preprocessing(self):
		self.value = [v if isinstance(v,str) else v.preprocessing() for v in self.value if not isinstance(v,_Spacing)]
		return self

#--------------------------------------------------------------------------------
class _Grammar(peg):
	# Grammar <- Spacing Definition+ EndOfFile
	def evaluate(self):
		return dict([d.evaluate() for d in self.value if isinstance(d,_Definition)])

class _Definition(peg):
	# Definition <- Identifier LEFTARROW Expression
	def evaluate(self):
		return (self.value[0].evaluate()[1],('_definition',self.value[0].evaluate()[1],self.value[2].evaluate()))

class _Expression(peg):
	# Expression <- Sequence (SLASH Sequence)*
	def evaluate(self):
		return ('_prioritized_choice',*[s.evaluate() for s in self.value[::2]]) if len(self.value) > 1 else self.value[0].evaluate()

class _Sequence(peg):
	# Sequence <- Prefix*
	def evaluate(self):
		s = [s.evaluate() for s in self.value]
		return ('_sequence',*s) if len(s) > 1 else s[0]

class _Prefix(peg):
	# Prefix <- (AND / NOT)? Suffix
	def evaluate(self):
		match self.value[0]:
			case _AND():
				return ('_and_predicate',self.value[1].evaluate())
			case _NOT():
				return ('_not_predicate',self.value[1].evaluate())
			case _:
				# Just Suffix:
				return self.value[0].evaluate()

class _Suffix(peg):
	# Suffix <- Primary (QUESTION / STAR / PLUS)?
	def evaluate(self):
		if len(self.value) > 1:
			match self.value[1]:
				case _QUESTION():
					return ('_optional',self.value[0].evaluate())
				case _STAR():
					return ('_zero_or_more',self.value[0].evaluate())
				case _PLUS():
					return ('_one_or_more',self.value[0].evaluate())
				case _:
					raise ParseError(f'Unrecognized suffix: {self.value[1]}')

		return self.value[0].evaluate()

class _Primary(peg):
	# Primary <- Identifier !LEFTARROW / OPEN Expression CLOSE / Literal / Class / DOT
	def evaluate(self):
		match self.value[0]:
			case _Identifier():
				return self.value[0].evaluate()
			case _OPEN():
				assert isinstance(self.value[2],_CLOSE),'ParseError, "(" was never closed:'+str(self.value)
				return self.value[1].evaluate()
			case _Literal():
				return self.value[0].evaluate()
			case _Class():
				return self.value[0].evaluate()
			case _DOT():
				return self.value[0].evaluate()
			case _:
				raise ParseError('Unrecognized primary value: {self.value[0]}')

class _Identifier(peg):
	# Identifier <- IdentStart IdentCont* Spacing
	def preprocessing(self):
		self.value = [''.join([v if isinstance(v,str) else v.evaluate() for v in self.value if not isinstance(v,_Spacing)])]
		return self

	def evaluate(self):
		identifier = ''.join([v if isinstance(v,str) else v.evaluate() for v in self.value if not isinstance(v,_Spacing)])
		return ('_rules',identifier)

class _IdentStart(peg):
	# IdentStart <- [a-zA-Z_]
	def evaluate(self):
		return reduce(lambda x,y: x + y if isinstance(y,str) else x + y.evaluate(),self.value,'')

class _IdentCont(peg):
	# IdentCont <- IdentStart / [0-9]
	def evaluate(self):
		return reduce(lambda x,y: x + y if isinstance(y,str) else x + y.evaluate(),self.value,'')

class _Literal(peg):
	# Literal <- ['] (!['] Char)* ['] Spacing / ["] (!["] Char)* ["] Spacing
	def preprocessing(self):
		self.value = [''.join([v if isinstance(v,str) else v.evaluate() for v in self.value if not isinstance(v,_Spacing)])]
		return self

	def evaluate(self):
		return ('_literal_string',reduce(lambda x,y: x + y if isinstance(y,str) else x if isinstance(y,_Spacing) else x + y.evaluate(),self.value,''))

class _Class(peg):
	# Class <- '[' (!']' Range)* ']' Spacing
	def preprocessing(self):
		self.value = [''.join([v if isinstance(v,str) else v.evaluate() for v in self.value if not isinstance(v,_Spacing)])]
		return self

	def evaluate(self):
		return ('_character_class',reduce(lambda x,y: x + y if isinstance(y,str) else x if isinstance(y,_Spacing) else x + y.evaluate(),self.value,''))

class _Range(peg):
	# Range <- Char '-' Char / Char
	def evaluate(self):
		return reduce(lambda x,y: x + y if isinstance(y,str) else x if isinstance(y,_Spacing) else x + y.evaluate(),self.value,'')

class _Char(peg):
	# Char <- '\\' [nrt'"\[\]\\] / '\\' [0-2][0-7][0-7] / '\\' [0-7][0-7]? / !'\\' .
	def evaluate(self):
		return self.value[0]

class _LEFTARROW(peg):
	# LEFTARROW <- '<-' Spacing
	pass

class _SLASH(peg):
	# SLASH <- '/' Spacing
	pass

class _AND(peg):
	# AND <- '&' Spacing
	pass

class _NOT(peg):
	# NOT <- '!' Spacing
	pass

class _QUESTION(peg):
	# QUESTION <- '?' Spacing
	pass

class _STAR(peg):
	# STAR <- '*' Spacing
	pass

class _PLUS(peg):
	# PLUS <- '+' Spacing
	pass

class _OPEN(peg):
	# OPEN <- '(' Spacing
	pass

class _CLOSE(peg):
	# CLOSE <- ')' Spacing
	pass

class _DOT(peg):
	# DOT <- '.' Spacing
	def evaluate(self):
		return ('_any_character',self.value[0])

class _Spacing(peg):
	# Spacing <- (Space / Comment)*
	def evaluate(self):
		return reduce(lambda x,y: x + y if isinstance(y,str) else x + y.evaluate(),self.value,'')

class _Comment(peg):
	# Comment <- '#' (!EndOfLine .)* EndOfLine
	def evaluate(self):
		return reduce(lambda x,y: x + y if isinstance(y,str) else x + y.evaluate(),self.value,'')

class _Space(peg):
	# Space <- ' ' / '\t' / EndOfLine
	def evaluate(self):
		return reduce(lambda x,y: x + y if isinstance(y,str) else x + y.evaluate(),self.value,'')

class _EndOfLine(peg):
	# EndOfLine <- '\r\n' / '\n' / '\r'
	def evaluate(self):
		return reduce(lambda x,y: x + y if isinstance(y,str) else x + y.evaluate(),self.value,'')

class _EndOfFile(peg):
	# EndOfFile <- !.
	pass

#================================================================================
# Persing Expression Grammar R and eS
#================================================================================
peg_R = {
	'Grammar': ('_definition', 'Grammar', ('_sequence', ('_rules', 'Spacing'), ('_one_or_more', ('_rules', 'Definition')), ('_rules', 'EndOfFile'))),
	'Definition': ('_definition', 'Definition', ('_sequence', ('_rules', 'Identifier'), ('_rules', 'LEFTARROW'), ('_rules', 'Expression'))),
	'Expression': ('_definition', 'Expression', ('_sequence', ('_rules', 'Sequence'), ('_zero_or_more', ('_sequence', ('_rules', 'SLASH'), ('_rules', 'Sequence'))))),
	'Sequence': ('_definition', 'Sequence', ('_one_or_more', ('_rules', 'Prefix'))),
	'Prefix': ('_definition', 'Prefix', ('_sequence', ('_optional', ('_prioritized_choice', ('_rules', 'AND'), ('_rules', 'NOT'))), ('_rules', 'Suffix'))),
	'Suffix': ('_definition', 'Suffix', ('_sequence', ('_rules', 'Primary'), ('_optional', ('_prioritized_choice', ('_rules', 'QUESTION'), ('_rules', 'STAR'), ('_rules', 'PLUS'))))),
	'Primary': ('_definition', 'Primary', ('_prioritized_choice', ('_sequence', ('_rules', 'Identifier'), ('_not_predicate', ('_rules', 'LEFTARROW'))), ('_sequence', ('_rules', 'OPEN'), ('_rules', 'Expression'), ('_rules', 'CLOSE')), ('_rules', 'Literal'), ('_rules', 'Class'), ('_rules', 'DOT'))),
	'Identifier': ('_definition', 'Identifier', ('_sequence', ('_rules', 'IdentStart'), ('_zero_or_more', ('_rules', 'IdentCont')), ('_rules', 'Spacing'))),
	'IdentStart': ('_definition', 'IdentStart', ('_character_class', '[a-zA-Z_]')),
	'IdentCont': ('_definition', 'IdentCont', ('_prioritized_choice', ('_rules', 'IdentStart'), ('_character_class', '[0-9]'))),
	'Literal': ('_definition', 'Literal', ('_prioritized_choice', ('_sequence', ('_character_class', "[']"), ('_zero_or_more', ('_sequence', ('_not_predicate', ('_character_class', "[']")), ('_rules', 'Char'))), ('_character_class', "[']"), ('_rules', 'Spacing')), ('_sequence', ('_character_class', '["]'), ('_zero_or_more', ('_sequence', ('_not_predicate', ('_character_class', '["]')), ('_rules', 'Char'))), ('_character_class', '["]'), ('_rules', 'Spacing')))),
	'Class': ('_definition', 'Class', ('_sequence', ('_literal_string', "'['"), ('_zero_or_more', ('_sequence', ('_not_predicate', ('_literal_string', "']'")), ('_rules', 'Range'))), ('_literal_string', "']'"), ('_rules', 'Spacing'))),
	'Range': ('_definition', 'Range', ('_prioritized_choice', ('_sequence', ('_rules', 'Char'), ('_literal_string', "'-'"), ('_rules', 'Char')), ('_rules', 'Char'))),
	'Char': ('_definition', 'Char', ('_prioritized_choice', ('_sequence', ('_literal_string', "'\\\\'"), ('_character_class', '[nrt\'"\\[\\]\\\\]')), ('_sequence', ('_literal_string', "'\\\\'"), ('_character_class', '[0-2]'), ('_character_class', '[0-7]'), ('_character_class', '[0-7]')), ('_sequence', ('_literal_string', "'\\\\'"), ('_character_class', '[0-7]'), ('_optional', ('_character_class', '[0-7]'))), ('_sequence', ('_not_predicate', ('_literal_string', "'\\\\'")), ('_any_character', '.')))), 'LEFTARROW': ('_definition', 'LEFTARROW', ('_sequence', ('_literal_string', "'<-'"), ('_rules', 'Spacing'))),
	'SLASH': ('_definition', 'SLASH', ('_sequence', ('_literal_string', "'/'"), ('_rules', 'Spacing'))),
	'AND': ('_definition', 'AND', ('_sequence', ('_literal_string', "'&'"), ('_rules', 'Spacing'))),
	'NOT': ('_definition', 'NOT', ('_sequence', ('_literal_string', "'!'"), ('_rules', 'Spacing'))),
	'QUESTION': ('_definition', 'QUESTION', ('_sequence', ('_literal_string', "'?'"), ('_rules', 'Spacing'))),
	'STAR': ('_definition', 'STAR', ('_sequence', ('_literal_string', "'*'"), ('_rules', 'Spacing'))),
	'PLUS': ('_definition', 'PLUS', ('_sequence', ('_literal_string', "'+'"), ('_rules', 'Spacing'))),
	'OPEN': ('_definition', 'OPEN', ('_sequence', ('_literal_string', "'('"), ('_rules', 'Spacing'))),
	'CLOSE': ('_definition', 'CLOSE', ('_sequence', ('_literal_string', "')'"), ('_rules', 'Spacing'))),
	'DOT': ('_definition', 'DOT', ('_sequence', ('_literal_string', "'.'"), ('_rules', 'Spacing'))),
	'Spacing': ('_definition', 'Spacing', ('_zero_or_more', ('_prioritized_choice', ('_rules', 'Space'), ('_rules', 'Comment')))),
	'Comment': ('_definition', 'Comment', ('_sequence', ('_literal_string', "'#'"), ('_zero_or_more', ('_sequence', ('_not_predicate', ('_rules', 'EndOfLine')), ('_any_character', '.'))), ('_rules', 'EndOfLine'))),
	'Space': ('_definition', 'Space', ('_prioritized_choice', ('_literal_string', "' '"), ('_literal_string', "'\\t'"), ('_rules', 'EndOfLine'))),
	'EndOfLine': ('_definition', 'EndOfLine', ('_prioritized_choice', ('_literal_string', "'\\r\\n'"), ('_literal_string', "'\\n'"), ('_literal_string', "'\\r'"))),
	'EndOfFile': ('_definition', 'EndOfFile', ('_not_predicate', ('_any_character', '.')))
}

# EOF
