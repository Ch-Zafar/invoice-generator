import os
from pathlib import Path
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Circle, String, PolyLine


def number_to_words(n: int) -> str:
    """Converts a non-negative integer to English words."""
    if n == 0:
        return "zero"

    ones = [
        "", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
        "seventeen", "eighteen", "nineteen"
    ]
    tens = [
        "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"
    ]
    scales = [
        (1_000_000_000, "billion"),
        (1_000_000, "million"),
        (1_000, "thousand"),
        (100, "hundred"),
    ]

    words = []
    for scale, name in scales:
        if n >= scale:
            count = n // scale
            n %= scale
            if scale == 100:
                words.append(f"{ones[count]} hundred")
            else:
                words.append(f"{number_to_words(count)} {name}")

    if n > 0:
        if n < 20:
            words.append(ones[n])
        else:
            t = tens[n // 10]
            o = ones[n % 10]
            words.append(f"{t}-{o}" if o else t)

    return " ".join(words)


class InvoiceGenerator:
    """Generates Sales Tax Invoices as PDF documents matching the official template."""

    def __init__(
        self,
        date: str,
        invoice_no: str,
        quantity: float | int | str,
        rate: float | int | str,
        buyer_name: str,
        buyer_address: str,
        buyer_ntn: str,
        hs_code: str = "2303-2000",
        buyer_sales_tax: str = "08-90-9991-573-19",
        description: str = "BAGASS",
        gst_rate: float = 18.0,
        seller_name: str = "CHAUDRY TRADERS",
        seller_address: str = "166-K Wapda City<br/>Expressway Faisalabad",
        seller_sales_tax: str = "32-77-8763-790-88",
        seller_ntn: str = "1062600-5",
        stamp_image: str = "stamp.png",
        stamp_width: float = 95,
        stamp_height: float = 95,
        background_image: str = "background.png",
    ):
        self.date = str(date)
        self.invoice_no = str(invoice_no)
        self.hs_code = str(hs_code)
        self.quantity = quantity
        self.rate = rate
        self.buyer_name = buyer_name
        self.buyer_address = str(buyer_address).replace("\n", "<br/>")
        self.buyer_ntn = str(buyer_ntn)
        self.buyer_sales_tax = str(buyer_sales_tax)
        self.description = description
        self.gst_rate = self._parse_number(gst_rate)
        self.seller_name = seller_name
        self.seller_address = str(seller_address).replace("\n", "<br/>")
        self.seller_sales_tax = str(seller_sales_tax)
        self.seller_ntn = str(seller_ntn)
        self.stamp_image = stamp_image
        self.stamp_width = stamp_width
        self.stamp_height = stamp_height
        self.background_image = background_image

    @staticmethod
    def _parse_number(val: float | int | str) -> float:
        if isinstance(val, (int, float)):
            return float(val)
        cleaned = str(val).replace(",", "").replace("%", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @staticmethod
    def _format_number(val: float) -> str:
        if val.is_integer():
            return f"{int(val):,}"
        return f"{val:,.2f}"

    def _resolve_path(self, path: str | None) -> str | None:
        if not path:
            return None
        if os.path.isabs(path) and os.path.exists(path):
            return path
        if os.path.exists(path):
            return path
        # Check relative to cwd
        cwd_path = os.path.join(os.getcwd(), path)
        if os.path.exists(cwd_path):
            return cwd_path
        # Check relative to project root
        project_root = Path(__file__).resolve().parent.parent.parent
        root_path = project_root / path
        if root_path.exists():
            return str(root_path)
        return path

    def draw_background(self, canvas, doc):
        """Draws the letterhead background image behind the content on each page."""
        canvas.saveState()
        bg_path = self._resolve_path(self.background_image)
        if bg_path and os.path.exists(bg_path):
            width, height = doc.pagesize
            canvas.drawImage(bg_path, 0, 0, width=width, height=height, mask="auto")
        canvas.restoreState()

    def create_stamp(self):
        """Returns a stamp Flowable (uses custom stamp image if available, else vector stamp)."""
        stamp_path = self._resolve_path(self.stamp_image)
        if stamp_path and os.path.exists(stamp_path):
            return Image(stamp_path, width=self.stamp_width, height=self.stamp_height, hAlign="LEFT")

        # Vector circular stamp fallback matching Chaudhry Traders
        d = Drawing(105, 105)
        d.add(Circle(52, 52, 46, fillColor=None, strokeColor=colors.black, strokeWidth=1.5))
        d.add(Circle(52, 52, 42, fillColor=None, strokeColor=colors.black, strokeWidth=0.8))
        d.add(String(24, 76, "CHAUDHRY", fontName="Helvetica-Bold", fontSize=7.5, fillColor=colors.black))
        d.add(String(29, 22, "TRADERS", fontName="Helvetica-Bold", fontSize=7.5, fillColor=colors.black))
        d.add(PolyLine(
            [(30, 48), (38, 62), (44, 38), (52, 65), (60, 40), (68, 55), (78, 48)],
            strokeColor=colors.black,
            strokeWidth=1.2,
        ))
        return d

    def build(self, filename: str = "report.pdf") -> str:
        """Builds and saves the invoice PDF."""
        # Page dimensions and document setup (A4 with space for letterhead header and footer)
        pdf = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=115,
            bottomMargin=65,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=1,  # Center
            textColor=colors.black,
        )

        box_label_style = ParagraphStyle(
            "BoxLabel",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.black,
        )

        box_val_style = ParagraphStyle(
            "BoxValue",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.black,
        )

        amount_style = ParagraphStyle(
            "AmountStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.black,
        )

        story = []

        # 1. Title: Sales Tax Invoice
        story.append(Paragraph("Sales Tax Invoice", title_style))
        story.append(Spacer(1, 14))

        # 2. Seller and Buyer Information Boxes
        seller_data = [
            [Paragraph("Seller's Name:", box_label_style), Paragraph(self.seller_name, box_val_style)],
            [Paragraph("Address:", box_label_style), Paragraph(self.seller_address, box_val_style)],
            [Paragraph("Sales Tax #", box_label_style), Paragraph(self.seller_sales_tax, box_val_style)],
            [Paragraph("NTN #", box_label_style), Paragraph(self.seller_ntn, box_val_style)],
        ]

        seller_box = Table(seller_data, colWidths=[70, 175])
        seller_box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))

        buyer_data = [
            [Paragraph("Buyer's<br/>Name:", box_label_style), Paragraph(self.buyer_name, box_val_style)],
            [Paragraph("Address:", box_label_style), Paragraph(self.buyer_address, box_val_style)],
            [Paragraph("Sales Tax #", box_label_style), Paragraph(self.buyer_sales_tax, box_val_style)],
            [Paragraph("NTN #", box_label_style), Paragraph(self.buyer_ntn, box_val_style)],
        ]

        buyer_box = Table(buyer_data, colWidths=[65, 180])
        buyer_box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))

        # Place Seller & Buyer boxes side-by-side (Total width = 523.27 pt)
        info_table = Table([[seller_box, "", buyer_box]], colWidths=[245, 33.27, 245])
        info_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 8))

        # 3. Invoice Number & Date (Right Aligned)
        inv_meta_data = [
            ["INV #", self.invoice_no],
            ["Date:", self.date],
        ]
        inv_meta_table = Table(inv_meta_data, colWidths=[48, 82], hAlign="RIGHT")
        inv_meta_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(inv_meta_table)
        story.append(Spacer(1, 10))

        # 4. Main Items Table with GST Columns
        qty_num = self._parse_number(self.quantity)
        rate_num = self._parse_number(self.rate)
        value_excl = qty_num * rate_num
        gst_amount = value_excl * (self.gst_rate / 100.0)
        value_incl = value_excl + gst_amount

        qty_display = self._format_number(qty_num)
        rate_display = self._format_number(rate_num)
        value_excl_display = self._format_number(value_excl)
        gst_rate_display = self._format_number(self.gst_rate)
        gst_amount_display = self._format_number(gst_amount)
        value_incl_display = self._format_number(value_incl)

        table_data = [
            # Row 0: Header Top
            [
                "Date",
                "Quantity\nM.TN",
                "HS CODE",
                "Description",
                "Rate",
                "Value\nExcluding\nSales Tax",
                "G.S. T",
                "",
                "Value\nIncluding\nSales Tax",
            ],
            # Row 1: Sub-header for G.S. T
            [
                "",
                "",
                "",
                "",
                "",
                "",
                "Rate%",
                "Amount",
                "",
            ],
            # Row 2: Data Row
            [
                self.date,
                qty_display,
                self.hs_code,
                self.description,
                rate_display,
                value_excl_display,
                gst_rate_display,
                gst_amount_display,
                value_incl_display,
            ],
            # Row 3: TOTAL Row
            [
                "TOTAL",
                qty_display,
                "",
                "",
                "",
                value_excl_display,
                "",
                gst_amount_display,
                value_incl_display,
            ],
        ]

        col_widths = [62, 50, 48, 66, 38, 72, 37, 62, 88.27]
        items_table = Table(table_data, colWidths=col_widths)

        items_table_style = TableStyle([
            # Headers Font & Alignment
            ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LEADING", (0, 0), (-1, -1), 9.5),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

            # Multi-row/col header spans
            ("SPAN", (0, 0), (0, 1)),  # Date
            ("SPAN", (1, 0), (1, 1)),  # Quantity M.TN
            ("SPAN", (2, 0), (2, 1)),  # HS CODE
            ("SPAN", (3, 0), (3, 1)),  # Description
            ("SPAN", (4, 0), (4, 1)),  # Rate
            ("SPAN", (5, 0), (5, 1)),  # Value Excluding Sales Tax
            ("SPAN", (6, 0), (7, 0)),  # G.S. T (spans Rate% and Amount)
            ("SPAN", (8, 0), (8, 1)),  # Value Including Sales Tax

            # Grid lines for Header and Data
            ("GRID", (0, 0), (-1, 1), 0.75, colors.black),
            ("GRID", (0, 2), (-1, 2), 0.75, colors.black),

            # Total Row styling matching template
            ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
            ("ALIGN", (0, 3), (0, 3), "LEFT"),
            ("LEFTPADDING", (0, 3), (0, 3), 4),
            ("LINEABOVE", (0, 3), (-1, 3), 0.75, colors.black),
            ("LINEBELOW", (0, 3), (-1, 3), 0.75, colors.black),
            ("LINEBEFORE", (0, 3), (0, 3), 0.75, colors.black),  # outer left
            ("LINEAFTER", (-1, 3), (-1, 3), 0.75, colors.black),  # outer right
            ("LINEAFTER", (1, 3), (1, 3), 0.75, colors.black),   # after Quantity
            ("LINEBEFORE", (5, 3), (5, 3), 0.75, colors.black),  # before Value Excl
            ("LINEAFTER", (5, 3), (5, 3), 0.75, colors.black),   # after Value Excl
            ("LINEBEFORE", (7, 3), (7, 3), 0.75, colors.black),  # before GST Amount
            ("LINEAFTER", (7, 3), (7, 3), 0.75, colors.black),   # after GST Amount
            ("LINEAFTER", (8, 3), (8, 3), 0.75, colors.black),   # after Value Incl

            # Padding
            ("TOPPADDING", (0, 0), (-1, -1), 4.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ])

        items_table.setStyle(items_table_style)
        story.append(items_table)
        story.append(Spacer(1, 14))

        # 5. Amount in Words
        words = number_to_words(int(round(value_incl)))
        amount_text = f"<b>Amount in Rupess:</b> &nbsp;&nbsp; {words}"
        story.append(Paragraph(amount_text, amount_style))
        story.append(Spacer(1, 10))

        # 6. Stamp / Signature
        story.append(self.create_stamp())

        # Build Document
        pdf.build(
            story,
            onFirstPage=self.draw_background,
            onLaterPages=self.draw_background,
        )
        return filename

    def generate(self, filename: str = "report.pdf") -> str:
        """Alias for build()."""
        return self.build(filename)


def build_invoice(
    date: str,
    invoice_no: str,
    quantity: float | int | str,
    rate: float | int | str,
    buyer_name: str,
    buyer_address: str,
    buyer_ntn: str,
    hs_code: str = "2303-2000",
    gst_rate: float | int | str = 18.0,
    filename: str = "report.pdf",
    stamp_image: str = "stamp.png",
    **kwargs,
) -> str:
    """Convenience function to build an invoice using InvoiceGenerator."""
    generator = InvoiceGenerator(
        date=date,
        invoice_no=invoice_no,
        quantity=quantity,
        rate=rate,
        buyer_name=buyer_name,
        buyer_address=buyer_address,
        buyer_ntn=buyer_ntn,
        hs_code=hs_code,
        gst_rate=gst_rate,
        stamp_image=stamp_image,
        **kwargs,
    )
    return generator.build(filename)


def run_gui():
    """Launches the Tkinter GUI Invoice Generator."""
    from .gui import main as gui_main
    gui_main()


def main():
    """Main CLI entry point for the invoice-creator script."""
    from .main import main as run_main
    run_main()


if __name__ == "__main__":
    main()
