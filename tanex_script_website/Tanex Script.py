# tanex script

# version：1.0.0
# originator：Liu Songlan
# change time：2025/5/4
# computer environment：Windows, Linux (Not Supported Mac OS)
# pgramming language：Python 3.11.5 32-bit
# official website: http://localhost:8080/index.html?_dc=20250412
# email：2477872205@qq.com

# This project is not open source
# © 2025 Tanex Script. All rights reserved

import re
import json
from decimal import Decimal, getcontext

getcontext().prec = 1000
'''
decimal类型的处理
`0.5`+`9.99999999999999999999999999999999` -> ```py Decimal('0.5') + Decimal('9.99999999999999999999999999999999')```
'''
#print(Decimal('0.5') + Decimal('9.99999999999999999999999999999999'))

# ====================== 词法分析器 ======================
TOKEN_REGEX = [
    (r'//;.*?;//', 'MULTILINE_COMMENT'),
    (r'//.*?;', 'COMMENT'),
    (r'#.*?;', 'COMMENT'),
    (r'"(?:\\.|[^"\\])*"', 'STRING'),
    (r"'(?:\d+)'", 'INTEGER'),
    (r'`\d+\.\d+`', 'DECIMAL'),
    (r'\{', 'LBRACE'),
    (r'\}', 'RBRACE'),
    (r'\[', 'LBRACKET'),
    (r'\]', 'RBRACKET'),
    (r'<', 'LANGLE'),
    (r'>', 'RANGLE'),
    (r'\(', 'LPAREN'),
    (r'\)', 'RPAREN'),
    (r';', 'SEMI'),
    (r',', 'COMMA'),
    (r'\?\:', 'TERNARY'),
    (r'\+=|-=|\*=|/=|%=|&=|\|=|\^=', 'ASSIGN_OP'),
    (r'&&|\|\||==|!=|<=|>=|<|>', 'LOGIC_OP'),
    (r'\+|-|\*|/|%|\^|\\', 'MATH_OP'),
    (r'=', 'ASSIGN'),
    (r'a\'[0-9a-zA-Z_]+\'', 'ADDRESS'),
    (r'None', 'NONE'),
    (r'[0-9a-zA-Z_]+', 'IDENTIFIER'),
    (r'\s+', 'WHITESPACE'),
    (r'infinity', 'INFINITY'),
    (r'NaN', 'NAN')
]

class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        
    def tokenize(self):
        tokens = []
        while self.pos < len(self.code):
            match = None
            for pattern, tag in TOKEN_REGEX:
                regex = re.compile(pattern, re.DOTALL)
                match = regex.match(self.code, self.pos)
                if match:
                    value = match.group(0)
                    if tag not in ['WHITESPACE', 'COMMENT', 'MULTILINE_COMMENT']:
                        tokens.append((tag, value))
                    self.pos = match.end()
                    break
            if not match:
                raise SyntaxError(f'意外字符：{self.code[self.pos]}')
        return tokens

# ====================== 语法分析器 ======================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = None
        self.advance()
        
    def advance(self):
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
            self.pos += 1
        else:
            self.current_token = None
            
    def expect(self, tag, err_msg):
        if self.current_token and self.current_token[0] == tag:
            value = self.current_token[1]
            self.advance()
            return value
        else:
            raise SyntaxError(err_msg)
    
    def parse(self):
        ast = []
        while self.current_token:
            if self.current_token[0] == 'SEMI':
                self.advance()  # 跳过结束符
                continue
            statement = self.parse_statement()
            ast.append(statement)
        return ast
    
    def parse_statement(self):
        if self.current_token[0] == 'IDENTIFIER':
            return self.parse_function_call()
        elif self.current_token[0] == 'LBRACKET':
            return self.parse_assignment()
        elif self.current_token[0] == 'LBRACE':
            return self.parse_list_or_codeblock()
        else:
            raise SyntaxError(f"意外标记: {self.current_token[1]}")
        #             ^报错
   #     """
    #    PS C:\Users\联想\tanex script website> & D:/aaa/Python/python.exe "c:/Users/联想/tanex script website/Tanex Script.py"
     #       Traceback (most recent call last):
      #  File "c:\Users\联想\tanex script website\Tanex Script.py", line 204, in <module>
       #     ast = parser.parse()
        #        ^^^^^^^^^^^^^^
        #File "c:\Users\联想\tanex script website\Tanex Script.py", line 97, in parse
  #          statement = self.parse_statement()
   #                     ^^^^^^^^^^^^^^^^^^^^^^
    #    File "c:\Users\联想\tanex script website\Tanex Script.py", line 109, in parse_statement
     #       raise SyntaxError(f"意外标记: {self.current_token[1]}")
      #  SyntaxError: 意外标记: '1'
       # """
    
    def parse_function_call(self):
        func_name = self.expect('IDENTIFIER', "Expected function name")
        args = []
        if self.current_token and self.current_token[0] in ['LPAREN', 'STRING', 'INTEGER']:
            args = self.parse_arguments()
        return {
            "function": {
                "name": func_name,
                "arg": args[0] if len(args) == 1 else {"expression": args}
            }
        }
    
    def parse_arguments(self):
        if self.current_token[0] == 'LPAREN':
            self.advance()
            args = []
            while self.current_token and self.current_token[0] != 'RPAREN':
                arg = self.parse_expression()
                args.append(arg)
                if self.current_token[0] == 'COMMA':
                    self.advance()
            self.expect('RPAREN', "Expected ')'")
        else:
            args = [self.parse_expression()]
        return args
    
    def parse_expression(self):
        elements = {}
        while self.current_token and self.current_token[0] not in ['SEMI', 'COMMA', 'RPAREN']:
            if self.current_token[0] in ['MATH_OP', 'LOGIC_OP']:
                elements = {**elements, "symbol": self.current_token[1]}
                self.advance()
            else:
                elements = {**elements, **self.parse_primary()}
        return {"expression": elements}
    
    def parse_primary(self):
        token_type, token_value = self.current_token
        if token_type == 'STRING':
            self.advance()
            return {"string": token_value.strip('"')}
        elif token_type == 'INTEGER':
            self.advance()
            return {"integer": token_value.strip("'")}
        elif token_type == 'LBRACKET':
            return self.parse_variable()
        elif token_type == 'LBRACE':
            return self.parse_list_or_codeblock()
        elif token_type == 'IDENTIFIER':
            return self.parse_function_call()
        else:
            raise SyntaxError(f"意外的主令牌: {token_value}")
    
    def parse_variable(self):
        self.expect('LBRACKET', "Expected '['")
        var_name = self.expect('IDENTIFIER', "Expected variable name")
        self.expect('RBRACKET', "Expected ']'")
        return {"variable": var_name}
    
    def parse_assignment(self):
        var = self.parse_variable()
        self.expect('ASSIGN', "Expected '='")
        value = self.parse_expression()
        return {
            "assignment": {
                "left": var,
                "right": value
            }
        }
    
    def parse_list_or_codeblock(self):
        self.expect('LBRACE', "Expected '{'")
        items = []
        while self.current_token and self.current_token[0] != 'RBRACE':
            if self.current_token[0] == 'COMMA':
                self.advance()
                continue
            items.append(self.parse_expression())
        self.expect('RBRACE', "Expected '}'")
        return {"list": items}

# ====================== 测试验证 ======================
if __name__ == "__main__":
    test_code = '''
    output (integer "1" + integer "3");
    '1'+'1';
    '''
    lexer = Lexer(test_code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    print(json.dumps(ast, indent = 4))

# 希望的输出结果：
"""
{
"1": {
        "function": {
            "name": "output",
            "arg": {
                "expression": {
                    "function": {
                        "name": "integer",
                        "arg": {"string": "\"1\""}
                    },
                    "symbol": "+",
                    "function": {
                        "name": "integer",
                        "arg": {"string": "\"3\""}
                    }
                }
            }
        }
    },
"2": {
        "expression": {
            "integer": "'1'",
            "symbol": "+",
            "integer": "'1'"
        }
    }
# ......
}
"""

"""
tanex script的优先级
1 ()
2 name age
3 name[index]
4 name.age
5 +n -n *n /n !n
6 n*m n/m n%m n^m
7 n+m n-m
8 n<m n>m n<=m n>=m
9 n==m n!=m
10 n&&m n||m
11 n?m:p
12 n&m|p
13 n=m
14 n+=m n-=m n*=m n/=m n%=m n^=m
15 n&=m n|=m
"""

"""
tanex

我希望用python写一个编程语言解释器，tanex，可以执行代码、报错
tanex的语法：
```tanex
//每行末尾都要有结束符，如;(代码的一句话结束) ,(list);
{[a] = 1//缩进可以不加哦;
	{'1','1',
		'1'};
};
//;
//;
这是多行注释;
由2个斜杠组成;
//;
#这是注释;
```\

type：
类型                     示例                                           说明                                        写法(*为任意)
character_string   "I'm a string\n"                           可以在字符串中放很多字符         "*"
integer                '123'                                          可以在整数中放很多数字             '*'
decimal               `123.123`                                    可以在小数中放很多数字            `*.*`
list                       {'1',{'1',"1"},"1", {int "1";}}              可以在列表中放很多东西            {*,*,*...}
code                    {[a] = "12345678";output [a];}      可以在代码块中放很多代码         {*;*;*...;}
variable                [a]                                             变量名没有大限制，因为有[]包裹 [*]
boolean                <True>                                     布尔值只有<True><False>        <*>
function                include "standard"                     函数可以不带括号（后面有别的）*(*)
none                     None                                        none类型只有(None)这个值       None
address                 a1234                                       address类型以a开头,可以解地址 a*

目前我希望可以将tanex代码分解为类似ast的字典（不需要别的）

symbol:
示例            解释               ast
+n              正N                {"Unary operator":{"+":n}}
-n               负N                {"Unary operator":{'-':n}}
n+m           /                     {"symbol":"+"}
n-m             /                   {"symbol":"-"}
n/m 相当于py的n/m，不是n//m          {"symbol":"/"}
n*m            /                   {"symbol":"*"},
n%m          模                  {"symbol":"%"},
n^m      n的m次方                {"symbol":"^"}
//str//     (注释：str)          /
#str        (注释：str)            /
n[m]       n的第m项               {'subscript':{'left':n,'rihgt':m}}
n<m       /                          {"symbol":"<"}
n<=m       /                        {"symbol":"<="}
n==m        /                       {"symbol":"=="}
n>m         /                       {"symbol":">"}
n>=m      /                       {"symbol":">="}
n!=m      /                       {"symbol":"!="}
n=m    n的类型必为variable      {"assignment=":{'left':n,'rihgt':m}}
n&&m     (类似c语言)            {"symbol":"&&"}
n||m        (类似c语言)          {"symbol":"||"}
n+=m           /                  {"assignment+=":{'left':n,'rihgt':m}}
n-=m            /                  {"assignment-=":{'left':n,'rihgt':m}}
n/=m            /                  {"assignment/=":{'left':n,'rihgt':m}}
n*=m            /                  {"assignment*=":{'left':n,'rihgt':m}}
n%=m           /                  {"assignment%=":{'left':n,'rihgt':m}}
n&=m           n = n && m         {"assignment&=":{'left':n,'rihgt':m}}
n|=m             n = n || m       {"assignment|=":{'left':n,'rihgt':m}}
n^=m           n = n ^ m           {"assignment^=":{'left':n,'rihgt':m}}
n?m:p     如果n?那么m,否则p         {'if':{'if_':n,'if-y':m,'if-n':p}}
n|m&p(尝试n，error:m,否则p)        {'try':{'try_':n,'error-y':m,'error-n':p}}
n\m      相当于py的n//m            {"symbol":"\"}
*n(n为address，解地址)              {"Unary operator":{"*":n}}
/n(n为variable, 转化为address)      {"Unary operator":{"/":n}}
n.m(库访问（如py.print()(实际没有这个函数)）) {".":{'left':n,'rihgt':m}}
$ (tanex系统处理特殊符号(需要处理))        ???
"""