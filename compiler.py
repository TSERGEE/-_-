import sys
from lexer import Lexer
from parser import Parser
from semantic import Semantic

def run_compiler(filename):
    try:
        filetext = open(filename, "r", encoding="utf-8").read()
    except Exception as e:
        print("Ошибка чтения файла:", e); sys.exit(1)
    try:
        # Лексический анализ
        lexer = Lexer(filetext)
        lexemes = lexer.tokenize()
        print("Лексический анализ завершён.")
        # Синтаксический анализ
        parser = Parser(lexemes)
        ast = parser.parse_program()
        print("Синтаксический анализ завершён.")
        # Семантический анализ
        sema = Semantic()
        errors = sema.analyze(ast)
        if errors:
            print("Semantic check: FAILED")
            for e in errors:
                print(" -", e)
        print("Семантический анализ завершён. Программа корректна.")
    except Exception as e:
        print("Ошибка компиляции:", e)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python compiler.py <имя_файла>")
    else:
        run_compiler(sys.argv[1])