from lexer import Token

# AST узлы

class Node:
    def __init__(self, kind, value=None, children=None, pos=None):
        self.kind = kind
        self.value = value
        self.children = children or []
        self.pos = pos

    def __repr__(self):
        return f"{self.kind}({self.value}, {self.children})"

# Pratt — таблица приоритетов

PRECEDENCE = {
    "or": 10,
    "and": 20,
    "lt": 30, "le": 30, "gt": 30, "ge": 30, "ne": 30, "eq": 30,
    "plus": 40, "min": 40,
    "mult": 50, "div": 50
}

# PARSER

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    def current(self):
        return self.tokens[self.pos]
    def advance(self):
        tok = self.current()
        self.pos += 1
        return tok
    def expect(self, kind, value=None):
        tok = self.current()
        if tok.kind != kind:
            raise Exception(
                f"Синтаксическая ошибка на {tok.line}:{tok.col}: ожидалось {kind}, получено {tok.kind}"
            )
        if value is not None and tok.value != value:
            raise Exception(
                f"Синтаксическая ошибка на {tok.line}:{tok.col}: ожидалось '{value}', получено '{tok.value}'"
            )
        return self.advance()
    def parse_program(self):
        self.expect("KW_PROGRAM")
        self.expect("KW_VAR")
        
        decl = self.parse_declaration()

        self.expect("KW_BEGIN")
        stmts = []
        while self.current().kind != "OP" and  self.current().kind != 'KW_END':
            stmts.append(self.parse_statement())
            if self.current().value == ";":
                self.advance()
            #print(self.current().value)
        self.expect("KW_END")
        self.expect("OP", ".")
        return Node("program", children=[decl] + stmts)
    def parse_declaration(self):
        self.expect("KW_DIM")
        vars_ = []
        id_tok = self.expect("ID")
        vars_.append(Node("var", id_tok.value, pos=(id_tok.line, id_tok.col)))

        while self.current().value == ",":
            self.advance()
            id_tok = self.expect("ID")
            vars_.append(Node("var", id_tok.value, pos=(id_tok.line, id_tok.col)))
        
        if self.current().value in ("%", "!", "$"):
            type_tok = self.current()
            self.advance()
            return Node("decl", type_tok.value, vars_, pos=(type_tok.line, type_tok.col))
        else:
            raise Exception(
            f"Синтаксическая ошибка: неправильная лексема '{self.current().value}' на {self.current().line}:{self.current().col}"
        )
    def parse_compound(self):
        lbrace = self.expect("OP", "{")

        stmts = [self.parse_statement()]

        while self.current().value == ";":
            self.advance()
            if self.current().value == "}":
                break
            stmts.append(self.parse_statement())

        self.expect("OP", "}")

        return Node(
            "compound",
            children=stmts,
            pos=(lbrace.line, lbrace.col)
        )
    def parse_assignment(self):
        if self.current().kind == "KW_LET":
            self.advance()
        id_tok = self.expect("ID")
        self.expect("OP", "eq")
        expr = self.parse_expression()

        return Node(
            "assign",
            id_tok.value,
            [expr],
            pos=(id_tok.line, id_tok.col)
        )
    def parse_if(self):
        if_tok = self.advance()
        cond = self.parse_expression()
        self.expect("KW_THEN")
        then_stmt = self.parse_statement()

        else_stmt = None
        if self.current().kind == "KW_ELSE":
            self.advance()
            else_stmt = self.parse_statement()
        self.expect("KW_END_ELSE")
        return Node("if", children=[cond, then_stmt, else_stmt], pos=(if_tok.line, if_tok.col))
    def parse_while(self):
        w = self.advance()
        self.expect("KW_WHILE")
        cond = self.parse_expression()
        body = self.parse_statement()
        self.expect("KW_LOOP")
        return Node("while", children=[cond, body], pos=(w.line, w.col))
    def parse_for(self):
        f = self.advance()
        self.expect("OP", "(")
        if self.current().value != ";":
            #self.advance()
            init = self.parse_expression()
        else:
            init = None
        self.expect("OP", ";")
        if self.current().value != ";":
            cond = self.parse_expression()
        else:
            cond = None
        self.expect("OP", ";")
        if self.current().value != ")":
            inc = self.parse_expression()
        else:
            inc = None
        self.expect("OP", ")")
        body = self.parse_statement()
        #print(init)
        #print(cond)
        #print(inc)
        #print(body)
        return Node("for", children=[init, cond, inc, body], pos=(f.line, f.col))
    def parse_input(self):
        r = self.advance()
        self.expect("OP", "(")
        ids = [self.expect("ID").value]
        while self.current().kind == "ID":
            #self.advance()
            ids.append(self.expect("ID").value)
        
        self.expect("OP", ")")
        return Node("input", ids, pos=(r.line, r.col))
    def parse_output(self):
        w = self.advance()
        self.expect("OP", "(")
        args = [self.parse_expression()]
        self.expect("OP", ")")
        return Node("output", children=args, pos=(w.line, w.col))
    def parse_simple_statement(self):
        tok = self.current()

        #if tok.kind in ("KW_DIM"):
        #    return self.parse_declaration()

        if tok.kind in ("ID", "KW_LET"):
            return self.parse_assignment()

        if tok.kind == "KW_IF":
            return self.parse_if()

        if tok.kind == "KW_DO":
            return self.parse_while()

        if tok.kind == "KW_FOR":
            return self.parse_for()

        if tok.kind == "KW_INPUT":
            return self.parse_input()

        if tok.kind == "KW_OUTPUT":
            return self.parse_output()

        raise Exception(
            f"Синтаксическая ошибка: неожиданная лексема '{tok.value}' на {tok.line}:{tok.col}"
        )
    def parse_statement(self):
        if self.current().value == "{":
            return self.parse_compound()
        return self.parse_simple_statement()
    def parse_expression(self, min_prec=0):
        left = self.parse_prefix()

        while self.current().kind == "OP":
            op = self.current()
            prec = PRECEDENCE.get(op.value)
            if prec is None or prec < min_prec:
                break

            self.advance()
            right = self.parse_expression(prec + 1)
            left = Node("binop", op.value, [left, right], pos=(op.line, op.col))

        return left
    def parse_prefix(self):
        tok = self.current()

        if tok.kind == "ID":
            self.advance()
            return Node("id", tok.value, pos=(tok.line, tok.col))

        if tok.kind == "NUMBER":
            self.advance()
            return Node("number", tok.value, pos=(tok.line, tok.col))

        if tok.kind.startswith("KW_") and tok.value in ("true", "false"):
            self.advance()
            return Node("bool", tok.value, pos=(tok.line, tok.col))

        if tok.kind == "OP" and tok.value == "not":
            self.advance()
            operand = self.parse_expression(60)
            return Node("unop", "not", [operand], pos=(tok.line, tok.col))

        if tok.value == "(":
            self.advance()
            expr = self.parse_expression()
            self.expect("OP", ")")
            return expr

        raise Exception(
            f"Синтаксическая ошибка: неожиданная лексема '{tok.value}' на {tok.line}:{tok.col}"
        )
