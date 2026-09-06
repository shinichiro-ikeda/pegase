#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Copyright © 2025 Shinichiro Ikeda
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# flatten(source [,exclude]) -- n次元の配列を1次元配列に変換する
#  - strは展開しない
#  - excludeで指定したクラスは展開しない
#  - excludeはクラス単体またはクラスのリストで指定する
# 例)
#   flatten(x)					str以外の__iter__オブジェクトを展開する
#   flatten(x,tuple)			tupleを展開対象外にする
#   flatten(x,[tuple,dict])		tuple,dictを展開対象外にする

flatten = lambda x,ts=[],f=lambda x,ts,g: [z for y in x for z in (g(y,ts,g) if hasattr(y, '__iter__') and not any([isinstance(y,t) for t in (ts+[str] if isinstance(ts,list) else [ts,str])]) else (y,))]: f(x,ts,f)
