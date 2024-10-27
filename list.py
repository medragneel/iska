import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def list_pdfs_in_directory(base_directory):
    """
    Traverse through directories and list all PDF files.
    Prints a structured overview of folders and their PDF contents.
    """
    logger.info(f"Starting to scan directory: {base_directory}")

    # Check if base directory exists
    if not os.path.exists(base_directory):
        logger.error(f"Directory {base_directory} does not exist!")
        return

    # Track total counts
    total_folders = 0
    total_pdfs = 0

    # Get all items in the base directory
    try:
        items = sorted(os.listdir(base_directory))
    except Exception as e:
        logger.error(f"Error reading directory {base_directory}: {str(e)}")
        return

    # Print header
    print("\n" + "=" * 50)
    print(f"Contents of {base_directory}")
    print("=" * 50)

    # Go through each item in the directory
    for item in items:
        item_path = os.path.join(base_directory, item)

        # If it's a directory
        if os.path.isdir(item_path):
            total_folders += 1
            pdf_count = 0

            # Print folder name
            print(f"\n📁 Folder: {item}")

            try:
                # List contents of the folder
                folder_contents = sorted(os.listdir(item_path))

                # Print each PDF file
                for file in folder_contents:
                    if file.lower().endswith(".pdf"):
                        pdf_count += 1
                        total_pdfs += 1
                        file_size = (
                            os.path.getsize(os.path.join(item_path, file)) / 1024
                        )  # Size in KB
                        print(f"   📄 {file} ({file_size:.2f} KB)")

                if pdf_count == 0:
                    print("   (No PDF files found)")

            except Exception as e:
                logger.error(f"Error reading folder {item}: {str(e)}")

    # Print summary
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"Total folders: {total_folders}")
    print(f"Total PDF files: {total_pdfs}")
    print("=" * 50 + "\n")


def main():
    # Specify the base directory where the split PDFs are stored
    base_directory = "split_pdfs"  # Change this if your output directory is different

    try:
        list_pdfs_in_directory(base_directory)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()
