import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from lexer import Lexer
from parser import Parser
from semantic import Semantic

class CompilerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Учебный компилятор")
        self.geometry("1200x700")

        self.create_widgets()

    def create_widgets(self):
        # ---------- Верхняя панель ----------
        top = tk.Frame(self)
        top.pack(fill=tk.X)

        tk.Button(top, text="Открыть файл", command=self.load_file).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Компилировать", command=self.compile).pack(side=tk.LEFT, padx=5)

        # ---------- Вкладки ----------
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.src_tab = self.make_text_tab("Исходный код")
        self.token_tab = self.make_text_tab("Токены")
        self.tables_tab = self.make_text_tab("Таблицы лексем")
        self.ast_tab = self.make_text_tab("AST")
        self.log_tab = self.make_text_tab("Лог компиляции")

    def make_text_tab(self, title):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text=title)

        text = tk.Text(frame, wrap=tk.NONE)
        text.pack(fill=tk.BOTH, expand=True)

        frame.text = text
        return frame

    # ---------- Загрузка файла ----------
    def load_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Source files", "*.txt *.src"), ("All files", "*.*")]
        )
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            self.src_tab.text.delete(1.0, tk.END)
            self.src_tab.text.insert(tk.END, f.read())

    # ---------- Компиляция ----------
    def compile(self):
        self.clear_tabs()
        source = self.src_tab.text.get(1.0, tk.END)

        try:
            self.log("Лексический анализ...")
            lexer = Lexer(source)
            tokens = lexer.tokenize()

            self.show_tokens(tokens)
            self.show_tables(lexer.tables)

            self.log("Лексический анализ завершён")

            self.log("Синтаксический анализ...")
            parser = Parser(tokens)
            ast = parser.parse_program()
            self.ast_tab.text.insert(tk.END, repr(ast))
            self.log("Синтаксический анализ завершён")

            self.log("Семантический анализ...")
            sema = Semantic()
            sema.analyze(ast)
            self.log("Семантический анализ завершён")
            self.log("\nПрограмма корректна")

        except Exception as e:
            self.log("\n❌ Ошибка:")
            self.log(str(e))
            messagebox.showerror("Ошибка компиляции", str(e))

    # ---------- Вывод ----------
    def show_tokens(self, tokens):
        t = self.token_tab.text
        for tok in tokens:
            t.insert(tk.END, f"{tok}\n")

    def show_tables(self, tables):
        t = self.tables_tab.text
        names = {
            1: "Ключевые слова",
            2: "Разделители",
            3: "Числа",
            4: "Идентификаторы"
        }

        for k in range(1, 5):
            t.insert(tk.END, f"\n=== {names[k]} ===\n")
            for i, val in enumerate(tables[k], start=1):
                t.insert(tk.END, f"{i}: {val}\n")

    def log(self, msg):
        self.log_tab.text.insert(tk.END, msg + "\n")

    def clear_tabs(self):
        for tab in [self.token_tab, self.tables_tab, self.ast_tab, self.log_tab]:
            tab.text.delete(1.0, tk.END)

# ---------- Запуск ----------
if __name__ == "__main__":
    app = CompilerGUI()
    app.mainloop()
