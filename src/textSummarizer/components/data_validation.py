import os
from textSummarizer.logging import logger
from textSummarizer.entity import DataValidationConfig

class DataValidation:
    def __init__(self, config: DataValidationConfig):
        self.config = config

    def validate_all_files_exist(self)->bool:
        try:
            status = None

            all_files = os.listdir(os.path.join("artifacts","data_ingestion", "samsum_dataset"))

            for file in self.config.ALL_REQUIRED_FILES:
                if file in self.config.ALL_REQUIRED_FILES:
                    status = True
                    with open(self.config.STATUS_FILE, "w") as f:
                        f.write(f"Validation status: {status} \n")
                else:
                    status = False
                    with open(self.config.STATUS_FILE, "w") as f:
                        f.write(f"Validation status: {status} \n")
            return status
        except Exception as e:
            raise e