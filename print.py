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
        """Get list of available printers"""
        try:
            if self.os_type == "windows":
                printers = []
                for printer in self.win32print.EnumPrinters(2):
                    printers.append(printer[2])
                return printers

            elif self.os_type in ["darwin", "linux"]:
                result = subprocess.run(
                    ["lpstat", "-a"], capture_output=True, text=True
                )
                if result.returncode == 0 and result.stdout:
                    # Parse printer names from lpstat output
                    printers = []
                    for line in result.stdout.splitlines():
                        if line.strip():
                            printer_name = line.split()[0]
                            printers.append(printer_name)
                    return printers

                # Try alternative command if lpstat -a fails
                result = subprocess.run(
                    ["lpinfo", "-v"], capture_output=True, text=True
                )
                if result.returncode == 0 and result.stdout:
                    printers = []
                    for line in result.stdout.splitlines():
                        if "network" in line or "usb" in line:
                            printer_name = line.split()[-1]
                            printers.append(printer_name)
                    return printers

            return []

        except Exception as e:
            logger.error(f"Error getting printers: {str(e)}")
            return []

    def print_file(self, file_path, printer_name=None):
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

                # Add -o raw for direct printing
                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Printing failed: {result.stderr}")

            else:
                raise Exception(f"Unsupported operating system: {self.os_type}")

            time.sleep(2)
            logger.info(f"Successfully sent to printer: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error printing {file_path}: {str(e)}")
            return False


def select_printer(printer_system):
    """Allow user to select a printer from available printers"""
    printers = printer_system.get_available_printers()

    if not printers:
        print("\nNo printers found! Please check if:")
        print("1. Printers are properly connected")
        print("2. CUPS is installed (for Linux/macOS)")
        print("3. Printer drivers are installed")
        print("\nTo install CUPS on Linux:")
        print("sudo apt-get install cups cups-client")
        print("sudo systemctl start cups")
        print("sudo systemctl enable cups")
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
    """
    Go through each folder and print all PDFs in order.
    """
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
            else:
                failed_prints.append(pdf_path)

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
    base_directory = "split_pdfs"  # Change this to your directory path

    try:
        printer_system = PrinterSystem()
        print(f"Operating System: {platform.system()}")

        # Let user select printer
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
