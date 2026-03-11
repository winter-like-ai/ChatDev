'''
GUI implementation for the Capital of China application.
Uses tkinter for the graphical interface.
'''
import tkinter as tk
from tkinter import ttk, messagebox
from capital_finder import create_capital_finder
class CapitalApp:
    """Main GUI application class."""
    def __init__(self):
        """Initialize the application."""
        self.finder = create_capital_finder()
        self.window = None
        self.language_var = None
    def create_widgets(self):
        """Create all GUI widgets."""
        # Title frame
        title_frame = ttk.Frame(self.window, padding="20")
        title_frame.grid(row=0, column=0, sticky="ew")
        title_label = ttk.Label(
            title_frame,
            text="中国首都查询系统",
            font=("Microsoft YaHei", 24, "bold"),
            foreground="#2c3e50"
        )
        title_label.pack()
        subtitle_label = ttk.Label(
            title_frame,
            text="Capital of China Information System",
            font=("Microsoft YaHei", 12),
            foreground="#7f8c8d"
        )
        subtitle_label.pack()
        # Question frame
        question_frame = ttk.LabelFrame(self.window, text="问题", padding="15")
        question_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        question_label = ttk.Label(
            question_frame,
            text="中国的首都是哪里？",
            font=("Microsoft YaHei", 16),
            foreground="#2980b9"
        )
        question_label.pack()
        # Answer frame
        answer_frame = ttk.LabelFrame(self.window, text="答案", padding="15")
        answer_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.answer_text = tk.StringVar()
        self.answer_text.set(self.finder.get_answer())
        answer_label = ttk.Label(
            answer_frame,
            textvariable=self.answer_text,
            font=("Microsoft YaHei", 18, "bold"),
            foreground="#27ae60",
            wraplength=400
        )
        answer_label.pack()
        # Language selection
        language_frame = ttk.Frame(self.window, padding="10")
        language_frame.grid(row=3, column=0, pady=10)
        ttk.Label(language_frame, text="选择语言 / Select Language:").pack(side=tk.LEFT, padx=5)
        self.language_var = tk.StringVar(value="chinese")
        language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.language_var,
            values=["中文", "English"],
            state="readonly",
            width=15
        )
        language_combo.pack(side=tk.LEFT, padx=5)
        language_combo.bind("<<ComboboxSelected>>", self.on_language_change)
        # Buttons frame
        buttons_frame = ttk.Frame(self.window, padding="10")
        buttons_frame.grid(row=4, column=0, pady=10)
        details_btn = ttk.Button(
            buttons_frame,
            text="详细信息",
            command=self.show_details,
            width=15
        )
        details_btn.pack(side=tk.LEFT, padx=5)
        facts_btn = ttk.Button(
            buttons_frame,
            text="有趣事实",
            command=self.show_fun_facts,
            width=15
        )
        facts_btn.pack(side=tk.LEFT, padx=5)
        exit_btn = ttk.Button(
            buttons_frame,
            text="退出",
            command=self.window.quit,
            width=15
        )
        exit_btn.pack(side=tk.LEFT, padx=5)
        # Footer
        footer_frame = ttk.Frame(self.window, padding="10")
        footer_frame.grid(row=5, column=0, sticky="ew")
        footer_label = ttk.Label(
            footer_frame,
            text="© 2023 中国首都查询系统 - 知识就是力量",
            font=("Microsoft YaHei", 9),
            foreground="#95a5a6"
        )
        footer_label.pack()
    def on_language_change(self, event=None):
        """Handle language change event."""
        selected = self.language_var.get().lower()  # Normalize to lowercase
        self.answer_text.set(self.finder.get_answer(selected))
    def show_details(self):
        """Show detailed information about Beijing."""
        details = self.finder.get_detailed_info()
        info_text = f"""
{details['country']} ({details['english_country']})
首都: {details['capital']} ({details['english_capital']})
详细信息:
• 人口: {details['additional_info']['population']}
• 面积: {details['additional_info']['area']}
• 成为首都时间: {details['additional_info']['established_as_capital']}
• 著名地标: {', '.join(details['additional_info']['famous_landmarks'])}
        """
        messagebox.showinfo("详细信息", info_text)
    def show_fun_facts(self):
        """Show fun facts about Beijing."""
        facts = self.finder.get_fun_facts()
        facts_text = "关于北京的有趣事实:\n\n" + "\n\n• ".join([""] + facts)
        messagebox.showinfo("有趣事实", facts_text)
    def run(self):
        """Run the GUI application."""
        self.window = tk.Tk()
        self.window.title("中国首都查询系统 - Capital of China")
        self.window.geometry("500x450")
        self.window.resizable(False, False)
        # Center the window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        self.create_widgets()
        self.window.mainloop()