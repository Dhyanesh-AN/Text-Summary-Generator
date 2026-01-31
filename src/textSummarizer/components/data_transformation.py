import os
from textSummarizer.logging import logger
from transformers import AutoTokenizer
from datasets import load_dataset, load_from_disk
from textSummarizer.entity import DataTransformationConfig

class DataTransformation:
    def __init__(self, config: DataTransformationConfig):
        self.config = config
        self.tokenizer = AutoTokenizer.from_pretrained(config.tokenizer_path)

        # Match constants used in fine-tune script
        self.MAX_INPUT_LENGTH = 1024
        self.MAX_TARGET_LENGTH = 128

    def _preprocess(self, batch):
        model_inputs = self.tokenizer(
            batch["dialogue"],
            max_length=self.MAX_INPUT_LENGTH,
            truncation=True,
            padding="max_length",
        )

        labels = self.tokenizer(
            batch["summary"],
            max_length=self.MAX_TARGET_LENGTH,
            truncation=True,
            padding="max_length",
        )

        # replace pad token id's in labels by -100 so they are ignored by the loss
        labels["input_ids"] = [
            [(l if l != self.tokenizer.pad_token_id else -100) for l in label]
            for label in labels["input_ids"]
        ]

        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    def convert(self):
        # Attempt to load from directory of CSVs, then from disk, then from HF dataset id
        data_path = self.config.data_path

        dataset_samsum = None
        # If data_path is a local directory containing CSV files
        try:
            if os.path.isdir(data_path):
                csv_train = os.path.join(data_path, "train.csv")
                csv_val = os.path.join(data_path, "validation.csv")
                csv_test = os.path.join(data_path, "test.csv")

                data_files = {}
                if os.path.exists(csv_train):
                    data_files["train"] = csv_train
                if os.path.exists(csv_val):
                    data_files["validation"] = csv_val
                if os.path.exists(csv_test):
                    data_files["test"] = csv_test

                if data_files:
                    dataset_samsum = load_dataset("csv", data_files=data_files)
                else:
                    # maybe it's a saved dataset directory
                    dataset_samsum = load_from_disk(data_path)
            else:
                # not a directory: try load_from_disk then load_dataset (HF id)
                try:
                    dataset_samsum = load_from_disk(data_path)
                except Exception:
                    dataset_samsum = load_dataset(data_path)
        except Exception:
            # Fallback to trying load_dataset with HF id
            dataset_samsum = load_dataset(data_path)

        tokenized = dataset_samsum.map(
            self._preprocess,
            batched=True,
            remove_columns=dataset_samsum["train"].column_names,
        )

        out_dir = os.path.join(self.config.root_dir, "samsum_dataset")
        tokenized.save_to_disk(out_dir)
        logger.info(f"Saved tokenized dataset to {out_dir}")