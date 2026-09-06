# Pegase
Parsing Expression Grammar Abstract Syntax Extension


# Overview
Pegase is a parsing module implemented in Python based on "Parsing Expression Grammars: A Recognition-Based Syntactic Foundation," a paper presented by Bryan Ford of the Massachusetts Institute of Technology at POPL 2004 (ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages).
The PEG paper is available at https://bford.info/pub/lang/peg/.

The Pegase grammar object (G) defines a grammar based on externally provided syntax rules and non-terminal objects, and provides functionality to perform parsing via its `parse` method.
The parsing result is constructed and output as a syntax tree composed of non-terminal objects.

When parsing syntax definitions written in PEG, you can use the PEG-compliant syntax rules and non-terminal objects built into Pegase to execute the parse and obtain the resulting syntax rules.

# Usage
A grammar object in Pegase is created by instantiating the `G` class from the `pegase` package. When creating the grammar object, you specify the following parameters: the package name (VN) defining the non-terminal symbol objects, the S-expression (R) defining the syntax rules, and the name (eS) of the S-expression serving as the starting point for parsing. If these parameters are omitted, the internal VN, R, and eS values ​​for PEG grammar parsing within the `pegase` package are used.

```
from pegase import G
PEG = G()
```

By parsing the grammar definition of a programming language (written in PEG syntax) using this PEG grammar object (PEG), you can obtain an abstract syntax tree; evaluating this tree allows you to derive the syntax rules (R) for the programming language.

As an example, we will define a language capable of performing the four basic arithmetic operations and save it as `basic-calc.peg`.

```basic-calc.peg
expr <- term (('+' / '-') term)*
term <- factor (('*' / '/') factor)*
factor <- [0-9]+ / '(' expr ')'
```

We parse this grammar definition file (basic-calc.peg) using the `parse` method of the previously created PEG grammar object, and then evaluate the resulting abstract syntax tree (AST) to obtain the syntax rules (R) of basic-calc.peg.

```
basic_ST = PEG.parse('basic-calc.peg')
basic_R = basic_ST.evaluate()
```

The evaluation logic for each node of the abstract syntax tree is implemented as a Python package, where the names of the PEG grammar's non-terminal symbols serve as class names. In the arithmetic operation example presented here, we define classes named `expr`, `term`, and `factor` to represent the non-terminal symbol objects.

Create a Python package named `basic-calc_VN.py` containing non-terminal symbol objects for a language that supports the four basic arithmetic operations.

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

A grammar object for a language supporting the four basic arithmetic operations is generated based on the non-terminal symbol object name, syntax rules, and the start symbol name; the result of the arithmetic operation is then obtained by parsing a mathematical expression using the grammar object's `parse` method and evaluating the result.

Create the main program for the four basic arithmetic operations as `basic-calc.py`.

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


The execution results are as follows.

```
$ python basic-calc.py '1+2*3/(4-5)'
-5.0
```
