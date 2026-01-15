class SymbolTable:
    def __init__(self):
        self.table = {}
    def declare(self, name, typ, pos):
        if name in self.table:
            raise Exception(
                f"Семантическая ошибка на {pos[0]}:{pos[1]}: переобъявление переменной '{name}'"
            )
        self.table[name] = typ
    def lookup(self, name, pos):
        if name not in self.table:
            raise Exception(
                f"Семантическая ошибка на {pos[0]}:{pos[1]}: необъявленная переменная '{name}'"
            )
        return self.table[name]
def can_assign(target, source):
        if target == source:
            return True
        if target == "!" and source == "%":
            return True
        return False

class Semantic:
    def __init__(self):
        self.symbols = SymbolTable()
    def analyze(self, node):
        for stmt in node.children:
            self.visit(stmt)
    def visit(self, node):
        method = getattr(self, f"visit_{node.kind}", None)
        if not method:
            raise Exception(f"Семантическая ошибка на {node.pos[0]}:{node.pos[1]}: "
                f"Неизвестная лексема {node.kind}")
        return method(node)
    def visit_decl(self, node):
        var_type = node.value
        for var in node.children:
            self.symbols.declare(var.value, var_type, var.pos)
    def visit_assign(self, node):
        var_name = node.value
        var_type = self.symbols.lookup(var_name, node.pos)

        expr_type = self.visit(node.children[0])

        if not can_assign(var_type, expr_type):
            raise Exception(
                f"Семантическая ошибка на {node.pos[0]}:{node.pos[1]}: "
                f"невозможно присвоить {expr_type} к {var_type}"
            )
    def visit_if(self, node):
        cond_type = self.visit(node.children[0])
        if cond_type != "$":
            raise Exception(
                f"Семантическая ошибка на {node.pos[0]}:{node.pos[1]}: "
                f"условие в if должно быть $"
            )

        self.visit(node.children[1])
        if node.children[2]:
            self.visit(node.children[2])
    def visit_while(self, node):
        cond_type = self.visit(node.children[0])
        if cond_type != "$":
            raise Exception(f"Семантическая ошибка на {node.children[0].pos[0]}:{node.children[0].pos[1]}: "
                f"условие в while должно быть $")

        self.visit(node.children[1])
    def visit_for(self, node):
        init, cond, inc, body = node.children
        # init — если есть
        if init is not None:
            self.visit(init)
        # cond — если есть
        if cond is not None:
            cond_type = self.visit(cond)
            if cond_type != "$":
                raise Exception(
                    f"Семантическая ошибка на {cond.pos[0]}:{cond.pos[1]}: "
                    f"условие в for должно быть логическим ($)"
                )
        # inc — если есть
        if inc is not None:
            self.visit(inc)
        # тело цикла — всегда есть
        self.visit(body)
    def visit_input(self, node):
        for name in node.value:
            self.symbols.lookup(name, node.pos)
    def visit_output(self, node):
        for expr in node.children:
            self.visit(expr)
    def visit_id(self, node):
        return self.symbols.lookup(node.value, node.pos)
    def visit_number(self, node):
        if "." in node.value or "e-" in node.value.lower():
            return "!"
        return "%"
    def visit_bool(self, node):
        return "$"
    def visit_unop(self, node):
        operand_type = self.visit(node.children[0])
        if operand_type != "$":
            raise Exception(f"Семантическая ошибка на {node.children[0].pos[0]}:{node.children[0].pos[1]}: "
                f"'not' применим только к $")
        return "$"
    def visit_binop(self, node):
        left = self.visit(node.children[0])
        right = self.visit(node.children[1])
        op = node.value

        if op in ("plus", "min", "mult", "div"):
            if left not in ("%", "!") or right not in ("%", "!"):
                raise Exception(f"Семантическая ошибка на {node.children[0].pos[0]}:{node.children[0].pos[1]}: "
                f"арифметические операции применимы только к числам")
            if op == "div" and left == "%":
                raise Exception(f"Семантическая ошибка на {node.children[0].pos[0]}:{node.children[0].pos[1]}: "
                f"делимое должно быть дробным числом")
            return "!" if "!" in (left, right) else "%"

        if op in ("and", "or"):
            if left != "$" or right != "$":
                raise Exception(f"Семантическая ошибка на {node.children[0].pos[0]}:{node.children[0].pos[1]}: "
                f"логические операции применимы только к $")
            return "$"

        if op in ("eq", "ne", "lt", "le", "gt", "ge"):
            if left != right:
                raise Exception(f"Семантическая ошибка на {node.children[0].pos[0]}:{node.children[0].pos[1]}: "
                f"сравниваемые переменные должны быть одного типа")
            return "$"
    def visit_compound(self, node):
        for stmt in node.children:
            self.visit(stmt)