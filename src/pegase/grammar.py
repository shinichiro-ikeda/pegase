#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Copyright © 2025 Shinichiro Ikeda
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import importlib
import inspect
import os
import re
import sys
from functools import reduce

from .nonterminal import A
from .peg import peg_R
from .primitive import Stream,_expression,DefinitionError,ParseError
from .flatten import flatten


# Definition
#   G = (VN,VT,R,eS)
#   A ∈ VN
#   a ∈ VT
#   r ∈ R, A <- e ∈ R
#   e = R[A]

# Usage:
#	PEG = G()
#	target_R = PEG.parse('target.peg').evaluate()
#	target_eS = 'TargetStartExpr'
#	result = G(target_VN,target_R,target_eS).parse('source-file')

#	from pegase import G
#	querre_VN = 'querre_VN'
#	querre_eS = 'direct_SQL_statement'
#	result = G(querre_VN,G().parse('querre.peg').evaluate(),querre_eS).parse('select * from "a.csv";').evaluate()


#	PEG = G()
#	ebnf_VN = 'ebnf_VN'
#	ebnf_R = PEG.parse('ebnf.peg').evaluate()
#	ebnf_eS = 'Grammar'
#	querre_VN = 'querre_VN'
#	querre_R = G(ebnf_VN,ebnf_R,ebnf_eS).parse('querre.ebnf').evaluate()
#	querre_eS = 'direct_SQL_statement'
#	result = G(querre_VN,querre_R,querre_eS).parse('select * from "a.csv";').evaluate()

#	result = G('querre_VN',G('ebnf_VN',G().parse('ebnf.peg').evaluate(),'Grammar').parse('querre.ebnf').evaluate(),'direct_SQL_statement').parse('select * from "a.csv";').evaluate()


#	G.grammar(pegfile,eS,VN) コンストラクタ使用
#	result = G.grammar('querre.peg','direct_SQL_statement','querre_VN').parse('select * from "a.csv";').evaluate()


#================================================================================
# G Class
# parameters:
#	VN		A ∈ VN			Aをクラスとして実装したVNモジュール (省略した場合はpeg_VNを使用)
#							パッケージから呼び出す場合は('package','.module')のようにtupleで指定する (モジュール名は相対表示)
#	R		A <- e ∈ R		解析ルール(A <- e)の一覧を{'A':e}として実装したdict (省略した場合はpeg_Rを使用)
#	eS		e = R(A)		解析を開始するexpressionをAとして指定 (省略した場合はpeg_VN.Grammarを使用)
#================================================================================
class G:
	def __init__(self,VN=None,R=None,eS=None,verbose=0):
		R = R or peg_R
		# eSが指定されなかった場合はRに定義された最初の項目をeSとして使用する
		eS = eS or list(R.keys())[0]
		self.verbose = verbose
#		# verboseが0の場合はtracebackを表示しない
#		if self.verbose == 0:
#			sys.tracebacklimit=0
		# モジュールVNに定義されているクラス一覧をdictとして取得
		self.VN = dict(inspect.getmembers(importlib.import_module('.peg',package=__package__) if VN is None else (importlib.import_module(VN[1],package=VN[0]) if isinstance(VN,tuple) else importlib.import_module(VN)),inspect.isclass))
		parent_VN = 'peg' if VN is None else (VN[1].split('.')[-1] if isinstance(VN,tuple) else VN)
		self.parent = (self.VN[parent_VN],) if parent_VN in self.VN else (A,)
		self.R = {A:_expression(e) for A,e in R.items()}
		self.eS = eS
		if self.eS not in self.R.keys():
			raise DefinitionError(f'eS not defined in R: {self.eS}')

		# ----------------------------
		# 未定義の非終端記号参照の検出
		# ----------------------------
		nonterminals = list(R.keys())

		rules = list(set(flatten(
			reduce(
				lambda rules,definition:
					rules + (
						lambda expr,
							   f=lambda ex,g: [ex[1]] if ex[0] == '_rules' else [g(e,g) for e in ex[1:] if e[0] in ['_optional','_zero_or_more','_one_or_more','_and_predicate','_not_predicate','_sequence','_prioritized_choice','_rules']]
						: f(expr,f)
					)(definition[2]),
					R.values(),
					[]
			)
		))) + [eS]

		unused_rules = sorted(set(nonterminals) - set(rules))
		if len(unused_rules) > 0 and self.verbose > 0:
			print(f'WARNING: Unuse rules detected: {unused_rules}')

		undefined_rules = sorted(set(rules) - set(nonterminals))
		if len(undefined_rules) > 0:
			raise ParseError(f'Undefined rules detected: {undefined_rules}')
#		if len(undefined_rules) > 0 and self.verbose > 0:
#			print(f'WARNING: Undefined rules detected: {undefined_rules}')

		# --------------------
		# left recursionの検出
		# --------------------
		# 各ルール毎に最初の_rulesプリミティブを抽出(最初が終端記号の場合を除く)
		leading_rules = {definition[1]: flatten((lambda expr,f=lambda ex,g:
											# sequenceはe1のみ抽出対象とする
											[] if ex[0] in ['_empty_string','_literal_string','_character_class','_any_character'] else
											[ex[1]] if ex[0] == '_rules' else
											[g(e,g) for e in ex[1:] if e[0] in ['_optional','_zero_or_more','_one_or_more','_and_predicate','_not_predicate','_sequence','_prioritized_choice','_rules']] if ex[0] == '_prioritized_choice' else
											[g(e,g) for e in [ex[1]] if e[0] in ['_optional','_zero_or_more','_one_or_more','_and_predicate','_not_predicate','_sequence','_prioritized_choice','_rules']]
										: f(expr,f)
				    	)(definition[2]))
						for definition in R.values()
		}
		# 自分の配下で自分を呼び出す定義を左再帰として検出
		left_recursions = {A:e for A,e in 
			{A: flatten(
					(lambda A,e,f=lambda A,a,ex,g: [g(A+[e],e,leading_rules[e],g) if e in leading_rules and e not in A else (f'{a} <- {e}' if e == A[0] else []) for e in ex]: f([A],None,e,f))(A,e)
				) for A,e in leading_rules.items()
			}.items()
			if len(e) > 0
		}
		if len(left_recursions) > 0:
			raise DefinitionError(f'left recursion detected',left_recursions)

	def __repr__(self):
		return '{1}.{0.__class__.__name__}(\n  VN = {2},\n  R = {3},\n  eS = {4}\n)'.format(self,__package__,list(self.VN.keys()),list(self.R.keys()),self.eS)

	def parse(self,src,forcefile=False):
		if os.path.isfile(src):
			with open(src,'r') as f:
				stream = f.read()
		elif forcefile:
			raise ParseError(f'File not found: {src}')
		else:
			stream = src

		s = Stream(stream,self)
		# eSと!.のsequenceを作成して実行する
		parsed = _expression(('_sequence',('_rules',self.eS),('_not_predicate',('_any_character','.'))))(s)

		if parsed is None:
			raise ParseError('Parse error detected at line #{}: {}'.format(len(re.findall('\n',s._stream[:s._hwm]))+1,s._stream[s._stream[:s._hwm].rfind('\n')+1:s._hwm]),s)

		return parsed[0]


	# G.grammar(pegfile,eS,VN) コンストラクタ
	@classmethod
	def grammar(cls,pegfile,eS=None,VN=None,verbose=0):
		return cls(VN,G().parse(pegfile,forcefile=True).evaluate(),eS,verbose=verbose)

# EOF
