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
        """Initialize the appropriate printing system based on OS."""
        if self.os_type == "windows":
            try:
                import win32print
                import win32api

                self.win32print = win32print
                self.win32api = win32api
            except ImportError:
                logger.error("Please install pywin32: pip install pywin32")
                raise

    def get_default_printer(self):
        """Get default printer name for the current OS."""
        try:
            if self.os_type == "windows":
                return self.win32print.GetDefaultPrinter()

            elif self.os_type in ["darwin", "linux"]:
                # Try lpstat -d first
                result = subprocess.run(
                    ["lpstat", "-d"], capture_output=True, text=True
                )
                if result.returncode == 0 and result.stdout:
                    return result.stdout.strip().split(": ")[-1]

                # If no default printer, try to get first available printer
                result = subprocess.run(
                    ["lpstat", "-a"], capture_output=True, text=True
                )
                if result.returncode == 0 and result.stdout:
                    return result.stdout.split()[0]

            return None

        except Exception as e:
            logger.error(f"Error getting default printer: {str(e)}")
            return None

    def print_file(self, file_path, printer_name=None):
        """Print a file using the appropriate method for the current OS."""
        try:
            if self.os_type == "windows":
                if not printer_name:
                    printer_name = self.win32print.GetDefaultPrinter()

                self.win32api.ShellExecute(
                    0, "print", file_path, f'/d:"{printer_name}"', ".", 0
                )

            elif self.os_type in ["darwin", "linux"]:
                command = ["lp"]
                if printer_name:
                    command.extend(["-d", printer_name])
                command.append(file_path)

                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Printing failed: {result.stderr}")

            else:
                raise Exception(f"Unsupported operating system: {self.os_type}")

            # Wait for print job to be processed
            time.sleep(2)
            logger.info(f"Successfully sent to printer: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error printing {file_path}: {str(e)}")
            return False


def print_pdfs_in_folders(base_directory, printer_system, printer_name=None):
    """
    Go through each folder and print all PDFs in order.
    """
    logger.info(f"Starting to process directory: {base_directory}")

    # Check if base directory exists
    if not os.path.exists(base_directory):
        logger.error(f"Directory {base_directory} does not exist!")
        return

    # Get all folders in sorted order
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

        # Get all PDF files in the folder in sorted order
        pdf_files = sorted(
            [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
        )

        if not pdf_files:
            print(f"No PDF files found in {folder}")
            continue

        # Print each PDF in the folder
        for pdf_file in pdf_files:
            pdf_path = os.path.join(folder_path, pdf_file)
            print(f"Printing: {pdf_file}")

            if printer_system.print_file(pdf_path, printer_name):
                total_printed += 1
            else:
                failed_prints.append(pdf_path)

            # Wait between prints to avoid overwhelming the printer
            time.sleep(3)

    # Print summary
    print(f"\n{'='*50}")
    print("Printing Summary:")
    print(f"Total files printed: {total_printed}")
    if failed_prints:
        print("\nFailed to print the following files:")
        for failed_file in failed_prints:
            print(f"- {failed_file}")
    print("=" * 50)


def main():
    # Specify the base directory where the split PDFs are stored
    base_directory = "split_pdfs"  # Change this if your output directory is different

    try:
        # Initialize printer system
        printer_system = PrinterSystem()

        # Get default printer
        default_printer = printer_system.get_default_printer()
        if default_printer:
            print(f"\nDefault printer: {default_printer}")
        else:
            print("\nNo default printer found!")
            printer_name = input("Please enter printer name manually: ")
            if printer_name.strip():
                default_printer = printer_name
            else:
                print("No printer specified. Exiting.")
                return

        # Show current operating system
        print(f"Operating System: {platform.system()}")

        # Confirm before proceeding
        response = input("\nDo you want to proceed with printing? (yes/no): ")
        if response.lower() != "yes":
            print("Printing cancelled.")
            return

        print_pdfs_in_folders(base_directory, printer_system, default_printer)

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()

