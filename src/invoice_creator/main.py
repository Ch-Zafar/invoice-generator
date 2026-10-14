import sys
import argparse
from pathlib import Path

# Ensure src directory is in sys.path when executed directly as a script
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from invoice_creator import InvoiceGenerator


def prompt_user_input() -> dict:
    """Interactively prompts the user for invoice details in the terminal."""
    print("\n--- Sales Tax Invoice Generator ---")

    date = input("Enter Date (e.g. 29-08-26): ").strip()
    while not date:
        print("Date cannot be empty.")
        date = input("Enter Date (e.g. 29-08-26): ").strip()

    invoice_no = input("Enter Invoice # (e.g. 9000036): ").strip()
    while not invoice_no:
        print("Invoice # cannot be empty.")
        invoice_no = input("Enter Invoice #: ").strip()

    quantity = input("Enter Quantity in M.TN (e.g. 62): ").strip()
    while not quantity:
        print("Quantity cannot be empty.")
        quantity = input("Enter Quantity: ").strip()

    rate = input("Enter Rate per unit (e.g. 5000): ").strip()
    while not rate:
        print("Rate cannot be empty.")
        rate = input("Enter Rate: ").strip()

    buyer_name = input("Enter Buyer Name: ").strip()
    while not buyer_name:
        print("Buyer Name cannot be empty.")
        buyer_name = input("Enter Buyer Name: ").strip()

    buyer_address = input("Enter Buyer Address: ").strip()
    while not buyer_address:
        print("Buyer Address cannot be empty.")
        buyer_address = input("Enter Buyer Address: ").strip()

    buyer_ntn = input("Enter Buyer NTN #: ").strip()
    while not buyer_ntn:
        print("Buyer NTN # cannot be empty.")
        buyer_ntn = input("Enter Buyer NTN #: ").strip()

    hs_code_input = input("Enter HS Code [default: 2303-2000]: ").strip()
    hs_code = hs_code_input if hs_code_input else "2303-2000"

    gst_rate_input = input("Enter GST Rate % [default: 18]: ").strip()
    gst_rate = gst_rate_input if gst_rate_input else "18"

    return {
        "date": date,
        "invoice_no": invoice_no,
        "quantity": quantity,
        "rate": rate,
        "buyer_name": buyer_name,
        "buyer_address": buyer_address,
        "buyer_ntn": buyer_ntn,
        "hs_code": hs_code,
        "gst_rate": gst_rate,
    }


def generate_invoice(
    date: str,
    invoice_no: str,
    quantity: float | int | str,
    rate: float | int | str,
    buyer_name: str,
    buyer_address: str,
    buyer_ntn: str,
    hs_code: str = "2303-2000",
    gst_rate: float | int | str = 18.0,
    stamp_image: str = "stamp.png",
    output_filename: str = "report.pdf",
) -> str:
    """Creates and builds an invoice using InvoiceGenerator."""
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
    )
    return generator.build(output_filename)


def main(argv=None):
    args_list = sys.argv[1:] if argv is None else argv

    if "--gui" in args_list:
        from .gui import main as run_gui
        run_gui()
        return

    # When run without CLI flags, prompt the user interactively
    if not args_list:
        data = prompt_user_input()
        generator = InvoiceGenerator(
            date=data["date"],
            invoice_no=data["invoice_no"],
            quantity=data["quantity"],
            rate=data["rate"],
            buyer_name=data["buyer_name"],
            buyer_address=data["buyer_address"],
            buyer_ntn=data["buyer_ntn"],
            hs_code=data["hs_code"],
            gst_rate=data["gst_rate"],
            stamp_image="stamp.png",
        )
        output_path = generator.build("report.pdf")
        print(f"\nInvoice successfully generated: {output_path}")
        return

    # When CLI flags are supplied, parse them
    parser = argparse.ArgumentParser(
        description="Generate a sales tax invoice PDF. If no options are given, prompts interactively."
    )
    parser.add_argument("--date", required=True, help="Invoice date (required, e.g. 29-08-26)")
    parser.add_argument("--invoice-no", required=True, help="Invoice number (required, e.g. 9000036)")
    parser.add_argument("--quantity", required=True, help="Quantity in M.TN (required, e.g. 62)")
    parser.add_argument("--rate", required=True, help="Rate per unit (required, e.g. 5000)")
    parser.add_argument("--buyer-name", required=True, help="Buyer name (required)")
    parser.add_argument("--buyer-address", required=True, help="Buyer address (required)")
    parser.add_argument("--buyer-ntn", required=True, help="Buyer NTN number (required)")
    parser.add_argument("--hs-code", default="2303-2000", help="HS Code (default: 2303-2000)")
    parser.add_argument("--gst-rate", default=18.0, help="GST Rate percentage (default: 18)")
    parser.add_argument("--stamp", default="stamp.png", help="Path to custom stamp image (default: stamp.png)")
    parser.add_argument("--output", default="report.pdf", help="Output PDF file path (default: report.pdf)")

    args = parser.parse_args(args_list)

    generator = InvoiceGenerator(
        date=args.date,
        invoice_no=args.invoice_no,
        quantity=args.quantity,
        rate=args.rate,
        buyer_name=args.buyer_name,
        buyer_address=args.buyer_address,
        buyer_ntn=args.buyer_ntn,
        hs_code=args.hs_code,
        gst_rate=args.gst_rate,
        stamp_image=args.stamp,
    )

    output_path = generator.build(args.output)
    print(f"Invoice successfully generated: {output_path}")


if __name__ == "__main__":
    main()
