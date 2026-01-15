KEYWORDS = [
   "program", "var", "begin", "end", "dim", "let", "if", "then", "else", "end_else", "for", "do",
   "while", "loop", "input", "output", "%", "!", "$", "true", "false"
]

DELIMITER_TABLE = [
    ".", ";", ",", "{", "}", "=", "(", ")", "ne", "eq", "lt", "le", "gt", "ge", " ", "~", 
   "plus", "min", "or", "mult", "div", "and"
]

class Token:
    def __init__(self, kind, value, line, col):
        self.kind = kind
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.kind}, {self.value!r}, {self.line}:{self.col})"
    def __str__(self):
        return f"{self.kind}, {self.value!r}, {self.line}:{self.col}"


class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        # таблицы лексем
        self.tables = {
            1: [],  # ключевые слова
            2: [],  # разделители
            3: [],  # числа
            4: []   # идентификаторы
        }

    # -------------------------------------------------
    # Базовые операции
    # -------------------------------------------------

    def current(self):
        if self.pos >= len(self.text):
            return ''
        return self.text[self.pos]

    def peek(self, n=1):
        return self.text[self.pos:self.pos+n]

    def advance(self):
        ch = self.current()
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def register_lexeme(self, table_no, value):
        table = self.tables[table_no]
        if value not in table:
            table.append(value)
        index = table.index(value) + 1  # нумерация с 1
        return table_no, index

    def token_to_table_ref(self, token):                                                                             
        # Для ключевых слов
        if token.kind.startswith("KW_"):
            idx = KEYWORDS.index(token.value.lower()) + 1                          
            return (1, idx)
        # Для операторов и разделителей
        if token.kind in ("OP", "NEWLINE"):                                                   
            idx = DELIMITER_TABLE.index(token.value.lower()) + 1                                             
            return (2, idx)
        # Для чисел
        if token.kind == "NUMBER":
            return self.register_lexeme(3, token.value)
        # Для идентификаторов
        if token.kind == "ID":
            return self.register_lexeme(4, token.value)
        return

    # -------------------------------------------------
    # Пропуск пробелов и комментариев
    # -------------------------------------------------

    def skip_whitespace(self):
        while self.current().isspace():
            self.advance()

    def skip_comment(self):
        # текущий символ '{', следующий '*'
        self.advance()  # пропускаем '{'
        self.advance()  # пропускаем '*'
    
        while self.current():
            if self.current() == '*' and self.peek(2) == "*}":       
                self.advance()
                self.advance()
                return
            self.advance()
        raise Exception(f"Лексическая ошибка на {self.line}:{self.col}: незакрытый комментарий")
    # -------------------------------------------------
    # Идентификаторы и ключевые слова
    # -------------------------------------------------

    def identifier_or_keyword(self):
        start_line, start_col = self.line, self.col
        value = ""
        # Собираем буквенно-цифровые символы
        while self.current().isalnum() or self.current() == '_':
            value += self.advance()
        low = value.lower()
        # Проверяем ключевые слова
        if low in KEYWORDS:
            return Token("KW_" + low.upper(), value, start_line, start_col)
        # Проверяем операторы-слова
        if low in ("ne", "eq", "lt", "le", "gt", "ge", "plus", "min", "or", "mult", "div", "and"):
            return Token("OP", low, start_line, start_col)
        return Token("ID", value, start_line, start_col)

    # -------------------------------------------------
    # Числа (ВСЕ ВИДЫ)
    # -------------------------------------------------

    def number(self):
        start_line, start_col = self.line, self.col
        value = ""

        def error():
            raise Exception(
                f"Лексическая ошибка на {start_line}:{start_col}: "
                f"неправильный формат числа '{value}'"
            )

        # ---------- целая часть (обязательная) ----------
        if not self.current().isdigit():
            error()
        int_part = ""
        while self.current().isdigit():
            int_part += self.advance()
        value += int_part

        # ---------- проверка суффиксов целых ----------
        # BIN
        if self.current() in ('B', 'b'):
            if any(c not in '01' for c in int_part):
                error()
            value += self.advance()
            return Token("NUMBER", value, start_line, start_col)

        # OCT
        if self.current() in ('O', 'o'):
            if any(c not in '01234567' for c in int_part):
                error()
            value += self.advance()
            return Token("NUMBER", value, start_line, start_col)

        # DEC с суффиксом
        if self.current() in ('D', 'd'):
            value += self.advance()
            return Token("NUMBER", value, start_line, start_col)

        # ---------- экспонента ----------
        if self.current() in ('E', 'e'):
            value += self.advance()
            if self.current() in ('+', '-'):
                value += self.advance()
            # ---------- HEX ----------
            elif self.current().lower() in 'abcdef':
                hex_tail = ""
                while self.current().lower() in 'abcdef':
                    hex_tail += self.advance()
                if hex_tail:
                    if self.current() in ('H', 'h'):
                        value += hex_tail + self.advance()
                        return Token("NUMBER", value, start_line, start_col)
                    else:
                        error()
            exp = ""
            while self.current().isdigit():
                exp += self.advance()
            if not exp:
                error()
            value += exp
        
        # ---------- HEX ----------
        hex_tail = ""
        while self.current().lower() in 'abcdef':
            hex_tail += self.advance()
        if hex_tail:
            if self.current() in ('H', 'h'):
                value += hex_tail + self.advance()
                return Token("NUMBER", value, start_line, start_col)
            else:
                error()

        # ---------- вещественная часть ----------
        if self.current() == '.':
            value += self.advance()
            frac = ""
            while self.current().isdigit():
                frac += self.advance()
            if not frac:
                error()
            value += frac
            # ---------- экспонента ----------
            if self.current() in ('E', 'e'):
                value += self.advance()
                if self.current() in ('+', '-'):
                    value += self.advance()
                exp = ""
                while self.current().isdigit():
                    exp += self.advance()
                if not exp:
                    error()
                value += exp

        return Token("NUMBER", value, start_line, start_col)


    # -------------------------------------------------
    # Операторы и разделители
    # -------------------------------------------------

    def operator(self):
        start_line, start_col = self.line, self.col
        # Проверяем двухсимвольные операторы
        two_char = self.peek(2).lower()
        if two_char in ("ne", "eq", "lt", "le", "gt", "ge", "or"):
            for _ in two_char:
                self.advance()
            return Token("OP", two_char, start_line, start_col)
        # Проверяем многосимвольные операторы-слова
        for word in ("plus", "min", "mult", "div", "and"):
            if self.peek(len(word)).lower() == word:
                for _ in word:
                    self.advance()
                return Token("OP", word, start_line, start_col)
        # Одиночные символы-разделители
        ch = self.current()
        if ch in (".", ";", ",", "{", "}", "=", "(", ")", " ", "~"):
            self.advance()
            return Token("OP", ch, start_line, start_col)
        if ch in KEYWORDS:
            self.advance()
            return Token("KW_" + ch.upper(), ch, start_line, start_col)
        raise Exception(f"Лексическая ошибка на {start_line}:{start_col}"
                            f" неизвестный оператор '{ch}'")

    # -------------------------------------------------
    # Главный метод
    # -------------------------------------------------
    

    def tokenize(self):
        tokens = []

        while self.current():
            ch = self.current()
            # Пропускаем пробелы
            if ch.isspace():
                self.advance()
                continue
            # Обработка комментариев
            if ch == '{' and self.peek(2) == "{*":
                self.skip_comment()
                continue
            # Идентификаторы и буквенные ключевые слова
            if ch.isalpha() or ch == '_':
                tokens.append(self.identifier_or_keyword())
                if tokens[-1].kind == ".":
                    break
                continue
            # Числа
            if ch.isdigit():
                tokens.append(self.number())
                continue
            # Операторы и разделители
            tokens.append(self.operator())
        self.print_tokens(tokens)
        return tokens
    def print_tokens(self, tokens):           
        for token in tokens:
        #    print(str(token)) # Вывод токенов
            ref = self.token_to_table_ref(token)
            print(ref, end="\n")



if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python lexer.py source_file")
        sys.exit(1)
    try:
        filetext = open(sys.argv[1], "r", encoding="utf-8").read()
    except Exception as e:
        print("Ошибка чтения файла:", e); sys.exit(1)
    lexer = Lexer(filetext)
    lexemes = lexer.tokenize()
    print(lexemes)