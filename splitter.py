import os
import re
from PyPDF2 import PdfReader, PdfWriter
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ClientDocument:
    def __init__(self, dz_code=None, pages=None, original_filename=None):
        self.dz_code = dz_code
        self.pages = pages or []
        self.original_filename = original_filename


def extract_dz_code(text):
    dz_pattern = r"DZ(\d+)"
    match = re.search(dz_pattern, text)

    if match:
        dz_code = f"DZ{match.group(1)}"
        logger.info(f"Found DZ code: {dz_code}")
        return dz_code

    return None


def save_client_document(client_doc, output_dir):
    if not client_doc.pages:
        logger.warning("No pages to save for client document")
        return

    # Create DZ code specific directory
    dz_directory = os.path.join(output_dir, client_doc.dz_code)
    if not os.path.exists(dz_directory):
        os.makedirs(dz_directory)
        logger.info(f"Created directory: {dz_directory}")

    # Create output filename using original filename and DZ code
    base_filename = os.path.splitext(os.path.basename(client_doc.original_filename))[0]
    output_filename = f"{base_filename}_{client_doc.dz_code}.pdf"
    output_path = os.path.join(dz_directory, output_filename)

    # Create PDF writer and add all pages
    pdf_writer = PdfWriter()
    for page in client_doc.pages:
        pdf_writer.add_page(page)

    # Save the PDF
    with open(output_path, "wb") as output_file:
        pdf_writer.write(output_file)

    logger.info(f"Saved document to: {output_path}")


def split_pdf_by_dz(input_pdf_path, output_dir):
    logger.info(f"Starting to process PDF: {input_pdf_path}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    try:
        pdf_reader = PdfReader(input_pdf_path)
        logger.info(f"Successfully opened PDF with {len(pdf_reader.pages)} pages")
    except Exception as e:
        logger.error(f"Failed to open PDF: {str(e)}")
        raise

    current_client = None

    for page_num in range(len(pdf_reader.pages)):
        logger.info(f"Processing page {page_num + 1}/{len(pdf_reader.pages)}")
        page = pdf_reader.pages[page_num]
        text = page.extract_text()
        dz_code = extract_dz_code(text)

        if dz_code:
            if current_client:
                save_client_document(current_client, output_dir)

            current_client = ClientDocument(
                dz_code=dz_code, pages=[page], original_filename=input_pdf_path
            )
            logger.info(f"Started new client document for DZ code: {dz_code}")
        elif current_client:
            logger.info("Adding continuation page to current client document")
            current_client.pages.append(page)
        else:
            logger.warning("Found page with no DZ code and no current client exists")

    if current_client:
        save_client_document(current_client, output_dir)


def main():
    input_pdf = "./bordereau_import-id_6692.pdf"
    output_directory = "split_pdfs"

    try:
        logger.info("Starting PDF splitting process")
        split_pdf_by_dz(input_pdf, output_directory)
        logger.info("PDF splitting completed successfully!")
    except Exception as e:
        logger.error(f"An error occurred during processing: {str(e)}")
        raise


if __name__ == "__main__":
    main()
