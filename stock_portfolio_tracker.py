import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
from forex_python.converter import CurrencyRates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime

class StockTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Stock Portfolio Tracker")
        self.root.geometry("1100x650")

        self.stocks = []
        self.currency = 'INR'
        self.currency_rate = 1
        self.c = CurrencyRates()

        self.create_widgets()
        self.update_conversion_rate()

    def update_conversion_rate(self):
        try:
            self.currency_rate = self.c.get_rate('USD', 'INR') if self.currency == 'INR' else 1
        except:
            self.currency_rate = 83.0  # fallback

    def create_widgets(self):
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Stock Symbol").grid(row=0, column=0)
        self.symbol_entry = tk.Entry(input_frame)
        self.symbol_entry.grid(row=0, column=1)

        tk.Label(input_frame, text="Quantity").grid(row=0, column=2)
        self.quantity_entry = tk.Entry(input_frame)
        self.quantity_entry.grid(row=0, column=3)

        tk.Label(input_frame, text="Buy Price (USD)").grid(row=0, column=4)
        self.price_entry = tk.Entry(input_frame)
        self.price_entry.grid(row=0, column=5)

        tk.Button(input_frame, text="Add", command=self.add_stock).grid(row=0, column=6)
        tk.Button(input_frame, text="Switch to USD" if self.currency == 'INR' else "Switch to INR", command=self.toggle_currency).grid(row=0, column=7)

        # Table
        self.tree = ttk.Treeview(self.root, columns=("Symbol", "Qty", "Buy Price", "Curr Price", "Value", "Gain/Loss"), show='headings')
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        # Summary and actions
        action_frame = tk.Frame(self.root)
        action_frame.pack()

        tk.Button(action_frame, text="Refresh", command=self.update_table).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Show Graphs", command=self.plot_graphs).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Show Line Graphs", command=self.plot_line_graphs).pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=5)

        self.summary_label = tk.Label(self.root, text="", font=('Arial', 12))
        self.summary_label.pack(pady=10)

        self.timestamp_label = tk.Label(self.root, text="Last Updated: -", font=('Arial', 10, 'italic'))
        self.timestamp_label.pack()

    def add_stock(self):
        symbol = self.symbol_entry.get().upper()
        try:
            qty = int(self.quantity_entry.get())
            price = float(self.price_entry.get())
            self.stocks.append((symbol, qty, price))
            self.update_table()
        except:
            messagebox.showerror("Error", "Enter valid quantity and price.")

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Please select a stock to remove.")
            return
        values = self.tree.item(selected[0])['values']
        symbol = values[0]
        qty = int(values[1])
        buy_price = float(values[2]) / self.currency_rate if self.currency == 'INR' else float(values[2])
        self.stocks = [s for s in self.stocks if not (s[0] == symbol and s[1] == qty and abs(s[2] - buy_price) < 0.01)]
        self.update_table()

    def toggle_currency(self):
        self.currency = 'USD' if self.currency == 'INR' else 'INR'
        self.update_conversion_rate()
        self.update_table()

    def update_table(self):
        self.tree.delete(*self.tree.get_children())
        total_inv = 0
        total_val = 0
        stock_data = []

        for symbol, qty, buy_price in self.stocks:
            try:
                data = yf.Ticker(symbol).history(period='1d')
                curr_price = data['Close'].iloc[-1]
                rate = self.currency_rate
                inv = qty * buy_price * rate
                val = qty * curr_price * rate
                gain = val - inv
                stock_data.append((symbol, qty, buy_price*rate, curr_price*rate, val, gain))
                total_inv += inv
                total_val += val
            except:
                continue

        # Sort to find top gainers/losers
        if stock_data:
            top_gain = max(stock_data, key=lambda x: x[5])
            top_loss = min(stock_data, key=lambda x: x[5])
        else:
            top_gain = top_loss = None

        for row in stock_data:
            self.tree.insert('', 'end', values=(row[0], row[1], f"{row[2]:.2f}", f"{row[3]:.2f}", f"{row[4]:.2f}", f"{row[5]:.2f}"),  tags=('gain' if row[5] > 0 else 'loss'))

        self.tree.tag_configure('gain', background='lightgreen')
        self.tree.tag_configure('loss', background='salmon')

        net = total_val - total_inv
        summary = f"Total Investment: {total_inv:.2f} {self.currency} | Current Value: {total_val:.2f} {self.currency} | Net: {'+' if net >= 0 else ''}{net:.2f} {self.currency}"
        if top_gain and top_loss:
            summary += f"\nTop Gainer: {top_gain[0]} ({top_gain[5]:.2f}), Top Loser: {top_loss[0]} ({top_loss[5]:.2f})"

        self.summary_label.config(text=summary)
        self.timestamp_label.config(text=f"Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def plot_graphs(self):
        symbols = [s[0] for s in self.stocks]
        vals = []
        for symbol, qty, _ in self.stocks:
            try:
                price = yf.Ticker(symbol).history(period='1d')['Close'].iloc[-1] * self.currency_rate
                vals.append(price * qty)
            except:
                vals.append(0)

        plt.figure(figsize=(6,6))
        plt.pie(vals, labels=symbols, autopct='%1.1f%%')
        plt.title("Portfolio Distribution")
        plt.tight_layout()
        plt.show()

    def plot_line_graphs(self):
        if not self.stocks:
            messagebox.showinfo("No Data", "Add stocks first.")
            return

        plt.figure(figsize=(10, 6))
        for symbol, _, _ in self.stocks:
            try:
                data = yf.Ticker(symbol).history(period='1y')['Close'] * self.currency_rate
                data.plot(label=symbol)
            except:
                continue

        plt.title("Stock Trends (1 Year)")
        plt.xlabel("Date")
        plt.ylabel(f"Price ({self.currency})")
        plt.legend()
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = StockTracker(root)
    root.mainloop()


