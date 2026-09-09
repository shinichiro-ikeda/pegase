# Pegase
Parsing Expression Grammar Abstract Syntax Extension


## 概要
Pegaseは、マサチューセッツ工科大学(Massachusetts Institute of Technology)のBryan Fordが POPL 2004 (ACM SIGPLAN - SIGACT Symposium on Principles of Programming Languages)で発表したParsing Expression Grammars:
A Recognition-Based Syntactic Foundationに基づき、構文解析モジュールとしてPythonで実装したものです。
PEGの論文はhttps://bford.info/pub/lang/peg/で見ることができます。

Pegaseの文法オブジェクト(G)は、外部から与えられた構文規則(Syntax Rule)および非終端記号オブジェクト(Nonterminals)から文法(Grammar)を定義し、その文法オブジェクトのparseメソッドで構文解析を実行する機能を持ちます。
構文解析の結果は非終端記号オブジェクトによる構文解析木(Syntax Tree)として構築して出力します。

PEG文法で記述された構文定義を解析する際は、Pegase内部に用意されたPEG準拠の構文規則および非終端記号オブジェクトを用いて、構文解析の実行および解析結果の構文規則を得ることができます。


## ファイル構成

```
	LICENSE				MIT License (英語)
	LICENSE.jp			MIT License (日本語)
	README.md			本ファイル
	__init__.py			package定義ファイル
	grammar.py			文法オブジェクトクラスファイル
	primitive.py		プリミティブ処理ファイル
	peg.py				PEG文法の構文解析用VNおよびRの定義ファイル
	peg.peg				PEG文法定義ファイル(参考資料:peg.pyの元となったファイル。構文解析の実行には必要ありません)
```

## 使用方法
Pegaseの文法オブジェクトは、pegaseパッケージのGクラスのインスタンスを生成することで作成します。文法オブジェクトの生成時には、パラメータに非終端記号オブジェクトを定義したパッケージ名(VN)、構文規則を定義したS式(R)、構文解析の起点となるS式の名前(eS)を指定します。このパラメータを省略した場合、pegaseパッケージの内部に持つPEG文法解析用のVN、R、およびeSを使用します。

```
from pegase import G
PEG = G()
```

ソースコードを記述するプログラミング言語の文法定義(PEG文法で記述されたもの)を、このPEG文法オブジェクト(PEG)を用いて構文解析することで抽象構文木を取得し、それを評価することでプログラミング言語用の構文規則(R)を得ることができます。

ここでは例として、四則演算の機能を持つ言語を定義し、`basic-calc.peg`として保存します。

```basic-calc.peg
expr <- term (('+' / '-') term)*
term <- factor (('*' / '/') factor)*
factor <- [0-9]+ / '(' expr ')'
```

この文法定義ファイル(basic-calc.peg)を先ほど作成したPEG文法オブジェクトのparseメソッドを使用して解析し、解析結果の抽象構文木(ST)を評価することでbasic-calc.pegの構文規則(R)を取得します。

```
basic_ST = PEG.parse('basic-calc.peg')
basic_R = basic_ST.evaluate()
```

抽象構文木の各ノード毎の評価処理は、PEG文法の非終端記号名をクラスとしたPythonパッケージとして記述します。ここで作成する四則演算の例では、expr、term、factorのクラスを作成し、非終端記号オブジェクトとします。

四則演算の機能を持つ言語の非終端記号オブジェクトのPythonパッケージを`basic-calc_VN.py`として作成します。

```python:basic-calc_VN.py
from functools import reduce
from pegase import A

def calc(x,opcode,y):
  match opcode:
    case '+':
      return x + y
    case '-':
      return x- y
    case '*':
      return x * y
    case '/':
      return x / y

class _expr(A):
  def evaluate(self):
    return reduce(lambda x,y:calc(x,y[0],y[1].evaluate()),[('+',self.value[0])] if len(self.value) == 1 else [('+',self.value[0])] + list(zip(self.value[1::2],self.value[2::2])),0)

class _term(A):
  def evaluate(self):
    return reduce(lambda x,y:calc(x,y[0],y[1].evaluate()),[('+',self.value[0])] if len(self.value) == 1 else [('+',self.value[0])] + list(zip(self.value[1::2],self.value[2::2])),0)

class _factor(A):
  def evaluate(self):
    match self.value[0]:
      case '(':
        return self.value[1].evaluate()
      case _:
        return int(''.join(self.value))
```


非終端記号オブジェクト名、構文規則、構文解析の起点名を元に四則演算言語の文法オブジェクトを生成し、その文法オブジェクトのparseメソッドを用いて数式を解析した結果を評価することで、四則演算の結果を得ます。

四則演算のメインプログラムを`basic-calc.py`として作成します。

```python:basic-calc.py
import sys
from pegase import G

if __name__ == '__main__':
  PEG = G()
  basic_ST = PEG.parse('basic-calc.peg')
  basic_R = basic_ST.evaluate()
  basic_G = G('basic-calc_VN',basic_R,'expr')
  result = basic_G.parse(sys.argv[1]).evaluate()
  print(result)
```

実行結果は以下の通りです。

```
$ python basic-calc.py '1+2*3/(4-5)'
-5.0
```

