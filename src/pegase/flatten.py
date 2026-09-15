#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Pegase: flatten.py
#
# Copyright © 2025 Shinichiro Ikeda
#
# This software is released under the MIT license.
# see https://opensource.org/licenses/MIT


# flatten(source [,exclude]) -- n次元の配列を1次元配列に変換する
#  - strは展開しない
#  - excludeで指定したクラスは展開しない
#  - excludeはクラス単体またはクラスのリストで指定する
# 例)
#   flatten(x)					str以外の__iter__オブジェクトを展開する
#   flatten(x,tuple)			tupleを展開対象外にする
#   flatten(x,[tuple,dict])		tuple,dictを展開対象外にする

flatten = lambda x,ts=[],f=lambda x,ts,g: [z for y in x for z in (g(y,ts,g) if hasattr(y, '__iter__') and not any([isinstance(y,t) for t in (ts+[str] if isinstance(ts,list) else [ts,str])]) else (y,))]: f(x,ts,f)
