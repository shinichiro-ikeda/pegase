#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Copyright © 2025 Shinichiro Ikeda
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Description:
#   文法ファイルの構文解析を行い、構文解析式の集合Rを生成する
#   文法ファイルがPEG文法以外で記述されている場合、その文法を定義したPEG文法定義ファイルを-gパラメータを使って指定する
#
# Usage:
#   $ python pegase_gen_R.py [-g PEG文法定義ファイル] 文法ファイル > generated_R.py
#
# 使用例:
#   $ python pegase_gen_R.py epeg.peg > epeg_R.py
#   $ python pegase_gen_R.py sql1992.peg > sql1992_R.py
#   $ python pegase_gen_R.py -g epeg.peg sql2016.epeg > sql2016_R.py

import os
import sys
from pegase import G


#================================================================================
if __name__ == '__main__':

	# パラメータ取得
	args = sys.argv[1:]

	# パラメータ取得(grammar)
	grammar = None
	if '-g' in args:
		_idx = [i for i,p in enumerate(args) if p == '-g'][0]
		grammar = args[_idx+1]
		args = [p for i,p in enumerate(args) if i != _idx and i != _idx + 1]

	# パラメータ取得(verbose)
	verbose = 0
	if '-v' in args:
		_idx = [i for i,p in enumerate(args) if p == '-v'][0]
		verbose = int([args[_idx+1]][0])
		args = [p for i,p in enumerate(args) if i != _idx and i != _idx + 1]

	# パラメータ取得(pegfile)
	pegfile = [p for p in args if p[0] != '-' and os.path.isfile(p)][0]

	# 抽象構文木を取得
	AST = G(R = None if grammar is None else G().parse(grammar).evaluate(),verbose=verbose).parse(pegfile)

	# 構文解析式Rを生成
	R = AST.evaluate()
	print(f'{os.path.splitext(os.path.basename(pegfile))[0]}_R =','{')
	for a,e in R.items():
		print(f'\t\'{a}\': {e},')
	print('}')

# EOF
