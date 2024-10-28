import os
import logging
import subprocess
import time
import platform
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PrinterSystem:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.setup_print_system()

    def setup_print_system(self):
        if self.os_type == "windows":
            try:
                import win32print
                import win32api

                self.win32print = win32print
                self.win32api = win32api
            except ImportError:
                logger.error("Please install pywin32: pip install pywin32")
                raise

    def get_available_printers(self):
        try:
            if self.os_type == "windows":
                printers = []
                for printer in self.win32print.EnumPrinters(
                    2
                ):  # 2 = PRINTER_ENUM_LOCAL
                    printers.append(printer[2])
                return printers

            elif self.os_type in ["darwin", "linux"]:
                result = subprocess.run(
                    ["lpstat", "-a"], capture_output=True, text=True
                )
                if result.returncode == 0 and result.stdout:
                    return [line.split()[0] for line in result.stdout.splitlines()]
            return []

        except Exception as e:
            logger.error(f"Error getting printers: {str(e)}")
            return []

    def print_file_windows(self, filename, printer_name):
        try:
            # Open the printer
            handle = self.win32print.OpenPrinter(printer_name)
            try:
                # Start a print job
                job = self.win32print.StartDocPrinter(
                    handle, 1, ("PDF Document", None, "RAW")
                )
                try:
                    # Start a page
                    self.win32print.StartPagePrinter(handle)

                    # Write the file directly to the printer
                    with open(filename, "rb") as f:
                        data = f.read()
                        self.win32print.WritePrinter(handle, data)

                    # End the page
                    self.win32print.EndPagePrinter(handle)

                finally:
                    # End the document
                    self.win32print.EndDocPrinter(handle)
            finally:
                # Close the printer
                self.win32print.ClosePrinter(handle)

            logger.info(f"Successfully sent {filename} to printer {printer_name}")
            return True

        except Exception as e:
            logger.error(f"Error printing file {filename} to {printer_name}: {str(e)}")
            return False

    def print_file(self, file_path, printer_name=None):
        try:
            if self.os_type == "windows":
                if not printer_name:
                    printer_name = self.win32print.GetDefaultPrinter()
                return self.print_file_windows(file_path, printer_name)

            elif self.os_type in ["darwin", "linux"]:
                command = ["lp"]
                if printer_name:
                    command.extend(["-d", printer_name])
                command.append(file_path)

                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Printing failed: {result.stderr}")

                logger.info(f"Successfully sent to printer: {file_path}")
                return True

            else:
                raise Exception(f"Unsupported operating system: {self.os_type}")

        except Exception as e:
            logger.error(f"Error printing {file_path}: {str(e)}")
            return False


def select_printer(printer_system):
    printers = printer_system.get_available_printers()

    if not printers:
        print("\nNo printers found!")
        if platform.system().lower() == "windows":
            print("Please check if:")
            print("1. Printers are properly connected and turned on")
            print("2. Printer drivers are installed")
            print("3. Printers are added to Windows")
            print("\nTo add a printer in Windows:")
            print("1. Go to Settings > Devices > Printers & scanners")
            print("2. Click 'Add a printer or scanner'")
        return None

    print("\nAvailable printers:")
    for i, printer in enumerate(printers, 1):
        print(f"{i}. {printer}")

    while True:
        try:
            choice = input("\nSelect printer number (or 'q' to quit): ")
            if choice.lower() == "q":
                return None

            index = int(choice) - 1
            if 0 <= index < len(printers):
                return printers[index]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


def print_pdfs_in_folders(base_directory, printer_system, printer_name=None):
    logger.info(f"Starting to process directory: {base_directory}")

    if not os.path.exists(base_directory):
        logger.error(f"Directory {base_directory} does not exist!")
        return

    folders = sorted(
        [
            f
            for f in os.listdir(base_directory)
            if os.path.isdir(os.path.join(base_directory, f))
        ]
    )

    total_printed = 0
    failed_prints = []

    for folder in folders:
        folder_path = os.path.join(base_directory, folder)
        logger.info(f"\nProcessing folder: {folder}")
        print(f"\n{'='*50}")
        print(f"Printing contents of folder: {folder}")
        print("=" * 50)

        pdf_files = sorted(
            [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
        )

        if not pdf_files:
            print(f"No PDF files found in {folder}")
            continue

        for pdf_file in pdf_files:
            pdf_path = os.path.join(folder_path, pdf_file)
            print(f"Printing: {pdf_file}")

            if printer_system.print_file(pdf_path, printer_name):
                total_printed += 1
                print(f"Successfully sent {pdf_file} to printer")
            else:
                failed_prints.append(pdf_path)
                print(f"Failed to print {pdf_file}")

            time.sleep(3)

    print(f"\n{'='*50}")
    print("Printing Summary:")
    print(f"Total files printed: {total_printed}")
    if failed_prints:
        print("\nFailed to print the following files:")
        for failed_file in failed_prints:
            print(f"- {failed_file}")
    print("=" * 50)


def main():
    base_directory = "split_pdfs"

    try:
        printer_system = PrinterSystem()
        print(f"Operating System: {platform.system()}")

        printer_name = select_printer(printer_system)
        if not printer_name:
            print("No printer selected. Exiting.")
            return

        print(f"\nSelected printer: {printer_name}")

        response = input("\nDo you want to proceed with printing? (yes/no): ")
        if response.lower() != "yes":
            print("Printing cancelled.")
            return

        print_pdfs_in_folders(base_directory, printer_system, printer_name)

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()

