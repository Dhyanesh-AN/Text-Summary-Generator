from fastapi import FastAPI, Query, BackgroundTasks
import uvicorn
import os
import subprocess
from starlette.responses import RedirectResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from textSummarizer.pipeline.prediction import PredictionPipeline
from textSummarizer.logging import logger


app = FastAPI(title="Text Summarization API")

# Load model once at startup
prediction_pipeline = None

@app.on_event("startup")
async def startup_event():
    """Load model once at startup"""
    global prediction_pipeline
    logger.info("Loading prediction pipeline...")
    prediction_pipeline = PredictionPipeline()
    logger.info("Prediction pipeline loaded successfully")


class TextRequest(BaseModel):
    text: str


class SummaryResponse(BaseModel):
    dialogue: str
    summary: str


@app.get("/", tags=["root"])
async def index():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/train", tags=["training"])
async def training(background_tasks: BackgroundTasks):
    """Start training in background"""
    try:
        background_tasks.add_task(run_training)
        return {"status": "Training started in background"}
    except Exception as e:
        logger.error(f"Error starting training: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


def run_training():
    """Run training in background"""
    try:
        logger.info("Starting training...")
        result = subprocess.run(["python", "main.py"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Training completed successfully")
        else:
            logger.error(f"Training failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running training: {e}")


@app.post("/predict", response_model=SummaryResponse, tags=["prediction"])
async def predict_route(request: TextRequest):
    """Generate summary for given text"""
    try:
        if not request.text.strip():
            return JSONResponse(status_code=400, content={"error": "Text cannot be empty"})
        
        logger.info(f"Generating summary for text of length: {len(request.text)}")
        summary = prediction_pipeline.predict(request.text)
        
        return SummaryResponse(dialogue=request.text, summary=summary)
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)