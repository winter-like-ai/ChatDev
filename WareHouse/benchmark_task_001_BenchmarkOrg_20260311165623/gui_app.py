'''
Optional GUI module for displaying capital information.
This module is not required for the core document generation task but is kept for reference.
Uses tkinter for the graphical interface.
'''
import tkinter as tk
from tkinter import ttk, messagebox
from capital_facts import CapitalFacts
class CapitalApp:
    """GUI application class (optional)."""
    def __init__(self):
        """Initialize the application with facts database and create GUI."""
        self.facts = CapitalFacts()
        self.root = None
    def create_widgets(self):
        """Create all GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Title
        title_label = ttk.Label(
            main_frame,
            text="首都信息查询系统\nCapital Information System",
            font=("Arial", 16, "bold"),
            justify=tk.CENTER
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        # Question section
        question_frame = ttk.LabelFrame(main_frame, text="用户问题", padding="10")
        question_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        question_label = ttk.Label(
            question_frame,
            text="中国的首都是哪里？",
            font=("Arial", 12)
        )
        question_label.grid(row=0, column=0, padx=5)
        # Answer button
        answer_button = ttk.Button(
            question_frame,
            text="获取答案",
            command=self.show_answer
        )
        answer_button.grid(row=0, column=1, padx=10)
        # China capital info section
        china_frame = ttk.LabelFrame(main_frame, text="中国首都详细信息", padding="10")
        china_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        china_info = self.facts.get_china_capital_info()
        # Create labels for China capital info
        info_labels = [
            ("国家:", china_info['country']),
            ("首都:", f"{china_info['chinese_name']} ({china_info['capital']})"),
            ("人口:", china_info['population']),
            ("面积:", china_info['area']),
            ("建都时间:", china_info['established'])
        ]
        for i, (label_text, value_text) in enumerate(info_labels):
            label = ttk.Label(china_frame, text=label_text, font=("Arial", 10, "bold"))
            label.grid(row=i, column=0, sticky=tk.W, pady=2)
            value = ttk.Label(china_frame, text=value_text)
            value.grid(row=i, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        # Facts about Beijing
        facts_frame = ttk.LabelFrame(main_frame, text="关于北京的有趣事实", padding="10")
        facts_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        facts_text = tk.Text(facts_frame, height=6, width=40, wrap=tk.WORD)
        facts_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar = ttk.Scrollbar(facts_frame, orient=tk.VERTICAL, command=facts_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        facts_text.configure(yscrollcommand=scrollbar.set)
        for fact in china_info['facts']:
            facts_text.insert(tk.END, f"• {fact}\n")
        facts_text.configure(state='disabled')
        # Other capitals section
        other_frame = ttk.LabelFrame(main_frame, text="其他主要国家首都", padding="10")
        other_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        # Create treeview for other capitals
        columns = ('country', 'capital', 'population', 'area')
        tree = ttk.Treeview(other_frame, columns=columns, show='headings', height=4)
        # Define headings
        tree.heading('country', text='国家')
        tree.heading('capital', text='首都')
        tree.heading('population', text='人口')
        tree.heading('area', text='面积')
        # Define columns
        tree.column('country', width=120)
        tree.column('capital', width=120)
        tree.column('population', width=100)
        tree.column('area', width=100)
        # Add scrollbar
        tree_scrollbar = ttk.Scrollbar(other_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scrollbar.set)
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        # Insert data
        for capital_info in self.facts.get_all_capitals():
            if capital_info['country'] != 'China':
                tree.insert('', tk.END, values=(
                    capital_info['country'],
                    capital_info['capital'],
                    capital_info['population'],
                    capital_info['area']
                ))
        # Search section
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        search_label = ttk.Label(search_frame, text="搜索其他国家首都:")
        search_label.grid(row=0, column=0, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.grid(row=0, column=1, padx=(0, 5))
        search_button = ttk.Button(
            search_frame,
            text="搜索",
            command=self.search_country
        )
        search_button.grid(row=0, column=2)
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        china_frame.columnconfigure(1, weight=1)
        facts_frame.columnconfigure(0, weight=1)
        other_frame.columnconfigure(0, weight=1)
    def show_answer(self):
        """Show the direct answer to the user's question."""
        answer = self.facts.get_answer_to_question()
        messagebox.showinfo("答案", answer)
    def search_country(self):
        """Search for a country's capital."""
        country = self.search_var.get().strip()
        if not country:
            messagebox.showwarning("输入错误", "请输入国家名称")
            return
        result = self.facts.search_capital(country)
        if result:
            messagebox.showinfo(
                "搜索结果",
                f"{country}的首都是: {result['name']}\n"
                f"人口: {result.get('population', 'N/A')}\n"
                f"面积: {result.get('area', 'N/A')}"
            )
        else:
            messagebox.showerror("未找到", f"未找到国家 '{country}' 的首都信息")
    def run(self):
        """Run the main application loop."""
        self.root = tk.Tk()
        self.root.title("首都信息查询系统 - Capital Information System")
        self.root.geometry("800x600")
        # Make window resizable
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.create_widgets()
        self.root.mainloop()