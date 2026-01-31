import os
import math
import numpy as np
import torch
from datasets import load_dataset, load_from_disk
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
import evaluate
from dotenv import load_dotenv
from huggingface_hub import login
import os
from huggingface_hub import HfApi
from textSummarizer.entity import ModelTrainerConfig

class ModelTrainer:
    def __init__(self, config: ModelTrainerConfig):
        self.config = config
        
        # Set seeds for reproducibility
        torch.manual_seed(config.seed)
        np.random.seed(config.seed)

    def _hf_save_model(self, model, tokenizer):
        load_dotenv()
        token = os.getenv('HUGGINGFACE_HUB_TOKEN')
        username = os.getenv('HUGGINGFACE_USERNAME')
        login(token=token)
        api = HfApi()
        repo_id = f"{username}/distilbart-samsum-lora"

        # Push LoRA adapter only if repo does not already exist
        try:
            api.model_info(repo_id)
            print(f"Model https://huggingface.co/{repo_id} already exists — skipping push")
        except Exception:
            # Repo not found (or another error) — attempt to push
            model.push_to_hub(repo_id)
            tokenizer.push_to_hub(repo_id)
            print(f"Model pushed to https://huggingface.co/{repo_id}")


    def train(self):
        # Device setup
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(self.config.model_ckpt)
        model = AutoModelForSeq2SeqLM.from_pretrained(self.config.model_ckpt)
        
        # Recommended when training with adapters
        model.config.use_cache = False
        
        # Load pre-tokenized dataset
        dataset_samsum_pt = load_from_disk(self.config.data_path)
        
        # Data collator
        seq2seq_data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)
        
        # Setup PEFT (LoRA)
        lora_config = LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            target_modules=self.config.lora_target_modules,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            task_type=TaskType.SEQ_2_SEQ_LM
        )
        
        # Wrap model with LoRA
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
        
        # Training arguments using Seq2SeqTrainingArguments
        training_args = Seq2SeqTrainingArguments(
            output_dir=self.config.root_dir,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            predict_with_generate=True,
            eval_strategy=self.config.eval_strategy,
            save_strategy=self.config.save_strategy,
            logging_strategy="steps",
            logging_steps=self.config.logging_steps,
            save_total_limit=3,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            num_train_epochs=self.config.num_train_epochs,
            fp16=torch.cuda.is_available(),
            remove_unused_columns=True,
            push_to_hub=False,
            report_to="none",
        )
        
        # ROUGE metric for evaluation
        rouge = evaluate.load("rouge")
        
        def postprocess_text(preds, labels):
            preds = [pred.strip() for pred in preds]
            labels = [lab.strip() for lab in labels]
            return preds, labels
        
        def compute_metrics(eval_pred):
            generated_tokens, label_tokens = eval_pred
            # decode
            if isinstance(generated_tokens, tuple):
                generated_tokens = generated_tokens[0]
            decoded_preds = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
            # replace -100
            label_tokens = np.where(label_tokens != -100, label_tokens, tokenizer.pad_token_id)
            decoded_labels = tokenizer.batch_decode(label_tokens, skip_special_tokens=True)
            preds, labels = postprocess_text(decoded_preds, decoded_labels)
            result = rouge.compute(predictions=preds, references=labels, use_stemmer=True)
            # rouge returns dict with lists; get mid scores
            result = {k: round(v*100, 4) for k, v in result.items()}
            # optionally compute length
            result["gen_len"] = np.mean([len(tokenizer.encode(p)) for p in preds])
            return result
        
        train_dataset = dataset_samsum_pt["train"].select(range(10))
        eval_dataset = dataset_samsum_pt["validation"].select(range(10))
        # Seq2SeqTrainer
        trainer = Seq2SeqTrainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            processing_class=tokenizer,
            data_collator=seq2seq_data_collator,
            compute_metrics=compute_metrics
        )
        
        # Train
        trainer.train()
        
        # Save the LoRA adapter and tokenizer
        os.makedirs(self.config.root_dir, exist_ok=True)
        model.save_pretrained(self.config.root_dir)
        tokenizer.save_pretrained(self.config.root_dir)
        print(f"Saved LoRA adapter and tokenizer to {self.config.root_dir}")
    
