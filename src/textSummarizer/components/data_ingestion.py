import os
import urllib.request as request
import zipfile
from textSummarizer.logging import logger
from textSummarizer.utils.common import get_size

class DataIngestion:
    def __init__(self, config):
        self.config = config

    def download_data(self):
    # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config.local_data_file), exist_ok=True)

        if not os.path.exists(self.config.local_data_file):
            logger.info("Starting data download...")
            filename, headers = request.urlretrieve(
                url=self.config.source_URL,
                filename=str(self.config.local_data_file),
            )
            logger.info(
                f"Data downloaded successfully!\nFile: {filename}\nHeaders:\n{headers}"
            )
        else:
            logger.info("File already exists. Skipping download.")

    def extract_zip_file(self):

        unzip_path = self.config.unzip_dir
        os.makedirs(unzip_path, exist_ok=True)
        with zipfile.ZipFile(self.config.local_data_file, "r") as zip_ref:
            logger.info("Extracting zip file...")
            zip_ref.extractall(unzip_path)
            logger.info(f"Extraction completed at location: {unzip_path}")
