


import sys
from pathlib import Path
# 1. Add 'src' to sys.path so 'invoice_creator' is recognized as a package
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
# 2. If running directly from src/invoice_creator, remove current dir from sys.path[0]
#    so the file 'invoice_creator.py' does not shadow the package 'invoice_creator'
current_dir = Path(__file__).resolve().parent
if sys.path and sys.path[0] == str(current_dir):
    sys.path.pop(0)
# Now standard package imports work cleanly without conflicts:
from invoice_creator.excel_reader import get_next_invoice_number
from invoice_creator.invoice_creator import InvoiceGenerator



def main():
    next_inv = get_next_invoice_number()
    print(f"Next invoice number from Excel: {next_inv}")

    # Sample invoice record
    sample_data = {
        "buyer_name": "ABC Textile Mills Ltd",
        "buyer_address": "Plot 12, Industrial Area, Faisalabad",
        "buyer_ntn": "1234567-8",
        "date": "15-10-2026",
        "quantity": 10.0,
        "rate": 25000.0,
        "description": "COTTON YARN",
    }

    # 1. Instantiate the generator
    generator = InvoiceGenerator(**sample_data)

    # 2. Call .build() to actually create the PDF file
    output_file = generator.build(filename="invoice.pdf")
    print(f"Invoice PDF generated successfully: {output_file}")


if __name__ == "__main__":
    main()
