import re
import json
from decimal import Decimal, getcontext

getcontext().prec = 1000
'''
decimal类型的处理
`0.5`+`9.99999999999999999999999999999999` -> ```py Decimal('0.5') + Decimal('9.99999999999999999999999999999999')```
'''
print(Decimal('0.5') + Decimal('9.99999999999999999999999999999999'))
# ====================== 词法分析器 ======================
TOKEN_REGEX = [
    (r'//;.*?;//', 'MULTILINE_COMMENT'),
    (r'//.*?;', 'COMMENT'),
    (r'#.*?;', 'COMMENT'),
    (r'"(\\"|[^"])*"', 'STRING'),  # 保留完整双引号
    (r'\[.*?\]', 'VARIABLE'),      # 变量标记
    (r"'\d+'", 'INTEGER'),         # 整数
    (r'`\d+\.\d+`', 'DECIMAL'),    # 小数
    (r'\+=|-=|\*=|/=|%=|&=|\|=|\^=', 'ASSIGN_OP'),
    (r'&&|\|\||==|!=|<=|>=|<|>|\?|\:|\.', 'LOGIC_OP'),
    (r'\+\+|--|\+|-|\*|/|%|\^|\\|!|~', 'MATH_OP'),
    (r'\{', 'LBRACE'),
    (r'\}', 'RBRACE'),
    (r'\[', 'LBRACKET'),
    (r'\]', 'RBRACKET'),
    (r'\(', 'LPAREN'),
    (r'\)', 'RPAREN'),
    (r';', 'SEMI'),
    (r',', 'COMMA'),
    (r'=', 'ASSIGN'),
    (r'a[0-9a-zA-Z_]+', 'ADDRESS'),
    (r'None', 'NONE'),
    (r'[0-9a-zA-Z_]+', 'IDENTIFIER'),
    (r'\s+', 'WHITESPACE'),
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
                regex = re.compile(pattern)
                match = regex.match(self.code, self.pos)
                if match:
                    value = match.group(0)
                    if tag not in ['WHITESPACE', 'COMMENT', 'MULTILINE_COMMENT']:
                        tokens.append((tag, value))
                    self.pos = match.end()
                    break
            if not match:
                raise SyntaxError(f"Unexpected character: {self.code[self.pos]}")
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
            raise SyntaxError(err_msg + f", but got {self.current_token[1] if self.current_token else 'EOF'}")

    # 完整优先级处理
    precedence = [
        ('assignment', 14),
        ('conditional', 11),
        ('logical_or', 10),
        ('logical_and', 9),
        ('bitwise_or', 8),
        ('bitwise_xor', 7),
        ('bitwise_and', 6),
        ('equality', 5),
        ('relational', 4),
        ('shift', 3),
        ('additive', 2),
        ('multiplicative', 1),
        ('unary', 0)
    ]

    def parse(self):
        ast = []
        while self.current_token:
            if self.current_token[0] == 'SEMI':
                self.advance()
                continue
            ast.append(self.parse_expression())
        return ast

    def parse_expression(self, precedence_level=0):
        if precedence_level >= len(self.precedence):
            return self.parse_primary()
        
        current_prec_name = self.precedence[precedence_level][0]
        left = self.parse_expression(precedence_level + 1)

        while True:
            current_token = self.current_token
            if not current_token:
                break

            # 处理赋值运算符
            if current_prec_name == 'assignment' and current_token[0] in ['ASSIGN', 'ASSIGN_OP']:
                op = current_token[1]
                self.advance()
                right = self.parse_expression(precedence_level)
                left = {f"assignment{op}": {"left": left, "right": right}}
                continue

            # 处理三元运算符
            if current_prec_name == 'conditional' and current_token[1] == '?':
                self.advance()
                then_expr = self.parse_expression()
                self.expect(':', "Expected ':' in ternary operator")
                else_expr = self.parse_expression(precedence_level)
                left = {"ternary": {"condition": left, "then": then_expr, "else": else_expr}}
                continue

            # 处理二元运算符
            if self.is_binary_operator(current_prec_name, current_token):
                op = current_token[1]
                self.advance()
                right = self.parse_expression(precedence_level + 1)
                left = {"symbol": op, "left": left, "right": right}
                continue

            break
        
        return left

    def is_binary_operator(self, current_prec, token):
        op_mapping = {
            'logical_or': ['||'],
            'logical_and': ['&&'],
            'bitwise_or': ['|'],
            'bitwise_xor': ['^'],
            'bitwise_and': ['&'],
            'equality': ['==', '!='],
            'relational': ['<', '>', '<=', '>='],
            'additive': ['+', '-'],
            'multiplicative': ['*', '/', '%', '\\']
        }
        return token[0] in ['LOGIC_OP', 'MATH_OP'] and token[1] in op_mapping.get(current_prec, [])

    def parse_primary(self):
        token_type, token_value = self.current_token
        
        # 处理变量
        if token_type == 'VARIABLE':
            self.advance()
            return {"variable": token_value}

        # 处理字符串
        if token_type == 'STRING':
            self.advance()
            return {"string": token_value}

        # 处理数字
        if token_type == 'INTEGER_LITERAL':
            self.advance()
            return {"integer": token_value}
        
        if token_type == 'FLOAT':
            self.advance()
            return {"float": token_value}

        # 处理括号表达式
        if token_type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN', "Expected closing parenthesis")
            return expr

        # 处理函数调用
        if token_type == 'IDENTIFIER':
            return self.parse_function_call()

        # 处理列表
        if token_type == 'LBRACKET':
            return self.parse_list()

        raise SyntaxError(f"Unexpected primary token: {token_value}")

    def parse_function_call(self):
        func_name = self.expect('IDENTIFIER', "Expected function name")
        return {"function": {"name": func_name, "args": self.parse_expression()}}

    def parse_list(self):
        self.expect('LBRACKET', "Expected '['")
        items = []
        while self.current_token and self.current_token[0] != 'RBRACKET':
            items.append(self.parse_expression())
            if self.current_token and self.current_token[0] == 'COMMA':
                self.advance()
        self.expect('RBRACKET', "Expected ']'")
        return {"list": items}

# ====================== 测试验证 ======================
if __name__ == "__main__":
    test_code = '''
    output (int "1" + int "3");
    [result] = ([a] + [b]) * 3;
    '''
    
    lexer = Lexer(test_code)
    try:
        tokens = lexer.tokenize()
        print("Tokens:", tokens)  # 调试输出
        
        parser = Parser(tokens)
        ast = parser.parse()
        print(json.dumps(ast, indent=4))
    except SyntaxError as e:
        print(f"Syntax Error: {e}")

    # 期望输出结构：
    """
    [
        {
            "function": {
                "name": "output",
                "args": [
                    {
                        "symbol": "+",
                        "left": {
                            "function": {
                                "name": "int",
                                "args": [{"string": "\"1\""}]
                            }
                        },
                        "right": {
                            "function": {
                                "name": "int",
                                "args": [{"string": "\"3\""}]
                            }
                        }
                    }
                ]
            }
        },
        {
            "assignment=": {
                "left": {"variable": "[result]"},
                "right": {
                    "symbol": "*",
                    "left": {
                        "symbol": "+",
                        "left": {"variable": "[a]"},
                        "right": {"variable": "[b]"}
                    },
                    "right": {"integer": "3"}
                }
            }
        }
    ]
    """