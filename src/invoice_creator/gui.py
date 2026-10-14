import os
import sys
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Ensure src directory is in sys.path
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# Theme & Color Palette
BG_COLOR = "#F1F5F9"          # Light slate background
CARD_BG = "#FFFFFF"           # Clean white card background
BORDER_COLOR = "#E2E8F0"      # Subtle card border
BORDER_FOCUS = "#6366F1"      # Indigo focus ring
TEXT_MAIN = "#0F172A"         # Dark slate heading text
TEXT_MUTED = "#64748B"        # Slate secondary text
TEXT_LIGHT = "#94A3B8"        # Placeholder text
PRIMARY_COLOR = "#4F46E5"     # Indigo primary (Save button, active badges)
PRIMARY_HOVER = "#4338CA"     # Indigo hover
DARK_BTN_BG = "#0F172A"       # Dark navy (Download/Print button)
DARK_BTN_HOVER = "#1E293B"    # Dark navy hover
INPUT_BG = "#F8FAFC"          # Light input field background
SUMMARY_BG = "#1E1B4B"        # Deep midnight indigo summary card
SUMMARY_TEXT = "#C7D2FE"       # Light indigo text
SUMMARY_ACCENT = "#A5B4FC"     # Indigo header
DANGER_COLOR = "#EF4444"       # Red trash action

# Fonts
FONT_FAMILY = "Helvetica"
FONT_TITLE = (FONT_FAMILY, 15, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 9)
FONT_CARD_TITLE = (FONT_FAMILY, 10, "bold")
FONT_LABEL = (FONT_FAMILY, 8, "bold")
FONT_INPUT = (FONT_FAMILY, 9)
FONT_BTN = (FONT_FAMILY, 9, "bold")
FONT_SUMMARY_TOTAL = (FONT_FAMILY, 18, "bold")


class ModernEntry(tk.Frame):
    """Entry widget wrapped in a styled container with clean borders and focus ring."""
    def __init__(self, parent, placeholder="", default_value="", width=None, justify="left", **kwargs):
        super().__init__(parent, bg=BORDER_COLOR, bd=0, padx=1, pady=1)
        self.inner = tk.Frame(self, bg=INPUT_BG, padx=8, pady=6)
        self.inner.pack(fill="both", expand=True)

        self.placeholder = placeholder
        self.entry = tk.Entry(
            self.inner,
            bg=INPUT_BG,
            fg=TEXT_MAIN,
            bd=0,
            relief="flat",
            font=FONT_INPUT,
            justify=justify,
            insertbackground=PRIMARY_COLOR,
            **kwargs
        )
        if width:
            self.entry.config(width=width)
        self.entry.pack(fill="both", expand=True)

        if default_value:
            self.entry.insert(0, default_value)
            self.entry.config(fg=TEXT_MAIN)
        elif placeholder:
            self.entry.insert(0, placeholder)
            self.entry.config(fg=TEXT_LIGHT)

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, event):
        self.config(bg=BORDER_FOCUS)
        if self.placeholder and self.entry.get() == self.placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=TEXT_MAIN)

    def _on_focus_out(self, event):
        self.config(bg=BORDER_COLOR)
        if self.placeholder and not self.entry.get().strip():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=TEXT_LIGHT)

    def get(self):
        val = self.entry.get()
        if self.placeholder and val == self.placeholder:
            return ""
        return val.strip()

    def set(self, value):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(value))
        self.entry.config(fg=TEXT_MAIN)


class LineItemRow:
    """Represents a single editable row in the Line Items table."""
    def __init__(self, parent, on_change_callback, on_delete_callback, description="", qty=1, price=0.0, tax=10):
        self.parent = parent
        self.on_change = on_change_callback
        self.on_delete = on_delete_callback

        self.frame = tk.Frame(parent, bg=CARD_BG, pady=4)

        # Description
        self.desc_entry = ModernEntry(self.frame, default_value=description, placeholder="Item description")
        self.desc_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Qty
        self.qty_entry = ModernEntry(self.frame, default_value=str(qty), width=7, justify="center")
        self.qty_entry.pack(side="left", padx=4)
        self.qty_entry.entry.bind("<KeyRelease>", lambda e: self.on_change())

        # Price
        self.price_entry = ModernEntry(self.frame, default_value=f"{price:.2f}" if price else "0.00", width=11, justify="center")
        self.price_entry.pack(side="left", padx=4)
        self.price_entry.entry.bind("<KeyRelease>", lambda e: self.on_change())

        # Tax (%)
        self.tax_entry = ModernEntry(self.frame, default_value=str(tax), width=7, justify="center")
        self.tax_entry.pack(side="left", padx=4)
        self.tax_entry.entry.bind("<KeyRelease>", lambda e: self.on_change())

        # Subtotal Label
        self.subtotal_label = tk.Label(
            self.frame,
            text="$0.00",
            font=(FONT_FAMILY, 10, "bold"),
            bg=CARD_BG,
            fg=TEXT_MAIN,
            width=14,
            anchor="e"
        )
        self.subtotal_label.pack(side="left", padx=(8, 12))

        # Delete Button
        self.del_btn = tk.Button(
            self.frame,
            text="✕",
            font=(FONT_FAMILY, 9, "bold"),
            bg=CARD_BG,
            fg=TEXT_LIGHT,
            activeforeground=DANGER_COLOR,
            activebackground="#FEE2E2",
            bd=0,
            cursor="hand2",
            padx=6,
            pady=2,
            relief="flat",
            command=lambda: self.on_delete(self)
        )
        self.del_btn.pack(side="left", padx=2)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def destroy(self):
        self.frame.destroy()

    def calculate(self, currency_symbol="$"):
        try:
            qty = float(self.qty_entry.get().replace(",", "").strip() or 0)
        except ValueError:
            qty = 0.0

        try:
            price = float(self.price_entry.get().replace(",", "").strip() or 0)
        except ValueError:
            price = 0.0

        try:
            tax = float(self.tax_entry.get().replace(",", "").replace("%", "").strip() or 0)
        except ValueError:
            tax = 0.0

        base_val = qty * price
        tax_val = base_val * (tax / 100.0)
        total_val = base_val + tax_val

        self.subtotal_label.config(text=f"{currency_symbol}{total_val:,.2f}")
        return base_val, tax_val, total_val


class InvoiceGeneratorApp(tk.Tk):
    """Full-featured Tkinter GUI matching the modern invoice generator template."""

    def __init__(self):
        super().__init__()
        self.title("Invoice Generator")
        self.geometry("1140x840")
        self.minsize(900, 600)
        self.configure(bg=BG_COLOR)

        self.currency_var = tk.StringVar(value="USD ($)")
        self.currency_symbols = {
            "USD ($)": "$",
            "EUR (€)": "€",
            "GBP (£)": "£",
            "PKR (Rs.)": "Rs. ",
            "CAD ($)": "CA$",
            "AUD ($)": "A$",
        }

        self.line_items = []
        self._setup_styles()
        self._build_ui()
        self._populate_initial_data()
        self.recalculate()

        # Update initial layout so geometry is properly calculated
        self.update_idletasks()
        self._sync_canvas_width()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "TCombobox",
            fieldbackground=INPUT_BG,
            background=INPUT_BG,
            foreground=TEXT_MAIN,
            arrowcolor=TEXT_MUTED,
            relief="flat",
            padding=5
        )

    def _build_ui(self):
        # 1. Top Header Bar
        top_bar = tk.Frame(self, bg=CARD_BG, padx=28, pady=12, highlightthickness=1, highlightbackground=BORDER_COLOR)
        top_bar.pack(fill="x", side="top")

        # Left Header
        header_left = tk.Frame(top_bar, bg=CARD_BG)
        header_left.pack(side="left", fill="y")

        tk.Label(header_left, text="Invoice Generator", font=FONT_TITLE, fg=TEXT_MAIN, bg=CARD_BG).pack(anchor="w")
        tk.Label(header_left, text="Create, customize, and manage client billing seamlessly.", font=FONT_SUBTITLE, fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w")

        # Right Header
        header_right = tk.Frame(top_bar, bg=CARD_BG)
        header_right.pack(side="right", fill="y")

        # Search Bar
        search_box = tk.Frame(header_right, bg=INPUT_BG, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=8, pady=4)
        search_box.pack(side="left", padx=10)
        tk.Label(search_box, text="🔍", font=(FONT_FAMILY, 9), bg=INPUT_BG, fg=TEXT_MUTED).pack(side="left", padx=(0, 4))
        self.search_entry = tk.Entry(search_box, font=FONT_INPUT, bg=INPUT_BG, fg=TEXT_LIGHT, bd=0, relief="flat", width=18)
        self.search_entry.insert(0, "Search invoices...")
        self.search_entry.pack(side="left")

        # Notification Bell
        tk.Label(header_right, text="🔔", font=(FONT_FAMILY, 12), bg=CARD_BG, fg=TEXT_MUTED, cursor="hand2").pack(side="left", padx=8)

        # Auto-saved Pill
        tk.Label(
            header_right,
            text="☁  Auto-saved",
            font=(FONT_FAMILY, 8, "bold"),
            bg="#EEF2FF",
            fg=PRIMARY_COLOR,
            padx=10,
            pady=4,
            relief="flat"
        ).pack(side="left", padx=6)

        # 2. Main Scrollable Container
        main_canvas_frame = tk.Frame(self, bg=BG_COLOR)
        main_canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(main_canvas_frame, bg=BG_COLOR, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(main_canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=BG_COLOR, padx=24, pady=16)

        # Window item on canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Bind scrollable frame configure to update canvas scroll region
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Bind canvas configure to resize the scrollable frame width dynamically
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mouse wheel support
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        # Build Body Sections
        self._build_action_bar(self.scrollable_frame)
        self._build_parties_cards(self.scrollable_frame)
        self._build_line_items_card(self.scrollable_frame)
        self._build_bottom_section(self.scrollable_frame)

    def _sync_canvas_width(self):
        canvas_w = self.canvas.winfo_width()
        if canvas_w > 100:
            self.canvas.itemconfig(self.canvas_window, width=canvas_w)

    def _on_canvas_configure(self, event):
        if event.width > 100:
            self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _build_action_bar(self, parent):
        bar = tk.Frame(parent, bg=BG_COLOR, pady=6)
        bar.pack(fill="x", pady=(0, 14))

        # Mode Selector
        mode_frame = tk.Frame(bar, bg=BG_COLOR)
        mode_frame.pack(side="left", fill="y")

        tk.Label(mode_frame, text="Mode:", font=(FONT_FAMILY, 9, "bold"), fg=TEXT_MUTED, bg=BG_COLOR).pack(side="left", padx=(0, 8))

        pill_container = tk.Frame(mode_frame, bg="#E2E8F0", padx=2, pady=2)
        pill_container.pack(side="left")

        self.btn_editor = tk.Button(
            pill_container,
            text="Editor",
            font=(FONT_FAMILY, 8, "bold"),
            bg=CARD_BG,
            fg=TEXT_MAIN,
            bd=0,
            padx=14,
            pady=4,
            relief="flat",
            cursor="hand2",
            command=self._set_mode_editor
        )
        self.btn_editor.pack(side="left")

        self.btn_preview = tk.Button(
            pill_container,
            text="Live Preview",
            font=(FONT_FAMILY, 8),
            bg="#E2E8F0",
            fg=TEXT_MUTED,
            bd=0,
            padx=14,
            pady=4,
            relief="flat",
            cursor="hand2",
            command=self._set_mode_preview
        )
        self.btn_preview.pack(side="left")

        # Right Action Buttons
        actions_right = tk.Frame(bar, bg=BG_COLOR)
        actions_right.pack(side="right", fill="y")

        tk.Label(actions_right, text="Currency:", font=(FONT_FAMILY, 9), fg=TEXT_MUTED, bg=BG_COLOR).pack(side="left", padx=(0, 6))

        currency_combo = ttk.Combobox(
            actions_right,
            textvariable=self.currency_var,
            values=list(self.currency_symbols.keys()),
            state="readonly",
            width=10,
        )
        currency_combo.pack(side="left", padx=(0, 12))
        currency_combo.bind("<<ComboboxSelected>>", lambda e: self.recalculate())

        # Download / Print button
        self.dl_btn = tk.Button(
            actions_right,
            text="🖨  Download / Print",
            font=FONT_BTN,
            bg=DARK_BTN_BG,
            fg="#FFFFFF",
            activebackground=DARK_BTN_HOVER,
            activeforeground="#FFFFFF",
            bd=0,
            padx=14,
            pady=7,
            relief="flat",
            cursor="hand2",
            command=self.download_print_invoice
        )
        self.dl_btn.pack(side="left", padx=5)

        # Save Invoice button
        self.save_btn = tk.Button(
            actions_right,
            text="💾  Save Invoice",
            font=FONT_BTN,
            bg=PRIMARY_COLOR,
            fg="#FFFFFF",
            activebackground=PRIMARY_HOVER,
            activeforeground="#FFFFFF",
            bd=0,
            padx=16,
            pady=7,
            relief="flat",
            cursor="hand2",
            command=self.save_invoice
        )
        self.save_btn.pack(side="left", padx=(5, 0))

    def _set_mode_editor(self):
        self.btn_editor.config(bg=CARD_BG, fg=TEXT_MAIN, font=(FONT_FAMILY, 8, "bold"))
        self.btn_preview.config(bg="#E2E8F0", fg=TEXT_MUTED, font=(FONT_FAMILY, 8))

    def _set_mode_preview(self):
        self.btn_preview.config(bg=CARD_BG, fg=TEXT_MAIN, font=(FONT_FAMILY, 8, "bold"))
        self.btn_editor.config(bg="#E2E8F0", fg=TEXT_MUTED, font=(FONT_FAMILY, 8))
        self.show_live_preview()

    def _build_card(self, parent):
        return tk.Frame(
            parent,
            bg=CARD_BG,
            padx=20,
            pady=16,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )

    def _build_parties_cards(self, parent):
        container = tk.Frame(parent, bg=BG_COLOR)
        container.pack(fill="x", pady=(0, 16))

        container.columnconfigure(0, weight=1, uniform="party_col")
        container.columnconfigure(1, weight=1, uniform="party_col")

        # --- LEFT CARD: From (Your Company) ---
        from_card = self._build_card(container)
        from_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        from_header = tk.Frame(from_card, bg=CARD_BG)
        from_header.pack(fill="x", pady=(0, 12))
        tk.Label(from_header, text="🏢  From (Your Company)", font=FONT_CARD_TITLE, fg=PRIMARY_COLOR, bg=CARD_BG).pack(side="left")
        tk.Label(from_header, text="Issuer", font=(FONT_FAMILY, 8), fg=TEXT_MUTED, bg="#F1F5F9", padx=6, pady=2).pack(side="right")

        tk.Label(from_card, text="Company Name", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(0, 2))
        self.company_name = ModernEntry(from_card, placeholder="Company Name")
        self.company_name.pack(fill="x", pady=(0, 10))

        row2 = tk.Frame(from_card, bg=CARD_BG)
        row2.pack(fill="x", pady=(0, 10))
        row2.columnconfigure(0, weight=1)
        row2.columnconfigure(1, weight=1)

        f_email = tk.Frame(row2, bg=CARD_BG)
        f_email.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        tk.Label(f_email, text="Email Address", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(0, 2))
        self.company_email = ModernEntry(f_email, placeholder="Email Address")
        self.company_email.pack(fill="x")

        f_phone = tk.Frame(row2, bg=CARD_BG)
        f_phone.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        tk.Label(f_phone, text="Phone Number", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(0, 2))
        self.company_phone = ModernEntry(f_phone, placeholder="Phone Number")
        self.company_phone.pack(fill="x")

        tk.Label(from_card, text="Address", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(0, 2))
        self.company_address = ModernEntry(from_card, placeholder="Address")
        self.company_address.pack(fill="x")

        # --- RIGHT CARD: Bill To (Client) ---
        bill_card = self._build_card(container)
        bill_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        bill_header = tk.Frame(bill_card, bg=CARD_BG)
        bill_header.pack(fill="x", pady=(0, 12))
        tk.Label(bill_header, text="👤  Bill To (Client)", font=FONT_CARD_TITLE, fg=PRIMARY_COLOR, bg=CARD_BG).pack(side="left")
        tk.Label(bill_header, text="Recipient", font=(FONT_FAMILY, 8), fg=TEXT_MUTED, bg="#F1F5F9", padx=6, pady=2).pack(side="right")

        tk.Label(bill_card, text="Client / Company Name", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(0, 2))
        self.client_name = ModernEntry(bill_card, placeholder="Client Name")
        self.client_name.pack(fill="x", pady=(0, 10))

        b_row2 = tk.Frame(bill_card, bg=CARD_BG)
        b_row2.pack(fill="x", pady=(0, 10))
        b_row2.columnconfigure(0, weight=1)
        b_row2.columnconfigure(1, weight=1)

        f_cemail = tk.Frame(b_row2, bg=CARD_BG)
        f_cemail.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        tk.Label(f_cemail, text="Client Email", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(0, 2))
        self.client_email = ModernEntry(f_cemail, placeholder="Client Email")
        self.client_email.pack(fill="x")

        f_invno = tk.Frame(b_row2, bg=CARD_BG)
        f_invno.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        tk.Label(f_invno, text="Invoice Number", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(0, 2))
        self.invoice_number = ModernEntry(f_invno, placeholder="Invoice Number")
        self.invoice_number.pack(fill="x")

        b_row3 = tk.Frame(bill_card, bg=CARD_BG)
        b_row3.pack(fill="x")
        b_row3.columnconfigure(0, weight=1)
        b_row3.columnconfigure(1, weight=1)

        f_date = tk.Frame(b_row3, bg=CARD_BG)
        f_date.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        tk.Label(f_date, text="Invoice Date", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(0, 2))
        self.invoice_date = ModernEntry(f_date, placeholder="YYYY-MM-DD")
        self.invoice_date.pack(fill="x")

        f_due = tk.Frame(b_row3, bg=CARD_BG)
        f_due.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        tk.Label(f_due, text="Due Date", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(0, 2))
        self.due_date = ModernEntry(f_due, placeholder="YYYY-MM-DD")
        self.due_date.pack(fill="x")

    def _build_line_items_card(self, parent):
        card = self._build_card(parent)
        card.pack(fill="x", pady=(0, 16))

        header = tk.Frame(card, bg=CARD_BG)
        header.pack(fill="x", pady=(0, 14))

        tk.Label(header, text="📑  Line Items", font=(FONT_FAMILY, 11, "bold"), fg=TEXT_MAIN, bg=CARD_BG).pack(side="left")

        add_btn = tk.Button(
            header,
            text="+ Add Item",
            font=(FONT_FAMILY, 8, "bold"),
            bg="#EEF2FF",
            fg=PRIMARY_COLOR,
            activebackground="#E0E7FF",
            activeforeground=PRIMARY_COLOR,
            bd=0,
            padx=12,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self.add_item_row
        )
        add_btn.pack(side="right")

        col_header = tk.Frame(card, bg=CARD_BG)
        col_header.pack(fill="x", pady=(0, 8))

        tk.Label(col_header, text="DESCRIPTION", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG).pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(col_header, text="QTY", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG, width=7).pack(side="left", padx=4)
        tk.Label(col_header, text="PRICE", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG, width=11).pack(side="left", padx=4)
        tk.Label(col_header, text="TAX (%)", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG, width=7).pack(side="left", padx=4)
        tk.Label(col_header, text="SUBTOTAL", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG, width=14, anchor="e").pack(side="left", padx=(8, 12))
        tk.Label(col_header, text="ACTION", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG, width=4).pack(side="left", padx=2)

        self.items_container = tk.Frame(card, bg=CARD_BG)
        self.items_container.pack(fill="x")

    def _build_bottom_section(self, parent):
        container = tk.Frame(parent, bg=BG_COLOR)
        container.pack(fill="x", pady=(0, 20))

        container.columnconfigure(0, weight=1, uniform="bottom_col")
        container.columnconfigure(1, weight=1, uniform="bottom_col")

        # --- LEFT: Payment Terms & Notes ---
        notes_card = self._build_card(container)
        notes_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(notes_card, text="Payment Terms & Notes", font=FONT_CARD_TITLE, fg=TEXT_MAIN, bg=CARD_BG).pack(anchor="w", pady=(0, 10))

        tk.Label(notes_card, text="Payment Terms", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(0, 3))
        self.payment_terms_var = tk.StringVar(value="Net 30 Days")
        terms_combo = ttk.Combobox(
            notes_card,
            textvariable=self.payment_terms_var,
            values=["Net 30 Days", "Due on Receipt", "Net 15 Days", "Net 60 Days", "Custom Terms"],
            state="readonly"
        )
        terms_combo.pack(fill="x", pady=(0, 12))

        tk.Label(notes_card, text="Notes / Bank Details", font=FONT_LABEL, fg=TEXT_MUTED, bg=CARD_BG).pack(anchor="w", pady=(0, 3))

        notes_border = tk.Frame(notes_card, bg=BORDER_COLOR, padx=1, pady=1)
        notes_border.pack(fill="both", expand=True)

        self.notes_text = tk.Text(
            notes_border,
            bg=INPUT_BG,
            fg=TEXT_MAIN,
            bd=0,
            relief="flat",
            font=FONT_INPUT,
            height=4,
            padx=8,
            pady=6,
            insertbackground=PRIMARY_COLOR
        )
        self.notes_text.pack(fill="both", expand=True)

        # --- RIGHT: INVOICE SUMMARY Card ---
        summary_card = tk.Frame(container, bg=SUMMARY_BG, padx=24, pady=20, highlightthickness=0)
        summary_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(summary_card, text="INVOICE SUMMARY", font=(FONT_FAMILY, 9, "bold"), fg=SUMMARY_ACCENT, bg=SUMMARY_BG).pack(anchor="w", pady=(0, 16))

        # Subtotal
        sub_row = tk.Frame(summary_card, bg=SUMMARY_BG)
        sub_row.pack(fill="x", pady=4)
        tk.Label(sub_row, text="Subtotal", font=(FONT_FAMILY, 10), fg=SUMMARY_TEXT, bg=SUMMARY_BG).pack(side="left")
        self.summary_subtotal_lbl = tk.Label(sub_row, text="$0.00", font=(FONT_FAMILY, 10, "bold"), fg="#FFFFFF", bg=SUMMARY_BG)
        self.summary_subtotal_lbl.pack(side="right")

        # Total Tax
        tax_row = tk.Frame(summary_card, bg=SUMMARY_BG)
        tax_row.pack(fill="x", pady=4)
        tk.Label(tax_row, text="Total Tax", font=(FONT_FAMILY, 10), fg=SUMMARY_TEXT, bg=SUMMARY_BG).pack(side="left")
        self.summary_tax_lbl = tk.Label(tax_row, text="$0.00", font=(FONT_FAMILY, 10, "bold"), fg="#FFFFFF", bg=SUMMARY_BG)
        self.summary_tax_lbl.pack(side="right")

        # Divider
        div = tk.Frame(summary_card, bg="#312E81", height=1)
        div.pack(fill="x", pady=14)

        # Grand Total
        grand_row = tk.Frame(summary_card, bg=SUMMARY_BG)
        grand_row.pack(fill="x", pady=4)
        tk.Label(grand_row, text="Grand Total", font=(FONT_FAMILY, 12, "bold"), fg="#FFFFFF", bg=SUMMARY_BG).pack(side="left")
        self.summary_grand_lbl = tk.Label(grand_row, text="$0.00", font=FONT_SUMMARY_TOTAL, fg="#FFFFFF", bg=SUMMARY_BG)
        self.summary_grand_lbl.pack(side="right")

    def _populate_initial_data(self):
        """Populate initial data matching the exact template in the screenshot."""
        self.company_name.set("PixelCraft Digital Studio")
        self.company_email.set("billing@pixelcraft.io")
        self.company_phone.set("+1 (555) 234-5678")
        self.company_address.set("100 Innovation Avenue, Suite 400, San Francisco, CA")

        self.client_name.set("Apex Global Technologies")
        self.client_email.set("accounts@apexglobal.com")
        self.invoice_number.set("INV-2026-042")
        self.invoice_date.set("10/14/2026")
        self.due_date.set("11/14/2026")

        self.notes_text.insert(
            "1.0",
            "Thank you for your business! Please send payments via wire transfer to Bank of America, Account #: 1234-5678-9012, Routing #: 987654321."
        )

        # Line Items from screenshot
        self.add_item_row(
            description="UI/UX Dashboard Redesign & Wireframing",
            qty=1,
            price=2500.00,
            tax=10
        )
        self.add_item_row(
            description="Frontend Development (React & Tailwind)",
            qty=40,
            price=75.00,
            tax=10
        )

    def add_item_row(self, description="", qty=1, price=0.0, tax=10):
        row = LineItemRow(
            self.items_container,
            on_change_callback=self.recalculate,
            on_delete_callback=self.delete_item_row,
            description=description,
            qty=qty,
            price=price,
            tax=tax
        )
        row.pack(fill="x", pady=2)
        self.line_items.append(row)
        self.recalculate()

    def delete_item_row(self, row):
        if len(self.line_items) <= 1:
            messagebox.showwarning("Notice", "An invoice must have at least one line item.")
            return
        self.line_items.remove(row)
        row.destroy()
        self.recalculate()

    def get_currency_symbol(self):
        return self.currency_symbols.get(self.currency_var.get(), "$")

    def recalculate(self):
        curr = self.get_currency_symbol()
        total_subtotal = 0.0
        total_tax = 0.0

        for row in self.line_items:
            base, tax, _ = row.calculate(curr)
            total_subtotal += base
            total_tax += tax

        grand_total = total_subtotal + total_tax

        self.summary_subtotal_lbl.config(text=f"{curr}{total_subtotal:,.2f}")
        self.summary_tax_lbl.config(text=f"{curr}{total_tax:,.2f}")
        self.summary_grand_lbl.config(text=f"{curr}{grand_total:,.2f}")

        return total_subtotal, total_tax, grand_total

    def get_invoice_data(self):
        curr = self.get_currency_symbol()
        subtotal, tax, grand = self.recalculate()

        items = []
        for row in self.line_items:
            items.append({
                "description": row.desc_entry.get(),
                "qty": row.qty_entry.get(),
                "price": row.price_entry.get(),
                "tax": row.tax_entry.get(),
                "subtotal": row.subtotal_label.cget("text")
            })

        return {
            "company": {
                "name": self.company_name.get(),
                "email": self.company_email.get(),
                "phone": self.company_phone.get(),
                "address": self.company_address.get(),
            },
            "client": {
                "name": self.client_name.get(),
                "email": self.client_email.get(),
                "invoice_number": self.invoice_number.get(),
                "invoice_date": self.invoice_date.get(),
                "due_date": self.due_date.get(),
            },
            "currency": self.currency_var.get(),
            "currency_symbol": curr,
            "items": items,
            "payment_terms": self.payment_terms_var.get(),
            "notes": self.notes_text.get("1.0", "end").strip(),
            "subtotal": subtotal,
            "total_tax": tax,
            "grand_total": grand,
        }

    def save_invoice(self):
        data = self.get_invoice_data()
        filename = f"{data['client']['invoice_number'] or 'invoice'}.json"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=filename,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Saved", f"Invoice successfully saved to:\n{save_path}")

    def download_print_invoice(self):
        data = self.get_invoice_data()
        filename = f"{data['client']['invoice_number'] or 'invoice'}.pdf"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=filename,
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not save_path:
            return

        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Error", "ReportLab is required for PDF generation.")
            return

        self._export_pdf(save_path, data)
        messagebox.showinfo("Success", f"Invoice PDF exported successfully:\n{save_path}")

    def _export_pdf(self, filepath, data):
        """Builds a styled PDF invoice matching the template layout."""
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            "Title",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor(DARK_BTN_BG)
        )
        subtitle_style = ParagraphStyle(
            "Sub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor(TEXT_MUTED)
        )
        label_style = ParagraphStyle(
            "Label",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor(TEXT_MUTED)
        )
        val_style = ParagraphStyle(
            "Val",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor(TEXT_MAIN)
        )

        # Header Title
        story.append(Paragraph("INVOICE", title_style))
        story.append(Paragraph(f"Invoice #: {data['client']['invoice_number']} | Date: {data['client']['invoice_date']}", subtitle_style))
        story.append(Spacer(1, 16))

        # Parties Info Table
        from_content = [
            Paragraph("<b>FROM (ISSUER)</b>", label_style),
            Paragraph(f"<b>{data['company']['name']}</b>", val_style),
            Paragraph(data['company']['email'], val_style),
            Paragraph(data['company']['phone'], val_style),
            Paragraph(data['company']['address'], val_style),
        ]

        to_content = [
            Paragraph("<b>BILL TO (CLIENT)</b>", label_style),
            Paragraph(f"<b>{data['client']['name']}</b>", val_style),
            Paragraph(data['client']['email'], val_style),
            Paragraph(f"Due Date: {data['client']['due_date']}", val_style),
        ]

        parties_data = [
            [from_content, to_content]
        ]
        parties_table = Table(parties_data, colWidths=[260, 260])
        parties_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (0, 0), 1, colors.HexColor(BORDER_COLOR)),
            ("BOX", (1, 0), (1, 0), 1, colors.HexColor(BORDER_COLOR)),
        ]))
        story.append(parties_table)
        story.append(Spacer(1, 16))

        # Line Items Table
        curr = data["currency_symbol"]
        table_rows = [
            ["DESCRIPTION", "QTY", "PRICE", "TAX (%)", "SUBTOTAL"]
        ]

        for item in data["items"]:
            table_rows.append([
                item["description"],
                item["qty"],
                f"{curr}{float(item['price'] or 0):,.2f}",
                f"{item['tax']}%",
                item["subtotal"]
            ])

        # Summary rows in table
        table_rows.append(["", "", "", "Subtotal:", f"{curr}{data['subtotal']:,.2f}"])
        table_rows.append(["", "", "", "Total Tax:", f"{curr}{data['total_tax']:,.2f}"])
        table_rows.append(["", "", "", "Grand Total:", f"{curr}{data['grand_total']:,.2f}"])

        items_table = Table(table_rows, colWidths=[240, 50, 75, 55, 100])
        items_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(TEXT_MUTED)),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ALIGN", (4, 0), (4, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, len(data['items'])), 0.5, colors.HexColor(BORDER_COLOR)),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("FONTNAME", (3, -3), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (3, -1), (-1, -1), colors.HexColor("#EEF2FF")),
            ("TEXTCOLOR", (3, -1), (-1, -1), colors.HexColor(PRIMARY_COLOR)),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 16))

        # Notes / Payment Terms
        if data["notes"] or data["payment_terms"]:
            notes_p = [
                Paragraph(f"<b>Payment Terms:</b> {data['payment_terms']}", label_style),
                Spacer(1, 4),
                Paragraph(f"<b>Notes:</b> {data['notes']}", val_style)
            ]
            notes_table = Table([[notes_p]], colWidths=[520])
            notes_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(BORDER_COLOR)),
                ("PADDING", (0, 0), (-1, -1), 10),
            ]))
            story.append(notes_table)

        doc.build(story)

    def show_live_preview(self):
        """Displays a clean modal window with live preview of the invoice."""
        data = self.get_invoice_data()
        curr = data["currency_symbol"]

        preview_win = tk.Toplevel(self)
        preview_win.title(f"Live Preview - {data['client']['invoice_number']}")
        preview_win.geometry("680x720")
        preview_win.configure(bg="#FFFFFF")

        container = tk.Frame(preview_win, bg="#FFFFFF", padx=30, pady=24)
        container.pack(fill="both", expand=True)

        # Header
        top = tk.Frame(container, bg="#FFFFFF")
        top.pack(fill="x", pady=(0, 16))
        tk.Label(top, text="INVOICE", font=(FONT_FAMILY, 18, "bold"), fg=DARK_BTN_BG, bg="#FFFFFF").pack(side="left")
        tk.Label(top, text=f"{data['client']['invoice_number']}\nDate: {data['client']['invoice_date']}", font=(FONT_FAMILY, 9), fg=TEXT_MUTED, bg="#FFFFFF", justify="right").pack(side="right")

        # Parties
        parties = tk.Frame(container, bg="#F8FAFC", padx=16, pady=12, highlightthickness=1, highlightbackground=BORDER_COLOR)
        parties.pack(fill="x", pady=(0, 16))

        p_left = tk.Frame(parties, bg="#F8FAFC")
        p_left.pack(side="left", fill="both", expand=True)
        tk.Label(p_left, text="FROM:", font=(FONT_FAMILY, 8, "bold"), fg=PRIMARY_COLOR, bg="#F8FAFC").pack(anchor="w")
        tk.Label(p_left, text=data['company']['name'], font=(FONT_FAMILY, 10, "bold"), fg=TEXT_MAIN, bg="#F8FAFC").pack(anchor="w")
        tk.Label(p_left, text=data['company']['email'], font=(FONT_FAMILY, 8), fg=TEXT_MUTED, bg="#F8FAFC").pack(anchor="w")
        tk.Label(p_left, text=data['company']['address'], font=(FONT_FAMILY, 8), fg=TEXT_MUTED, bg="#F8FAFC").pack(anchor="w")

        p_right = tk.Frame(parties, bg="#F8FAFC")
        p_right.pack(side="right", fill="both", expand=True)
        tk.Label(p_right, text="BILL TO:", font=(FONT_FAMILY, 8, "bold"), fg=PRIMARY_COLOR, bg="#F8FAFC").pack(anchor="w")
        tk.Label(p_right, text=data['client']['name'], font=(FONT_FAMILY, 10, "bold"), fg=TEXT_MAIN, bg="#F8FAFC").pack(anchor="w")
        tk.Label(p_right, text=data['client']['email'], font=(FONT_FAMILY, 8), fg=TEXT_MUTED, bg="#F8FAFC").pack(anchor="w")
        tk.Label(p_right, text=f"Due: {data['client']['due_date']}", font=(FONT_FAMILY, 8), fg=TEXT_MUTED, bg="#F8FAFC").pack(anchor="w")

        # Line items summary
        items_frame = tk.Frame(container, bg="#FFFFFF")
        items_frame.pack(fill="x", pady=(0, 16))

        hdr = tk.Frame(items_frame, bg="#F1F5F9", pady=4)
        hdr.pack(fill="x")
        tk.Label(hdr, text="DESCRIPTION", font=(FONT_FAMILY, 8, "bold"), fg=TEXT_MUTED, bg="#F1F5F9").pack(side="left", padx=8)
        tk.Label(hdr, text="SUBTOTAL", font=(FONT_FAMILY, 8, "bold"), fg=TEXT_MUTED, bg="#F1F5F9").pack(side="right", padx=8)

        for it in data["items"]:
            r = tk.Frame(items_frame, bg="#FFFFFF", pady=4)
            r.pack(fill="x")
            tk.Label(r, text=f"{it['description']} (x{it['qty']} @ {curr}{it['price']})", font=(FONT_FAMILY, 9), fg=TEXT_MAIN, bg="#FFFFFF").pack(side="left", padx=8)
            tk.Label(r, text=it["subtotal"], font=(FONT_FAMILY, 9, "bold"), fg=TEXT_MAIN, bg="#FFFFFF").pack(side="right", padx=8)

        # Total summary bar
        tot_frame = tk.Frame(container, bg=SUMMARY_BG, padx=16, pady=12)
        tot_frame.pack(fill="x", pady=(0, 16))
        tk.Label(tot_frame, text=f"Grand Total:  {curr}{data['grand_total']:,.2f}", font=(FONT_FAMILY, 13, "bold"), fg="#FFFFFF", bg=SUMMARY_BG).pack(side="right")


def main():
    print("Starting Invoice Generator GUI...")
    app = InvoiceGeneratorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
