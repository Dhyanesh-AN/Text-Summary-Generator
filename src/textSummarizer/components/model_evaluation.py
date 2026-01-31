import os
import numpy as np
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, DataCollatorForSeq2Seq
from datasets import load_from_disk
from peft import PeftModel
import evaluate
import pandas as pd
from tqdm import tqdm
from textSummarizer.logging import logger
from dotenv import load_dotenv
from textSummarizer.entity import ModelEvaluationConfig

class ModelEvaluation:
    def __init__(self, config: ModelEvaluationConfig):
        self.config = config

    def evaluate(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        load_dotenv()
        username = os.getenv('HUGGINGFACE_USERNAME')
        repo_id = f"{username}/distilbart-samsum-lora"
        # Load LoRA model from Hugging Face
        logger.info(f"Loading LoRA model from {repo_id}")
        
        base_model = AutoModelForSeq2SeqLM.from_pretrained(self.config.base_model_path)
        base_model.config.use_cache = True
        
        # Load LoRA adapter from Hugging Face
        model = PeftModel.from_pretrained(base_model, repo_id)
        model = model.to(device)
        
        # Load tokenizer from Hugging Face (from LoRA repo)
        tokenizer = AutoTokenizer.from_pretrained(repo_id)
        
        # Load test dataset
        logger.info(f"Loading dataset from {self.config.data_path}")
        dataset_samsum_pt = load_from_disk(self.config.data_path)
        
        # ROUGE metric
        rouge = evaluate.load("rouge")
        
        # Get test dataset (use smaller subset if needed for faster evaluation)
        test_dataset = dataset_samsum_pt["test"].select(range(10))


        
        predictions = []
        references = []
        
        # Generate predictions on test set
        for example in tqdm(test_dataset, desc="Evaluating"):
            inputs = {
                "input_ids": torch.tensor(example["input_ids"]).unsqueeze(0).to(device),
                "attention_mask": torch.tensor(example["attention_mask"]).unsqueeze(0).to(device)
            }

            
            # Generate summary
            summary_ids = model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_length=128,
                num_beams=4,
                early_stopping=True,
                length_penalty=0.8
            )
            
            # Decode prediction
            pred = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            predictions.append(pred.strip())
            
            # Get reference from labels (convert -100 back to pad token id for decoding)
            label_ids = example["labels"]
            label_ids = [lid if lid != -100 else tokenizer.pad_token_id for lid in label_ids]
            ref = tokenizer.decode(label_ids, skip_special_tokens=True)
            references.append(ref.strip())
        
        # Compute ROUGE scores
        logger.info("Computing ROUGE scores...")
        rouge_scores = rouge.compute(predictions=predictions, references=references, use_stemmer=True)
        
        # Format results
        results = {
            "rouge1": round(rouge_scores["rouge1"] * 100, 4),
            "rouge2": round(rouge_scores["rouge2"] * 100, 4),
            "rougeL": round(rouge_scores["rougeL"] * 100, 4),
            "rougeLsum": round(rouge_scores["rougeLsum"] * 100, 4),
        }
        
        # Save results
        df = pd.DataFrame([results], index=["distilbart-lora"])
        df.to_csv(self.config.metric_file_name)
        
        logger.info(f"Evaluation complete! Results saved to {self.config.metric_file_name}")
        logger.info(f"ROUGE Scores:\n{df.to_string()}")
        
        return results