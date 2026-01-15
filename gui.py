import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import sys
import os
import struct

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Пробуем импортировать модули с обработкой ошибок
try:
    from lexer import Lexer, KEYWORDS, DELIMITER_TABLE
    from parser import Parser
    from semantic import Semantic
    MODULES_LOADED = True
except ImportError as e:
    print(f"Внимание: не удалось загрузить модули: {e}")
    print("GUI будет работать в демо-режиме")
    MODULES_LOADED = False

class SimpleCompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Учебный компилятор")
        self.root.geometry("1200x700")
        
        # Проверяем наличие модулей
        if not MODULES_LOADED:
            messagebox.showwarning("Внимание", 
                "Модули lexer.py, parser.py или semantic.py не найдены.\n"
                "GUI будет работать в демо-режиме.")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Панель управления
        control_frame = tk.Frame(self.root, bg="#e0e0e0", height=40)
        control_frame.pack(fill="x", padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        tk.Button(control_frame, text="📂 Открыть файл", 
                 command=self.load_file, bg="#4CAF50", fg="white",
                 font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        tk.Button(control_frame, text="▶ Запустить компиляцию", 
                 command=self.run_compilation, bg="#2196F3", fg="white",
                 font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        tk.Button(control_frame, text="🗑 Очистить все", 
                 command=self.clear_all, bg="#f44336", fg="white",
                 font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        # Основная область с разделителями
        main_paned = tk.PanedWindow(self.root, orient="horizontal", sashwidth=5)
        main_paned.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Левая часть - исходный код
        left_frame = tk.LabelFrame(main_paned, text="Исходный код", 
                                  font=("Arial", 10, "bold"), padx=5, pady=5)
        self.source_text = scrolledtext.ScrolledText(left_frame, wrap="word", 
                                                    font=("Courier New", 10),
                                                    width=40, height=30)
        self.source_text.pack(fill="both", expand=True)
        main_paned.add(left_frame)
        
        # Центральная часть - результаты
        center_paned = tk.PanedWindow(main_paned, orient="vertical", sashwidth=5)
        
        # Токены
        tokens_frame = tk.LabelFrame(center_paned, text="Токены (таблица, номер)", 
                                    font=("Arial", 10, "bold"), padx=5, pady=5)
        self.tokens_text = scrolledtext.ScrolledText(tokens_frame, wrap="word",
                                                    font=("Courier New", 10),
                                                    height=10)
        self.tokens_text.pack(fill="both", expand=True)
        center_paned.add(tokens_frame)
        
        # Таблицы
        tables_frame = tk.LabelFrame(center_paned, text="Таблицы лексем", 
                                    font=("Arial", 10, "bold"), padx=5, pady=5)
        
        # Вкладки для таблиц
        table_notebook = ttk.Notebook(tables_frame)
        
        self.table_texts = {}
        table_names = ["Ключевые слова", "Разделители", "Числа", "Идентификаторы"]
        
        for i, name in enumerate(table_names, 1):
            frame = tk.Frame(table_notebook)
            text = scrolledtext.ScrolledText(frame, wrap="word", 
                                           font=("Courier New", 10), height=8)
            text.pack(fill="both", expand=True)
            table_notebook.add(frame, text=name)
            self.table_texts[i] = text
        
        table_notebook.pack(fill="both", expand=True, padx=2, pady=2)
        center_paned.add(tables_frame)
        
        main_paned.add(center_paned)
        
        # Правая часть - AST и лог
        right_paned = tk.PanedWindow(main_paned, orient="vertical", sashwidth=5)
        
        # AST
        ast_frame = tk.LabelFrame(right_paned, text="AST (Абстрактное синтаксическое дерево)", 
                                 font=("Arial", 10, "bold"), padx=5, pady=5)
        self.ast_text = scrolledtext.ScrolledText(ast_frame, wrap="word",
                                                 font=("Courier New", 9),
                                                 height=15)
        self.ast_text.pack(fill="both", expand=True)
        right_paned.add(ast_frame)
        
        # Лог
        log_frame = tk.LabelFrame(right_paned, text="Лог компиляции", 
                                 font=("Arial", 10, "bold"), padx=5, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap="word",
                                                 font=("Courier New", 9),
                                                 height=10)
        self.log_text.pack(fill="both", expand=True)
        right_paned.add(log_frame)
        
        main_paned.add(right_paned)
        
        # Статус бар
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             bd=1, relief="sunken", anchor="w",
                             bg="#f0f0f0", font=("Arial", 9))
        status_bar.pack(side="bottom", fill="x", padx=5, pady=2)
    
    def load_file(self):
        filename = filedialog.askopenfilename(
            title="Выберите файл с исходным кодом",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.source_text.delete(1.0, "end")
                    self.source_text.insert(1.0, content)
                self.status_var.set(f"Загружен файл: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}")
    
    def clear_all(self):
        self.source_text.delete(1.0, "end")
        self.tokens_text.delete(1.0, "end")
        for text_widget in self.table_texts.values():
            text_widget.delete(1.0, "end")
        self.ast_text.delete(1.0, "end")
        self.log_text.delete(1.0, "end")
        self.status_var.set("Все поля очищены")
    
    def log(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.root.update()
    
    def int_to_binary(self, num_str):
        """Преобразует целое число в двоичное представление"""
        try:
            # Убираем пробелы и преобразуем в нижний регистр
            clean_num = num_str.strip().lower()
            
            # Обрабатываем разные системы счисления
            if clean_num.endswith('b'):
                # Двоичное число
                base_num = clean_num[:-1]
                decimal_val = int(base_num, 2)
                return f"{num_str} (десятичное: {decimal_val})"
            
            elif clean_num.endswith('o'):
                # Восьмеричное число
                base_num = clean_num[:-1]
                decimal_val = int(base_num, 8)
                binary_val = bin(decimal_val)[2:]  # убираем '0b'
                return f"{binary_val}"
            
            elif clean_num.endswith('h'):
                # Шестнадцатеричное число
                base_num = clean_num[:-1]
                decimal_val = int(base_num, 16)
                binary_val = bin(decimal_val)[2:]
                return f"{binary_val}"
            
            elif clean_num.endswith('d'):
                # Десятичное число с суффиксом
                base_num = clean_num[:-1]
                decimal_val = int(base_num)
                binary_val = bin(decimal_val)[2:]
                return f"{binary_val}"
            
            else:
                # Десятичное число без суффикса
                decimal_val = int(clean_num)
                binary_val = bin(decimal_val)[2:]
                return f"{binary_val}"
                
        except Exception as e:
            return f"{num_str} (ошибка преобразования: {str(e)})"
    
    def float_to_binary(self, num_str):
        """Преобразует вещественное число в двоичное представление IEEE 754"""
        try:
            # Преобразуем строку в float
            clean_num = num_str.strip().lower()
            float_val = float(clean_num)
            
            # Получаем двоичное представление float (32 бита)
            # Используем одинарную точность для компактности
            binary_repr = ''.join(f'{c:08b}' for c in struct.pack('!f', float_val))
            
            # Разделяем на компоненты IEEE 754:
            # 1 бит знака, 8 бит экспоненты, 23 бита мантиссы
            sign_bit = binary_repr[0]
            exponent_bits = binary_repr[1:9]
            mantissa_bits = binary_repr[9:]
            
            # Преобразуем экспоненту и мантиссу в десятичные значения
            exponent = int(exponent_bits, 2) - 127  # Смещение экспоненты
            
            # Вычисляем мантиссу
            mantissa = 1.0
            for i, bit in enumerate(mantissa_bits):
                if bit == '1':
                    mantissa += 2 ** (-(i + 1))
            
            # Формируем результат
            result = f"{num_str}\n"
            result += f"{sign_bit}{exponent_bits}{mantissa_bits}\n"
            #result += f"  Знак: {'-' if sign_bit == '1' else '+'}\n"
            #result += f"  Экспонента: {exponent_bits} (десятичная: {exponent})\n"
            #result += f"  Мантисса: 1.{mantissa_bits}\n"
            #result += f"  Значение: {'-' if sign_bit == '1' else ''}{mantissa} × 2^{exponent}"
            
            return result
            
        except Exception as e:
            return f"{num_str} (ошибка преобразования: {str(e)})"
    
    def number_to_binary(self, num_str):
        """Преобразует число в двоичное представление"""
        try:
            clean_num = num_str.strip().lower()
            
            # Проверяем, является ли число вещественным
            is_float = False
            if '.' in clean_num or 'e' in clean_num:
                # Убираем суффиксы для проверки
                temp_num = clean_num
                for suffix in ['b', 'o', 'h', 'd']:
                    if temp_num.endswith(suffix):
                        temp_num = temp_num[:-1]
                        break
                
                # Проверяем, содержит ли оставшаяся часть точку или 'e'
                if '.' in temp_num or 'e' in temp_num:
                    is_float = True
            
            if is_float:
                return self.float_to_binary(clean_num)
            else:
                return self.int_to_binary(clean_num)
                
        except Exception as e:
            return f"{num_str} (ошибка преобразования: {str(e)})"
    
    def run_compilation(self):
        if not MODULES_LOADED:
            messagebox.showerror("Ошибка", 
                "Модули компилятора не найдены. Убедитесь, что файлы "
                "lexer.py, parser.py и semantic.py находятся в той же папке.")
            return
        
        # Очищаем предыдущие результаты
        self.tokens_text.delete(1.0, "end")
        for text_widget in self.table_texts.values():
            text_widget.delete(1.0, "end")
        self.ast_text.delete(1.0, "end")
        self.log_text.delete(1.0, "end")
        
        source = self.source_text.get(1.0, "end-1c")
        if not source.strip():
            messagebox.showwarning("Внимание", "Исходный код пуст!")
            return
        
        try:
            self.status_var.set("Выполняется лексический анализ...")
            self.log("=== Начало компиляции ===")
            self.log("Шаг 1: Лексический анализ")
            
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            
            # Выводим токены в формате (таблица, номер)
            self.tokens_text.insert("end", f"Найдено токенов: {len(tokens)}\n\n")
            for i, token in enumerate(tokens, 1):
                try:
                    # Получаем ссылку на таблицу
                    ref = lexer.token_to_table_ref(token)
                    if ref:
                        self.tokens_text.insert("end", f"{i:3}. ({ref[0]}, {ref[1]})\n")
                    else:
                        self.tokens_text.insert("end", f"{i:3}. {token}\n")
                except Exception as e:
                    self.tokens_text.insert("end", f"{i:3}. Ошибка: {str(e)}\n")
            
            # Заполняем таблицы
            # Таблица 1: Ключевые слова
            kw_text = self.table_texts[1]
            kw_text.insert("end", "Таблица 1: Ключевые слова\n")
            kw_text.insert("end", "=" * 40 + "\n")
            for i, keyword in enumerate(KEYWORDS, 1):
                kw_text.insert("end", f"{i:3}. {keyword}\n")
            
            # Таблица 2: Разделители
            delim_text = self.table_texts[2]
            delim_text.insert("end", "Таблица 2: Разделители\n")
            delim_text.insert("end", "=" * 40 + "\n")
            for i, delim in enumerate(DELIMITER_TABLE, 1):
                # Пропускаем пробел, если он есть в таблице
                if delim != " ":
                    delim_text.insert("end", f"{i:3}. {delim}\n")
            
            # Таблица 3: Числа (с двоичным представлением)
            num_text = self.table_texts[3]
            num_text.insert("end", "Таблица 3: Числа\n")
            num_text.insert("end", "=" * 40 + "\n")
            for i, num in enumerate(lexer.tables.get(3, []), 1):
                binary_repr = self.number_to_binary(num)
                num_text.insert("end", f"{i:3}. {binary_repr}\n\n")
            
            # Таблица 4: Идентификаторы
            id_text = self.table_texts[4]
            id_text.insert("end", "Таблица 4: Идентификаторы\n")
            id_text.insert("end", "=" * 40 + "\n")
            for i, ident in enumerate(lexer.tables.get(4, []), 1):
                id_text.insert("end", f"{i:3}. {ident}\n")
            
            self.log("✓ Лексический анализ завершен успешно")
            self.status_var.set("Выполняется синтаксический анализ...")
            
            # Синтаксический анализ
            self.log("\nШаг 2: Синтаксический анализ")
            parser = Parser(tokens)
            ast = parser.parse_program()
            
            # Выводим AST
            self.ast_text.insert("end", self.format_ast(ast))
            self.log("✓ Синтаксический анализ завершен успешно")
            self.status_var.set("Выполняется семантический анализ...")
            
            # Семантический анализ
            self.log("\nШаг 3: Семантический анализ")
            sema = Semantic()
            sema.analyze(ast)
            
            self.log("✓ Семантический анализ завершен успешно")
            self.log("\n=== Компиляция успешно завершена! ===")
            self.status_var.set("Компиляция завершена успешно")
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"\n✗ ОШИБКА: {error_msg}")
            self.log("=== Компиляция прервана ===")
            self.status_var.set("Ошибка компиляции")
            messagebox.showerror("Ошибка компиляции", error_msg)
    
    def format_ast(self, node, depth=0):
        """Форматирует AST для отображения"""
        result = ""
        indent = "  " * depth
        
        # Информация о узле
        node_info = f"{indent}{node.kind}"
        if node.value is not None:
            node_info += f": {node.value}"
        if hasattr(node, 'pos') and node.pos:
            node_info += f" [строка {node.pos[0]}, столбец {node.pos[1]}]"
        
        result += node_info + "\n"
        
        # Рекурсивно обрабатываем детей
        if hasattr(node, 'children'):
            for child in node.children:
                if child is not None:
                    if hasattr(child, 'kind'):  # Это узел AST
                        result += self.format_ast(child, depth + 1)
                    elif isinstance(child, list):
                        for item in child:
                            if item is not None and hasattr(item, 'kind'):
                                result += self.format_ast(item, depth + 1)
        
        return result

def main():
    try:
        root = tk.Tk()
        app = SimpleCompilerGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Ошибка при запуске GUI: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()