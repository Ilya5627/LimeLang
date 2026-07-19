import os
import platform
import sys
from typing import Tuple

keys = ["if", "elif", "ret", "fn", "else", "use", "match", "case", "var", "for", "loop", "load", "struct", "usec", "as", "in"]
ops = ['=', '+', '-', "*", '/', '==', '!=', '//', '%', '(', ')', '{', '}', '>', '<', '>=', '<=', ':', ';', '#', '.',
       ',', "^", '[', ']', '|', '&', '!', '..']


def get_libs_path():
    if getattr(sys, 'frozen', False):
        # Запущено как .exe (PyInstaller, Nuitka)
        p = os.path.dirname(sys.executable)
    else:
        # Обычный Python-скрипт
        p = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(p, "libs")


def lex(code) -> list[Tuple[str, str]]:
    chars: list[str] = list(code)
    tokens = []
    i = 0

    def get(x=0):
        nonlocal i
        if i + x < len(chars):
            return chars[i + x]
        return ''

    def pnum():
        nonlocal i
        num = ""
        if get() == '0' and get(1) == 'x':
            num += get()
            i += 1
            num += get()
            i += 1
            while get().isdigit() or get().lower() in 'abcdef':
                num += get()
                i += 1
            tokens.append(("NUM", num))  # оставляем как строку
            return
        while i < len(chars) and (get().isdigit() or get() == '.'):
            num += chars[i]
            i += 1
        tokens.append(("NUM", num))

    def pcom():
        nonlocal i
        while get() != "\n":
            i += 1

    def pstr():
        nonlocal i
        s = ""
        while i < len(chars) and (get() != '"'):
            s += chars[i]
            i += 1
        i += 1
        tokens.append(("STR", s))

    def pID():
        nonlocal i
        s = ""
        while i < len(chars) and (get().isalpha() or get() == "_" or get().isdigit()):
            s += get()
            i += 1
        if s in keys:
            tokens.append(("KEY", s))
            return
        tokens.append(("ID", s))

    while i < len(chars):
        if get().isdigit():
            pnum()
        elif get() == '"':
            i += 1
            pstr()
        elif get() == '/' and get(1) == '/':
            i += 2
            pcom()

        elif get().isalpha() or get() == "_":
            pID()
        elif get() in ops:
            op = get()
            i += 1
            while i < len(code) and op + get() in ops:
                op += get()
                i += 1
            tokens.append(("OP", op))
        else:
            i += 1

    return tokens


from typing import List, Tuple, Any, Dict


class Parser:
    def __init__(self, tokens: List[Tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0

    def peek(self, x=0) -> Tuple[str, str]:
        if self.pos + x < len(self.tokens):
            return self.tokens[self.pos + x]
        return ('EOF', '')

    def next(self) -> Tuple[str, str]:
        tok = self.peek()
        self.pos += 1
        return tok

    def match(self, expected_type: str) -> Tuple[str, str]:
        tok = self.peek()
        if tok[0] == expected_type:
            return self.next()
        raise SyntaxError(f"Ожидался {expected_type}, получен {tok}")

    # ---------- Грамматика ----------
    # program ::= statement*
    # statement ::= var_statement | expression
    # var_statement ::= "var" ID "=" expression
    # expression ::= equality
    # equality ::= comparison (("==" | "!=") comparison)*
    # comparison ::= term ((">" | "<" | ">=" | "<=") term)*
    # term ::= factor (("+" | "-") factor)*
    # factor ::= unary (("*" | "/" | "//" | "%") unary)*
    # unary ::= ("-" | "+") unary | primary
    # primary ::= NUM | STR | ID | "(" expression ")"

    def parse(self) -> List[Dict]:
        """Парсит программу (список statement'ов)"""
        statements = []
        while self.peek()[0] != 'EOF':
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return statements

    def parse_statement(self) -> Dict:
        """Парсит один statement"""
        if self.peek()[0] == 'KEY' and self.peek()[1] == 'var':
            return self.parse_var()
        if self.peek()[0] == 'KEY' and self.peek()[1] == 'if':
            return self.parse_if()
        if self.peek()[0] == 'KEY' and self.peek()[1] == 'fn':
            return self.parse_fn()
        if self.peek()[0] == 'KEY' and self.peek()[1] == 'loop':
            return self.parse_loop()
        if self.peek()[0] == 'KEY' and self.peek()[1] == 'for':
            return self.parse_for()
        if self.peek()[0] == 'KEY' and self.peek()[1] == 'ret':
            return self.parse_ret()
        if self.peek()[0] == 'KEY' and self.peek()[1] == 'load':
            return self.parse_load()
        if self.peek()[0] == 'KEY' and self.peek()[1] == 'use':
            return self.parse_use()
        if self.peek()[0] == 'KEY' and self.peek()[1] == 'struct':
            return self.parse_struct()
        if self.peek()[0] == 'KEY' and self.peek()[1] == 'usec':
            return self.parse_usec()
        if self.peek()[0] == 'ID' and self._is_assignment_ahead():
            return self.parse_change()
        if self.peek()[0] == 'ID' and self.peek(1)[1] == ":":
            return self.parse_met()
        if self.peek()[1] == '{':
            return self.parse_block()
        return self.parse_expression()

    def parse_block(self):
        statements = []
        self.next()

        while not self.peek()[1] == "}":
            statements.append(self.parse_statement())

        self.next()

        return {"type": "block", "statements": statements}

    def parse_met(self):
        cls = self.match("ID")[1]
        self.match("OP")
        func = self.match("ID")[1]
        if not self.peek()[0] == "OP" and not self.peek()[1] == "(":
            raise SyntaxError("Need '(' token but given " + self.peek()[1])
        self.next()
        args = []
        while self.peek()[1] != ")":
            args.append(self.match("ID")[1])
            if self.peek()[1] == ",":
                self.next()
        self.match("OP")
        if self.peek()[1] != "{":
            return {'type': 'eval_met', 'cls': cls, "func": func, 'args': args}
        stmt = self.parse_statement()
        return {'type': 'method', 'cls': cls, 'func': func, 'params': args, 'stmt': stmt}

    def parse_struct(self):
        self.match("KEY")
        name = self.match("ID")[1]
        if self.peek()[1] != '{':
            raise SyntaxError(f"Ожидалась '{{' после struct {name}, получен {self.peek()}")
        self.next()
        fields = []

        while not self.peek()[0] == "OP" and not self.peek()[1] == "}":
            n = self.match("ID")[1]
            self.match("OP")
            t = self.match("ID")[1]
            fields.append({"name": n, "type": t})

            if self.peek()[1] == ',':
                self.next()

        self.next()

        return {
            'type': 'struct',
            'name': name,
            'fields': fields
        }

    def parse_if(self) -> Dict:
        self.match('KEY')
        expr = self.parse_expression()
        stmt = self.parse_statement()
        elifs = []
        while self.peek()[0] == 'KEY' and self.peek()[1] == 'elif':
            self.next()
            expr_ = self.parse_expression()
            stmt_ = self.parse_statement()
            elifs.append({'type': 'elif', 'expr': expr_, 'stmt': stmt_})
        estmt = {}
        if self.peek()[0] == 'KEY' and self.peek()[1] == 'else':
            self.next()
            estmt = self.parse_statement()
        return {'type': 'if', 'expr': expr, 'stmt': stmt, 'elifs': elifs, 'else': {'stmt': estmt}}

    def parse_loop(self) -> Dict:
        self.match('KEY')
        expr = self.parse_expression()
        stmt = self.parse_statement()
        return {'type': 'loop', 'expr': expr, 'stmt': stmt}

    def parse_load(self) -> Dict:
        self.match('KEY')
        expr = self.parse_expression()
        return {'type': 'load', 'expr': expr}

    def parse_use(self) -> Dict:
        self.match('KEY')
        expr = self.parse_expression()
        return {'type': 'use', 'expr': expr}

    def parse_usec(self) -> Dict:
        self.match('KEY')
        expr = self.parse_expression()
        using = {'rule': '', 'as': ''}
        print(self.peek())
        if self.peek()[0] == "OP" and self.peek()[1] == '{':
            self.next()
            using["rule"] = self.parse_expression()
            self.match("OP")
        if self.peek()[1] == "as" and self.peek()[0] == "KEY":
            self.next()
            using["as"] = self.parse_expression()
        return {'type': 'usec', 'expr': expr, "rules": using}

    def _is_for_in_ahead(self) -> bool:
        p = self.pos
        if self.tokens[p][0] != 'ID':
            return False
        p += 1
        while p < len(self.tokens) and self.tokens[p][0] == 'OP' and self.tokens[p][1] == ',':
            p += 1
            if p >= len(self.tokens) or self.tokens[p][0] != 'ID':
                return False
            p += 1
        return p < len(self.tokens) and self.tokens[p][0] == 'KEY' and self.tokens[p][1] == 'in'

    def parse_for(self) -> Dict:
        self.match('KEY')  # 'for'
        if self._is_for_in_ahead():
            return self.parse_for_in()
        start = self.parse_statement()
        self.match('OP')
        expr = self.match("NUM")[1]
        self.match('OP')
        step = self.match("NUM")[1]
        stmt = self.parse_statement()
        return {'type': 'for', 'start': start, 'expr': expr, 'step': step, 'stmt': stmt}

    def parse_for_in(self) -> Dict:
        names = [self.match('ID')[1]]
        while self.peek()[0] == 'OP' and self.peek()[1] == ',':
            self.next()
            names.append(self.match('ID')[1])
        self.match('KEY')  # 'in'
        expr = self.parse_expression()
        stmt = self.parse_statement()
        return {'type': 'for_in', 'names': names, 'expr': expr, 'stmt': stmt}

    def parse_fn(self) -> Dict:
        self.match('KEY')
        name = self.match('ID')[1]
        self.match('OP')
        args = []
        while self.peek()[1] != ")":
            args.append(self.match("ID")[1])
            if self.peek()[1] == ",":
                self.next()
        self.match("OP")
        stmt = self.parse_statement()
        return {'type': 'fs', 'name': name, 'params': args, 'stmt': stmt}

    def parse_ret(self) -> Dict:
        self.match('KEY')
        expr = self.parse_expression()
        return {'type': 'ret', 'expr': expr}

    def parse_var(self) -> Dict:
        """var x = 10 + 2"""
        self.match('KEY')  # 'var'
        name = self.match('ID')[1]
        self.match('OP')  # '='
        expr = self.parse_expression()
        return {'type': 'var', 'name': name, 'value': expr}

    def _is_assignment_ahead(self) -> bool:
        """Смотрит вперёд: ID (('.' ID) | ('[' expr ']'))* '=' (но не '==')"""
        p = self.pos
        if self.tokens[p][0] != 'ID':
            return False
        p += 1
        while p < len(self.tokens):
            if self.tokens[p][0] == 'OP' and self.tokens[p][1] == '.':
                p += 1
                if p >= len(self.tokens) or self.tokens[p][0] != 'ID':
                    return False
                p += 1
            elif self.tokens[p][0] == 'OP' and self.tokens[p][1] == '[':
                depth = 1
                p += 1
                while p < len(self.tokens) and depth > 0:
                    if self.tokens[p][0] == 'OP' and self.tokens[p][1] == '[':
                        depth += 1
                    elif self.tokens[p][0] == 'OP' and self.tokens[p][1] == ']':
                        depth -= 1
                    p += 1
            else:
                break
        return (p < len(self.tokens)
                and self.tokens[p][0] == 'OP'
                and self.tokens[p][1] == '=')

    def parse_change(self) -> Dict:
        """x = 10  |  a.b = 10  |  a[0] = 10  |  a[0].b = 10 ..."""
        name = self.match('ID')[1]
        target = {'type': 'variable', 'name': name}

        while self.peek()[0] == 'OP' and self.peek()[1] in ('.', '['):
            op = self.next()[1]
            if op == '.':
                field = self.match('ID')[1]
                target = {'type': 'dot', 'left': target, 'field': field}
            else:  # '['
                index_expr = self.parse_expression()
                self.match('OP')  # ']'
                target = {'type': 'index', 'left': target, 'index': index_expr}

        self.match('OP')  # '='
        expr = self.parse_expression()
        return {'type': 'c_var', 'target': target, 'value': expr}

    def parse_expression(self) -> Dict:
        return self.parse_condition()

    def parse_condition(self) -> Dict:
        left = self.parse_equality()
        while self.peek()[0] == 'OP' and self.peek()[1] in ('|', '&'):
            op = self.next()[1]
            right = self.parse_equality()
            left = {'type': 'logic', 'op': op, 'left': left, 'right': right}
        return left

    def parse_equality(self) -> Dict:
        left = self.parse_comparison()
        while self.peek()[0] == 'OP' and self.peek()[1] in ('==', '!='):
            op = self.next()[1]
            right = self.parse_comparison()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_comparison(self) -> Dict:
        left = self.parse_term()
        while self.peek()[0] == 'OP' and self.peek()[1] in ('>', '<', '>=', '<='):
            op = self.next()[1]
            right = self.parse_term()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_term(self) -> Dict:
        left = self.parse_factor()
        while self.peek()[0] == 'OP' and self.peek()[1] in ('+', '-', '..'):
            op = self.next()[1]
            right = self.parse_factor()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_factor(self) -> Dict:
        left = self.parse_unary()
        while self.peek()[0] == 'OP' and self.peek()[1] in ('*', '/', '//', '%', '^'):
            op = self.next()[1]
            right = self.parse_func()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_unary(self) -> Dict:
        if self.peek()[0] == 'OP' and self.peek()[1] in ('+', '-', '#'):
            op = self.next()[1]
            operand = self.parse_unary()
            return {'type': 'unary', 'op': op, 'operand': operand}
        return self.parse_func()

    def parse_func(self) -> Dict:
        left = self.parse_primary()
        while self.peek()[0] == 'OP' and self.peek()[1] in ('(', '.', '['):
            op = self.next()[1]
            if op == '(':
                args = []
                while self.peek()[0] != 'OP' or self.peek()[1] != ')':
                    if self.peek()[0] == 'EOF':
                        raise SyntaxError("Ожидалась ')'")
                    args.append(self.parse_expression())
                    if self.peek()[0] == "OP" and self.peek()[1] == ',':
                        self.next()
                self.next()
                left = {'type': 'func', 'left': left, 'args': args}
            elif op == '.':
                if self.peek()[0] != 'ID':
                    raise SyntaxError(f"Ожидался идентификатор после '.', получен {self.peek()}")
                field_name = self.next()[1]
                left = {'type': 'dot', 'left': left, 'field': field_name}
            elif op == '[':
                index_expr = self.parse_expression()
                self.match('OP')  # ']'
                left = {'type': 'index', 'left': left, 'index': index_expr}
        return left

    def parse_primary(self) -> Dict:
        tok = self.peek()

        if tok[0] == 'NUM':
            self.next()
            value = tok[1]

            # Проверяем, не hex ли это
            if value.startswith('0x'):
                return {'type': 'number', 'value': int(value, 16)}

            # Проверяем, не число ли с плавающей точкой
            if '.' in value:
                return {'type': 'number', 'value': float(value)}
            else:
                return {'type': 'number', 'value': int(value)}

        elif tok[0] == 'STR':
            self.next()
            return {'type': 'string', 'value': tok[1]}

        elif tok[0] == 'ID':
            self.next()
            return {'type': 'variable', 'name': tok[1]}

        elif tok[0] == 'OP' and tok[1] == '(':
            self.next()
            expr = self.parse_expression()
            self.match('OP')  # ')'
            return expr

        elif tok[0] == 'OP' and tok[1] == '[':
            return self.parse_array_literal()

        elif tok[0] == 'OP' and tok[1] == '{':
            return self.parse_dict_literal()

        else:
            raise SyntaxError(f"Неожиданный токен: {tok}")

    def parse_array_literal(self) -> Dict:
        self.match('OP')  # '['
        items = []
        while not (self.peek()[0] == 'OP' and self.peek()[1] == ']'):
            if self.peek()[0] == 'EOF':
                raise SyntaxError("Ожидалась ']'")
            items.append(self.parse_expression())
            if self.peek()[0] == 'OP' and self.peek()[1] == ',':
                self.next()
        self.match('OP')  # ']'
        return {'type': 'array', 'items': items}

    def parse_dict_literal(self) -> Dict:
        self.match('OP')  # '{'
        pairs = []
        while not (self.peek()[0] == 'OP' and self.peek()[1] == '}'):
            if self.peek()[0] == 'EOF':
                raise SyntaxError("Ожидалась '}'")
            if self.peek()[0] == 'STR':
                key = {'type': 'string', 'value': self.next()[1]}
            elif self.peek()[0] == 'ID':
                key = {'type': 'string', 'value': self.next()[1]}  # ключ как идентификатор -> строка
            else:
                self.match('OP')  # '['  -- вычисляемый ключ [expr]:
                key = self.parse_expression()
                self.match('OP')  # ']'
            self.match('OP')  # ':'
            value = self.parse_expression()
            pairs.append((key, value))
            if self.peek()[0] == 'OP' and self.peek()[1] == ',':
                self.next()
        self.match('OP')  # '}'
        return {'type': 'dict', 'pairs': pairs}

    def pretty_print(self, ast: List[Dict], indent: int = 0) -> str:
        """Красивый вывод AST (для отладки)"""
        result = []
        for node in ast:
            result.append(self._node_to_str(node, indent))
        return '\n'.join(result)

    def _node_to_str(self, node: Dict, indent: int = 0) -> str:
        if node['type'] == 'var':
            return f'  ' * indent + f'var {node["name"]} = {self._node_to_str(node["value"], 0)}'

        elif node['type'] == 'binop':
            left = self._node_to_str(node['left'], 0)
            right = self._node_to_str(node['right'], 0)
            return f'({left} {node["op"]} {right})'

        elif node['type'] == 'unary':
            return f'({node["op"]}{self._node_to_str(node["operand"], 0)})'

        elif node['type'] == 'number':
            return str(node['value'])

        elif node['type'] == 'string':
            return f'"{node["value"]}"'

        elif node['type'] == 'variable':
            return node['name']

        else:
            return str(node)


class CodeGen:
    def __init__(self, ast: list[dict], path: str):
        self.ast: list[dict] = ast
        self.gen = ""
        self.path = path

    def generate(self):
        for i in self.ast:
            self.genSt(i)
        return self.gen

    def genSt(self, v):
        if v["type"] == "var":
            self.genVar(v)
        if v["type"] == "c_var":
            self.gencVar(v)
        elif v["type"] == "block":
            for i in v["statements"]:
                self.genSt(i)
        elif v["type"] == "if":
            self.genIf(v)
        elif v["type"] == "fs":
            self.genFunction(v)
        elif v["type"] == "for":
            self.genFor(v)
        elif v["type"] == "for_in":
            self.genForIn(v)
        elif v["type"] == "loop":
            self.genLoop(v)
        elif v["type"] == "load":
            self.genLoad(v)
        elif v["type"] == "use":
            self.genUse(v)
        elif v["type"] == "ret":
            self.genRet(v)
        elif v["type"] == "struct":
            self.genStruct(v)
        elif v["type"] == "method":
            self.genMethod(v)
        elif v["type"] == "usec":
            self.genUseC(v)
        else:
            self.genExpr(v)
            self.gen += '\n'

    def genVar(self, v):
        self.gen += "local " + v["name"] + " = "
        self.genExpr(v['value'])
        self.gen += "\n"

    def genRet(self, v):
        self.gen += "return "
        self.genExpr(v['expr'])
        self.gen += "\n"

    def genForIn(self, v):
        names = ', '.join(v['names'])
        self.gen += f"for {names} in pairs("
        self.genExpr(v['expr'])
        self.gen += ") do\n"
        self.genSt(v["stmt"])
        self.gen += "end\n"

    def genFor(self, v):
        self.gen += "for "
        if v["start"]['type'] != "c_var":
            raise SyntaxError("In \"for\" cycle must be var assignment(without \"var\")")
        self.genSt(v['start'])
        self.gen += f", {v["expr"]}, {v["step"]} do\n"
        self.genSt(v["stmt"])
        self.gen += "end\n"

    def genLoad(self, v):
        path = os.path.join(self.path, v["expr"]['value'] + ".lm")
        if not os.path.exists(path):
            raise SyntaxError("Cannot find file: " + path)
        with open(path, encoding="utf-8", mode="r") as f:
            code = f.read()
        self.gen += f"{CodeGen(Parser(lex(code)).parse(), path).generate()}\n"

    def genStruct(self, v):
        struct_name = v["name"]
        string_fields = [f['name'] for f in v["fields"] if f['type'] == 's']

        # В cdef строковые поля переименовываем с подчёркиванием,
        # чтобы освободить оригинальное имя под __index-геттер
        def cfield_name(fname, ftype):
            return f"_{fname}" if ftype == 's' else fname

        self.gen += "ffi.cdef([[\ntypedef struct {\n"
        for f in v["fields"]:
            ctype = self.boxTypeToC(f["type"])[0]
            self.gen += f"{ctype} {cfield_name(f['name'], f['type'])};\n"
        self.gen += f"}} {struct_name};\n]])\n"

        params = ', '.join(f['name'] for f in v["fields"])
        assigns = ', '.join(
            f"{cfield_name(f['name'], f['type'])} = {f['name']} or {self.boxTypeToC(f['type'])[1]}"
            for f in v["fields"]
        )

        self.gen += f"local {struct_name}_methods = {{}}\n"
        self.gen += f"local {struct_name}_refs = setmetatable({{}}, {{__mode = 'k'}})\n"

        if string_fields:
            self.gen += f"local {struct_name}_getters = {{\n"
            for fname in string_fields:
                self.gen += f"{fname} = function(self) return ffi.string(self._{fname}) end,\n"
            self.gen += "}\n"
            index_fn = (
                f"function(t, k)\n"
                f"local g = {struct_name}_getters[k]\n"
                f"if g then return g(t) end\n"
                f"return {struct_name}_methods[k]\n"
                f"end"
            )
        else:
            index_fn = f"{struct_name}_methods"

        refs_body = ""
        if string_fields:
            refs_assign = ', '.join(
                f"{fname} = {fname} or {self.boxTypeToC('s')[1]}" for fname in string_fields
            )
            refs_body = f"{struct_name}_refs[self] = {{{refs_assign}}}\n"

        self.gen += (
            f"local {struct_name} = ffi.metatype(\"{struct_name}\", {{\n"
            f"__index = {index_fn},\n"
            f"__new = function(ct, {params})\n"
            f"local self = ffi.new(ct, {{{assigns}}})\n"
            f"{refs_body}"
            f"return self\n"
            f"end\n"
            f"}})\n"
        )

    def genUse(self, v):
        path = os.path.join(self.path, "libs\\" + v["expr"]['value'] + "\\setup.lm")
        if not os.path.exists(path):
            path = os.path.join(get_libs_path(), v["expr"]['value'] + "\\setup.lm")
            if not os.path.exists(path):
                raise SyntaxError("Cannot find file: " + path)
        with open(path, encoding="utf-8", mode="r") as f:
            code = f.read()
        self.gen += f"{CodeGen(Parser(lex(code)).parse(), os.path.dirname(path)).generate()}\n"

    def normalize_path(self, path: str) -> str:
        path = os.path.normpath(path)
        path = path.replace('\\', '/')  # для Lua
        return path

    def get_library_extension(self) -> str:
        """Возвращает расширение библиотеки для текущей платформы"""
        if platform.system() == "Windows":
            return ".dll"
        elif platform.system() == "Linux":
            return ".so"
        elif platform.system() == "Darwin":  # macOS
            return ".dylib"
        return ".dll"  # fallback

    def find_library_file(self, name: str, search_paths: list) -> str:
        """Ищет библиотеку в указанных путях"""
        ext = self.get_library_extension()

        # Если нет расширения — добавляем
        if not name.endswith(ext):
            candidates = [name + ext, name]
        else:
            candidates = [name]

        for path in search_paths:
            for candidate in candidates:
                full_path = os.path.join(path, candidate)
                if os.path.exists(full_path):
                    return full_path

        return None

    def genUseC(self, v):
        # 1. Получаем имя библиотеки
        dll_name = v["expr"]['value']
        if not dll_name.endswith(('.dll', '.so', '.dylib')):
            dll_name += self.get_library_extension()

        # 2. Поиск библиотеки
        search_paths = [
            os.path.join(self.path, "libs"),  # локальная папка проекта
            os.getcwd(),  # текущая папка
            os.path.join(get_libs_path()),  # глобальная LIME_PATH
            "C:\\\\Windows\\System32"
        ]

        # Добавляем системные пути (Windows)
        if platform.system() == "Windows":
            search_paths.extend(os.environ.get("PATH", "").split(";"))
        else:
            search_paths.extend(os.environ.get("LD_LIBRARY_PATH", "").split(":"))
            search_paths.extend(["/usr/lib", "/usr/local/lib"])

        lib_path = self.find_library_file(dll_name, search_paths)

        if not lib_path:
            raise SyntaxError(f"Cannot find library: {dll_name} in {search_paths}")

        # 3. Нормализуем путь для Lua
        lib_path = self.normalize_path(lib_path)

        # 4. Получаем имя переменной
        var_name = os.path.splitext(os.path.basename(dll_name))[0]
        if v["rules"]["as"] and v["rules"]["as"] != '':
            var_name = v["rules"]["as"]["value"]

        # 6. Если есть правила (объявления функций)
        if v["rules"]["rule"] and v["rules"]["rule"] != '':
            if v["rules"]["rule"]["type"] != "string":
                raise SyntaxError("Cannot work with non-string type in dll import")

            self.gen += f"ffi.cdef([[\n{v["rules"]["rule"]["value"]}]])\n"

        # 7. Загружаем библиотеку
        self.gen += f"local {var_name} = ffi.load('{lib_path}')\n"

    def genLoop(self, v):
        self.gen += "while "
        self.genExpr(v['expr'])
        self.gen += " do\n"
        self.genSt(v["stmt"])
        self.gen += "end\n"

    def gencVar(self, v):
        self.genTarget(v['target'])
        self.gen += " = "
        self.genExpr(v['value'])
        self.gen += "\n"

    def genTarget(self, t):
        if t['type'] == 'variable':
            self.gen += t['name']
        elif t['type'] == 'dot':
            self.genTarget(t['left'])
            self.gen += "." + t['field']
        elif t['type'] == 'index':
            self.genTarget(t['left'])
            self.gen += "["
            self.genExpr(t['index'])
            self.gen += "]"

    def genFunction(self, v):
        self.gen += f"local function {v["name"]}("
        j = 0
        for i in v["params"]:
            self.gen += i
            if j < len(v["params"]) - 1:
                self.gen += ", "
            j += 1
        self.gen += ")\n"
        self.genSt(v["stmt"])
        self.gen += "end\n"

    def genMethod(self, v):
        self.gen += f"function {v["cls"]}_methods:{v["func"]}("
        j = 0
        for i in v["params"]:
            self.gen += i
            if j < len(v["params"]) - 1:
                self.gen += ", "
            j += 1
        self.gen += ")\n"
        self.genSt(v["stmt"])
        self.gen += "end\n"

    def genIf(self, v):
        self.gen += "if "
        self.genExpr(v['expr'])
        self.gen += " then\n"
        self.genSt(v["stmt"])
        for i in v["elifs"]:
            self.gen += "elseif "
            self.genExpr(i["expr"])
            self.gen += " then\n"
            self.genSt(i["stmt"])
        if v['else']['stmt'] != {}:
            self.gen += "else\n"
            self.genSt(v["else"]["stmt"])
        self.gen += "end\n"

    def genExpr(self, v):
        if v["type"] == "binop":
            self.gen += "("
            self.genExpr(v["left"])
            self.gen += f"{v['op'] if v["op"] != "!=" else "~="}"
            self.genExpr(v["right"])
            self.gen += ")"
        if v["type"] == "logic":
            self.gen += "("
            self.genExpr(v["left"])
            self.gen += f"{"and" if v['op'] == "&" else "or"}"
            self.genExpr(v["right"])
            self.gen += ")"
        elif v["type"] == "number":
            self.gen += str(v["value"])
        elif v["type"] == "unary":
            self.gen += v["op"]
            self.genExpr(v["operand"])
        elif v["type"] == "eval_met":
            self.gen += v["cls"] + ":" + v["func"]
            self.gen += "("
            j = 0
            for i in v['args']:
                self.genExpr(i)
                if len(v["args"]) - 1 > j:
                    self.gen += ", "
                j += 1
            self.gen += ')'
        elif v["type"] == "string":
            self.gen += f'"{v["value"]}"'
        elif v["type"] == "variable":
            self.gen += v["name"]
        elif v["type"] == "func":
            self.genExpr(v['left'])
            self.gen += "("
            j = 0
            for i in v['args']:
                self.genExpr(i)
                if len(v["args"]) - 1 > j:
                    self.gen += ", "
                j += 1
            self.gen += ')'
        elif v["type"] == "dot":
            self.genExpr(v['left'])
            self.gen += "." + v["field"]
        elif v["type"] == "index":
            self.genExpr(v['left'])
            self.gen += "["
            self.genExpr(v['index'])
            self.gen += "]"
        elif v["type"] == "array":
            self.gen += "{"
            j = 0
            for item in v["items"]:
                self.genExpr(item)
                if len(v["items"]) - 1 > j:
                    self.gen += ", "
                j += 1
            self.gen += "}"
        elif v["type"] == "dict":
            self.gen += "{"
            j = 0
            for key, value in v["pairs"]:
                self.gen += "["
                self.genExpr(key)
                self.gen += "] = "
                self.genExpr(value)
                if len(v["pairs"]) - 1 > j:
                    self.gen += ", "
                j += 1
            self.gen += "}"

    def boxTypeToC(self, s):
        if s == "f":
            return "float", "0"
        elif s == "s":
            return "const char*", "\"\""
        elif s == "i":
            return "int", "0"
        elif s == "p":
            return "void*", "NULL"
        elif s == "b":
            return "bool", "false"
        elif s == "d":
            return "double", "0"
        else:
            raise SyntaxError("Unknown Type: " + s)
