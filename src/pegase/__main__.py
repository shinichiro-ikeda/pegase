#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Pegase: __main__.py
#
# Copyright © 2025 Shinichiro Ikeda
#
# This software is released under the MIT license.
# see https://opensource.org/licenses/MIT


# Description:
#   文法ファイルの構文解析を行い、構文解析式の集合Rを生成する
#   文法ファイルがPEG文法以外で記述されている場合、その文法を定義したPEG文法定義ファイルを-gパラメータを使って指定する
#   指定された引数(--parse,--evaluate,--format)に従って構文解析結果の抽象構文木ASTおよびその評価結果（GrammarがPEGの場合は構文解析式R）を表示する
#   --generateが指定された場合は構文解析式Rのソースコードを表示する
#
# Usage:
#   python -m {__package__} [-g <grammar file> [--eS <eS>] [--VN <VN>]] [--preprocessing] [--parse|--evaluate [--format]] [--elapsed] [--generate] [-v|-vv|-vvv] [--help] [-V|--version] <source>")
#
#       -g <grammar file>   PEG文法ファイルを指定 (省略した場合はPEG文法を使用)
#       --eS <eS>           構文解析の起点となる構文解析式
#       --VN <VN>           非終端記号モジュール (パッケージ内のモジュールを使用する場合は '(package-name,.module_name_VN)' のように指定する
#       --preprocessing     抽象構文木に対する事前処理(preprocessing()メソッド)の実行
#       --parse             構文解析結果(抽象構文木)の表示
#       --evaluate          抽象構文木の評価結果の表示
#       --format            フォーマットして結果表示
#       --elapsed           実行時間の表示
#       --generate          PEG文法ファイルを構文解析して結果を評価して取得される構文解析式Rのソースコードを生成
#       -v,-vv,-vvv         verbose表示
#       --help              ヘルプテキストを表示
#       -V,--version        パッケージのバージョンを表示
#       <source>            構文解析の対象となるソースファイル
#
# 使用例:
#   $ python -m pegase --parse --format epeg.peg
#   $ python -m pegase epeg.peg --generate > epeg_R.py
#   $ python -m pegase -g epeg.peg sql2016.epeg --generate > sql2016_R.py
#   $ python -m pegase -g basic-mini.peg --eS expr --VN basic-mini_VN '1+2*3/(4-5)' --evaluate
#   $ python -m pegase -g querre.peg --VN querre_VN 'select * from "a.csv"' --preprocessing --parse --format
#   $ python -m pegase -g querre.peg --VN '(querre,.querre_VN)' 'select * from "a.csv"' --preprocessing --evaluate

import json
import os
import sys
import time
from pegase import G

format_elapsed = lambda t: '{:02.0f}:{:02.0f}:{:06.3f}'.format(t//3600,(t%3600)//60,t%3600%60)


#================================================================================
if __name__ == '__main__':

	start_time =time.perf_counter()

	# パラメータ取得
	args = sys.argv[1:]

	# パラメータ取得(-V, --version)
	if '-V' in args or '--version' in args:
		# パッケージのバージョンを動的に取得して表示する
		import importlib.metadata
		package_name = "pegase"
		try:
			version = importlib.metadata.version(package_name)
			print(f"{package_name} {version}")
		except importlib.metadata.PackageNotFoundError:
			print(f"{package_name} is not installed")
		sys.exit()

	# パラメータ取得(--help)
	if '--help' in args:
		print(f"usage: python -m {__package__} [-g <grammar file> [--eS <eS>] [--VN <VN>]] [--preprocessing] [--parse|--evaluate [--format]] [--elapsed] [--generate] [-v|-vv|-vvv] [--help] [-V|--version] <source>")
		sys.exit()

	# パラメータ取得(verbose-level)
	verbose_p = ['-v','-vv','-vvv']
	verbose = max([len(v)-1 for v in verbose_p if v in args]+[0])
	args = [p for p in args if p not in verbose_p]

	# パラメータ取得(-g grammar-file)
	grammar = None
	if '-g' in args:
		_idx = [i for i,p in enumerate(args) if p == '-g'][0]
		grammar = args[_idx+1]
		args = [p for i,p in enumerate(args) if i != _idx and i != _idx + 1]

	# パラメータ取得(--eS eS)
	eS = None
	if '--eS' in args:
		if grammar is None:
			print('grammar file is not specified')
			sys.exit()
		_idx = [i for i,p in enumerate(args) if p == '--eS'][0]
		eS = args[_idx+1]
		args = [p for i,p in enumerate(args) if i != _idx and i != _idx + 1]

	# パラメータ取得(--VN VN)
	VN = None
	if '--VN' in args:
		if grammar is None:
			print('grammar file is not specified')
			sys.exit()
		_idx = [i for i,p in enumerate(args) if p == '--VN'][0]
		VN = args[_idx+1]
		args = [p for i,p in enumerate(args) if i != _idx and i != _idx + 1]
		# VNが'(package-name,.VN)'の形式で指定された場合はtupleに変換する
		if VN[0] == '(' and VN[-1] == ')':
			VN = tuple(VN[1:-1].split(','))

	# パラメータ取得(source)
	source = [p for p in args if p[0] != '-'][0]

	# 抽象構文木を取得
	if verbose > 0:
		print(f"PEG = {grammar}, eS = {eS}, VN = {VN}, source = {source}")
		print(G(VN = VN,R = None if grammar is None else G().parse(grammar).evaluate(),eS = eS))
	parse_start = time.perf_counter()
	AST = G(VN = VN,R = None if grammar is None else G().parse(grammar).evaluate(),eS = eS,verbose=verbose).parse(source)
	# same as G.grammar(grammar,eS,VN,verbose=verbose).parse(source)
	parse_end = time.perf_counter()

	# 事前処理
	if '--preprocessing' in args:
		AST = AST.preprocessing()

	# 抽象構文木をフォーマットして表示
	if '--parse' in args:
		print('---- abstract syntax tree ----')
		print(AST.format() if '--format' in args else AST)
		# 実行時間の表示
		if '--elapsed' in args:
			print('---- elapsed time ----')
			if 'parse_start' in locals():
				print('     (parse):',format_elapsed(parse_end-parse_start))
			end_time =time.perf_counter()
			print('elapsed time:',format_elapsed(end_time-start_time))
		sys.exit()

	# 抽象構文木を評価(構文解析式Rを生成)
	evaluate_start = time.perf_counter()
	R = AST.evaluate()
	evaluate_end = time.perf_counter()

	# 評価結果をフォーマットして表示
	if '--evaluate' in args:
		print('---- evaluate ----')
		print(json.dumps(R,indent=4) if '--format' in args else R)
		# 実行時間の表示
		if '--elapsed' in args:
			print('---- elapsed time ----')
			if 'parse_start' in locals():
				print('     (parse):',format_elapsed(parse_end-parse_start))
			if 'evaluate_start' in locals():
				print('  (evaluate):',format_elapsed(evaluate_end-evaluate_start))
			end_time =time.perf_counter()
			print('elapsed time:',format_elapsed(end_time-start_time))
		sys.exit()

	# 構文解析式Rのソースコードを生成
	if '--generate' in args:
		if os.path.isfile(source) and source.split('.')[-1] == 'peg':
			print(f'{os.path.splitext(os.path.basename(source))[0]}_R =','{')
			for a,e in R.items():
				print(f'\t\'{a}\': {e},')
			print('}')
		else:
			print('The <source> must specify a PEG file')
		sys.exit()

# EOF
