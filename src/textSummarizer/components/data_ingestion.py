import os
from textSummarizer.logging import logger
from huggingface_hub import snapshot_download
from textSummarizer.entity import  DataIngestionConfig

class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config

    def download_data(self):
    # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config.root_dir), exist_ok=True)

        if not os.path.exists(self.config.root_dir) or not os.listdir(self.config.root_dir):
            logger.info("Starting data download...")
            snapshot_download(
                repo_id = self.config.repo_id,
                repo_type = "dataset",
                local_dir = self.config.root_dir,
                local_dir_use_symlinks = self.config.local_dir_use_symlinks,
            )
            
            logger.info(
                f"Data downloaded successfully!"
            )
        else:
            logger.info("Files already exists. Skipping download.")
