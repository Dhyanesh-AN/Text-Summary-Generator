import os
import pandas as pd
from textSummarizer.logging import logger
from textSummarizer.entity import DataValidationConfig

class DataValidation:
    def __init__(self, config: DataValidationConfig):
        self.config = config

    def validate_all_files_exist(self) -> bool:
        try:
            all_files = os.listdir(self.config.root_dir)
            
            # Check if all required files exist
            status = all(file in all_files for file in self.config.ALL_REQUIRED_FILES)
            
            # Write status once
            with open(self.config.STATUS_FILE, "w") as f:
                f.write(f"File Existence Validation status: {status}\n")
            logger.info(f"Files Existence Validated with status {status}")
            
            return status
        except Exception as e:
            raise e
    
    def validate_all_columns(self) -> bool:
        try:
            all_files = os.listdir(self.config.root_dir)
            csv_files = [file for file in all_files if file.endswith('.csv')]
            
            if not csv_files:
                logger.warning("No CSV files found in the directory")
                return False
            
            all_columns_valid = True
            for csv_file in csv_files:
                file_path = os.path.join(self.config.root_dir, csv_file)
                df = pd.read_csv(file_path)
                
                missing_columns = [col for col in self.config.ALL_REQUIRED_COLUMNS if col not in df.columns]
                
                if missing_columns:
                    logger.error(f"File {csv_file} is missing columns: {missing_columns}")
                    all_columns_valid = False
                else:
                    logger.info(f"File {csv_file} contains all required columns")
            
            # Append status to file
            with open(self.config.STATUS_FILE, "a") as f:
                f.write(f"Column Validation status: {all_columns_valid}\n")
            
            return all_columns_valid
        except Exception as e:
            raise e
    
    def validate_missing_values(self) -> bool:
        try:
            all_files = os.listdir(self.config.root_dir)
            csv_files = [file for file in all_files if file.endswith('.csv')]
            
            if not csv_files:
                logger.warning("No CSV files found in the directory")
                return False
            
            no_missing_values = True
            for csv_file in csv_files:
                file_path = os.path.join(self.config.root_dir, csv_file)
                df = pd.read_csv(file_path)
                
                missing_values = df.isnull().sum()
                
                if missing_values.sum() > 0:
                    logger.warning(f"File {csv_file} contains missing values:\n{missing_values[missing_values > 0]}")
                    no_missing_values = False
                else:
                    logger.info(f"File {csv_file} contains no missing values")
            
            # Append status to file
            with open(self.config.STATUS_FILE, "a") as f:
                f.write(f"Missing Values Validation status: {no_missing_values}\n")
            
            return no_missing_values
        except Exception as e:
            raise e