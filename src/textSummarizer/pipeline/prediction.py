import os
import torch
from textSummarizer.config.configuration import ConfigurationManager
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
from dotenv import load_dotenv
from textSummarizer.logging import logger


class PredictionPipeline:
    def __init__(self):
        self.config = ConfigurationManager().get_model_evaluation_config()
        load_dotenv()
        
        # Setup device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Get HF repo ID from environment
        username = os.getenv('HUGGINGFACE_USERNAME')
        self.repo_id = f"{username}/distilbart-samsum-lora"
        
        # Load base model and LoRA adapter
        logger.info(f"Loading base model: sshleifer/distilbart-cnn-12-6")
        self.base_model = AutoModelForSeq2SeqLM.from_pretrained("sshleifer/distilbart-cnn-12-6")
        self.base_model.config.use_cache = True
        
        logger.info(f"Loading LoRA adapter from: {self.repo_id}")
        self.model = PeftModel.from_pretrained(self.base_model, self.repo_id)
        self.model = self.model.to(self.device)
        
        # Load tokenizer from HF repo
        logger.info(f"Loading tokenizer from: {self.repo_id}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.repo_id)

    
    def predict(self, text):
        """Predict summary for given text"""
        logger.info("Generating summary...")
        
        # Tokenize input
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            max_length=1024,
            truncation=True
        ).to(self.device)
        
        # Generate summary
        summary_ids = self.model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=128,
            num_beams=4,
            early_stopping=True,
            length_penalty=0.8
        )
        
        # Decode and return summary
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        print("Dialogue:")
        print(text)
        print("\nModel Summary:")
        print(summary)
        
        return summary