import os
from textSummarizer.constant import *
from textSummarizer.utils.common import read_yaml, create_directories
from pathlib import Path
from textSummarizer.entity import (DataIngestionConfig,
                                   DataValidationConfig,
                                   DataTransformationConfig, ModelEvaluationConfig,
                                   ModelTrainerConfig)

class ConfigurationManager:
    def __init__(
        self,
        config_filepath: Path = CONFIG_FILE_PATH,
        params_filepath: Path = PARAMS_FILE_PATH,
    ):
        self.config = read_yaml(config_filepath)
        self.params = read_yaml(params_filepath)

        create_directories([self.config.artifacts_root])

    def get_data_ingestion_config(self) -> DataIngestionConfig:
        config = self.config.data_ingestion

        data_ingestion_config = DataIngestionConfig(
            root_dir = Path(config.root_dir),
            repo_id = config.repo_id,
            local_dir_use_symlinks = config.local_dir_use_symlinks,
        )

        return data_ingestion_config
    
    def get_data_validation_config(self) -> DataValidationConfig:
        config = self.config.data_validation

        os.makedirs(os.path.dirname(config.STATUS_FILE), exist_ok=True)

        data_validation_config = DataValidationConfig(
            root_dir=Path(config.root_dir),
            STATUS_FILE=config.STATUS_FILE,
            ALL_REQUIRED_FILES=config.ALL_REQUIRED_FILES,
            ALL_REQUIRED_COLUMNS=config.ALL_REQUIRED_COLUMNS,
        )

        return data_validation_config
    
    def get_data_transformation_config(self) -> DataTransformationConfig:
        config = self.config.data_transformation

        create_directories([config.root_dir])
        data_transformation_config = DataTransformationConfig(
            root_dir=Path(config.root_dir),
            data_path=Path(config.data_path),
            tokenizer_path=Path(config.tokenizer_path),
        )
        return data_transformation_config 
    
    def get_model_trainer_config(self) -> ModelTrainerConfig:
        config = self.config.model_trainer
        train_params = self.params.TrainingArguments
        lora_params = self.params.LoRAConfig

        create_directories([config.root_dir])

        model_trainer_config = ModelTrainerConfig(
            root_dir=config.root_dir,
            data_path=config.data_path,
            model_ckpt=config.model_ckpt,
            num_train_epochs=train_params.num_train_epochs,
            per_device_train_batch_size=train_params.per_device_train_batch_size,
            per_device_eval_batch_size=train_params.per_device_eval_batch_size,
            weight_decay=train_params.weight_decay,
            logging_steps=train_params.logging_steps,
            eval_strategy=train_params.eval_strategy,
            save_strategy=train_params.save_strategy,
            learning_rate=train_params.learning_rate,
            lora_r=lora_params.lora_r,
            lora_alpha=lora_params.lora_alpha,
            lora_dropout=lora_params.lora_dropout,
            lora_target_modules=lora_params.lora_target_modules,
            seed=train_params.seed
        )

        return model_trainer_config
    
    def get_model_evaluation_config(self) -> ModelEvaluationConfig:
        config = self.config.model_evaluation

        create_directories([config.root_dir])

        model_evaluation_config = ModelEvaluationConfig(
            root_dir=config.root_dir,
            data_path=config.data_path,
            metric_file_name=config.metric_file_name,
            base_model_path=config.base_model_path
        )

        return model_evaluation_config
    
    