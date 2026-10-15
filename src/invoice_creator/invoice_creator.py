from invoice_creator.excel_reader import get_next_invoice_number
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle




def number_to_words(n: int) -> str:
    """Converts a non-negative integer to English words."""
    if n == 0:
        return "Zero"

    ones = [
        "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen",
    ]
    tens = [
        "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety",
    ]
    scales = [
        (1_000_000_000, "Billion"),
        (1_000_000, "Million"),
        (1_000, "Thousand"),
        (100, "Hundred"),
    ]

    words = []
    for scale, name in scales:
        if n >= scale:
            count = n // scale
            n %= scale
            if scale == 100:
                words.append(f"{ones[count]} Hundred")
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


def format_number(val: float | int | str) -> str:
    """Formats a number with commas, omitting decimals if whole."""
    if isinstance(val, str):
        cleaned = val.replace(",", "").replace("%", "").strip()
        num = float(cleaned)
    else:
        num = float(val)

    if num.is_integer():
        return f"{int(num):,}"
    return f"{num:,.2f}"


def calculate_totals(quantity: float | int | str, rate: float | int | str, gst_rate: float | int | str = 18.0) -> dict:
    """Calculates tax amounts and totals from quantity, rate, and GST percentage."""
    qty = float(str(quantity).replace(",", "").strip())
    rt = float(str(rate).replace(",", "").strip())
    gst = float(str(gst_rate).replace(",", "").replace("%", "").strip())

    value_excl = qty * rt
    gst_amount = value_excl * (gst / 100.0)
    value_incl = value_excl + gst_amount

    return {
        "quantity": qty,
        "rate": rt,
        "gst_rate": gst,
        "value_excl": value_excl,
        "gst_amount": gst_amount,
        "value_incl": value_incl,
        "quantity_display": format_number(qty),
        "rate_display": format_number(rt),
        "gst_rate_display": format_number(gst),
        "value_excl_display": format_number(value_excl),
        "gst_amount_display": format_number(gst_amount),
        "value_incl_display": format_number(value_incl),
    }


def resolve_asset_path(filename: str | Path | None) -> Path | None:
    """Finds an asset file path relative to current directory or project root."""
    if not filename:
        return None
    path = Path(filename)
    if path.is_file():
        return path

    project_root = Path(__file__).resolve().parent.parent.parent
    root_path = project_root / filename
    if root_path.is_file():
        return root_path

    return None


def create_invoice_pdf(data: dict, output_filename: str = "report.pdf") -> str:
    """Generates the sales tax invoice PDF matching the official template."""
    # 1. Calculations
    totals = calculate_totals(
        quantity=data["quantity"],
        rate=data["rate"],
        gst_rate=data.get("gst_rate", 18.0),
    )

    # 2. Setup document with A4 page size and margins for letterhead
    pdf = SimpleDocTemplate(
        output_filename,
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

    # Title
    story.append(Paragraph("Sales Tax Invoice", title_style))
    story.append(Spacer(1, 14))

    # Seller & Buyer Boxes
    seller_name = data.get("seller_name", "CHAUDRY TRADERS")
    seller_address = data.get("seller_address", "166-K Wapda City<br/>Expressway Faisalabad").replace("\n", "<br/>")
    seller_tax = data.get("seller_sales_tax", "32-77-8763-790-88")
    seller_ntn = data.get("seller_ntn", "1062600-5")

    buyer_name = data["buyer_name"]
    buyer_address = str(data["buyer_address"]).replace("\n", "<br/>")
    buyer_tax = data.get("buyer_sales_tax", "08-90-9991-573-19")
    buyer_ntn = data["buyer_ntn"]

    seller_table = Table(
        [
            [Paragraph("Seller's Name:", box_label_style), Paragraph(seller_name, box_val_style)],
            [Paragraph("Address:", box_label_style), Paragraph(seller_address, box_val_style)],
            [Paragraph("Sales Tax #", box_label_style), Paragraph(seller_tax, box_val_style)],
            [Paragraph("NTN #", box_label_style), Paragraph(seller_ntn, box_val_style)],
        ],
        colWidths=[70, 175],
    )
    seller_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    buyer_table = Table(
        [
            [Paragraph("Buyer's<br/>Name:", box_label_style), Paragraph(buyer_name, box_val_style)],
            [Paragraph("Address:", box_label_style), Paragraph(buyer_address, box_val_style)],
            [Paragraph("Sales Tax #", box_label_style), Paragraph(buyer_tax, box_val_style)],
            [Paragraph("NTN #", box_label_style), Paragraph(buyer_ntn, box_val_style)],
        ],
        colWidths=[65, 180],
    )
    buyer_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    info_table = Table([[seller_table, "", buyer_table]], colWidths=[245, 33.27, 245])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8))

    # Invoice # and Date (Right Aligned)
    invoice_no = get_next_invoice_number()
    inv_meta_table = Table(
        [
            ["INV #", invoice_no],
            ["Date:", str(data["date"])],
        ],
        colWidths=[48, 82],
        hAlign="RIGHT",
    )
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

    # Items Table
    description = data.get("description", "BAGASS")
    hs_code = data.get("hs_code", "2303-2000")

    table_data = [
        # Header Row 0
        ["Date", "Quantity\nM.TN", "HS CODE", "Description", "Rate", "Value\nExcluding\nSales Tax", "G.S. T", "", "Value\nIncluding\nSales Tax"],
        # Sub-header Row 1
        ["", "", "", "", "", "", "Rate%", "Amount", ""],
        # Data Row 2
        [
            str(data["date"]),
            totals["quantity_display"],
            hs_code,
            description,
            totals["rate_display"],
            totals["value_excl_display"],
            totals["gst_rate_display"],
            totals["gst_amount_display"],
            totals["value_incl_display"],
        ],
        # Total Row 3
        [
            "TOTAL",
            totals["quantity_display"],
            "",
            "",
            "",
            totals["value_excl_display"],
            "",
            totals["gst_amount_display"],
            totals["value_incl_display"],
        ],
    ]

    items_table = Table(table_data, colWidths=[62, 50, 48, 66, 38, 72, 37, 62, 88.27])
    items_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Spans
        ("SPAN", (0, 0), (0, 1)),
        ("SPAN", (1, 0), (1, 1)),
        ("SPAN", (2, 0), (2, 1)),
        ("SPAN", (3, 0), (3, 1)),
        ("SPAN", (4, 0), (4, 1)),
        ("SPAN", (5, 0), (5, 1)),
        ("SPAN", (6, 0), (7, 0)),
        ("SPAN", (8, 0), (8, 1)),
        # Grid lines
        ("GRID", (0, 0), (-1, 1), 0.75, colors.black),
        ("GRID", (0, 2), (-1, 2), 0.75, colors.black),
        # Total Row lines
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("ALIGN", (0, 3), (0, 3), "LEFT"),
        ("LEFTPADDING", (0, 3), (0, 3), 4),
        ("LINEABOVE", (0, 3), (-1, 3), 0.75, colors.black),
        ("LINEBELOW", (0, 3), (-1, 3), 0.75, colors.black),
        ("LINEBEFORE", (0, 3), (0, 3), 0.75, colors.black),
        ("LINEAFTER", (-1, 3), (-1, 3), 0.75, colors.black),
        ("LINEAFTER", (1, 3), (1, 3), 0.75, colors.black),
        ("LINEBEFORE", (5, 3), (5, 3), 0.75, colors.black),
        ("LINEAFTER", (5, 3), (5, 3), 0.75, colors.black),
        ("LINEBEFORE", (7, 3), (7, 3), 0.75, colors.black),
        ("LINEAFTER", (7, 3), (7, 3), 0.75, colors.black),
        ("LINEAFTER", (8, 3), (8, 3), 0.75, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 14))

    # Amount in Words
    words = number_to_words(int(round(totals["value_incl"])))
    amount_text = f"<b>Amount in Rupess:</b> &nbsp;&nbsp; {words} Only"
    story.append(Paragraph(amount_text, amount_style))
    story.append(Spacer(1, 10))

    # Stamp image
    stamp_path = resolve_asset_path(data.get("stamp_image", "stamp.png"))
    if stamp_path:
        story.append(Image(str(stamp_path), width=95, height=95, hAlign="LEFT"))

    # Background canvas callback
    bg_path = resolve_asset_path(data.get("background_image", "background.png"))

    def draw_background(canvas, doc):
        if bg_path:
            canvas.saveState()
            width, height = doc.pagesize
            canvas.drawImage(str(bg_path), 0, 0, width=width, height=height, mask="auto")
            canvas.restoreState()

    pdf.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
    return output_filename


class InvoiceGenerator:
    """Simple class wrapper for invoice creation to support existing code."""

    def __init__(self, **kwargs):
        self.data = kwargs

    def build(self, filename: str = "report.pdf") -> str:
        return create_invoice_pdf(self.data, output_filename=filename)
