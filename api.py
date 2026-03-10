# api.py
import urllib.request
from typing import Optional

import cv2
import numpy as np
import torch
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from main import load_model, predict
from uniface import RetinaFace

app = FastAPI(
    title="Face Anti-Spoofing API",
    description="API for detecting whether a face is real or fake from a local file or URL.",
    version="1.0"
)

# 1. Initialize models at startup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
try:
    model, config = load_model("weights/MiniFASNetV2.pth", "v2", device)
    detector = RetinaFace()
except Exception as e:
    print(f"Failed to load model: {e}")
    # Still start server, but endpoints might fail if models aren't present
    model, config, detector = None, None, None

class InferenceResult(BaseModel):
    label: str
    score: float
    bbox: list[int]

class ImageResult(BaseModel):
    source: str
    faces: list[InferenceResult]
    error: str = ""

class BatchInferenceResponse(BaseModel):
    code: int
    results: list[ImageResult]
    message: str = ""

class PredictionRequest(BaseModel):
    sources: list[str]
    confidence: float = 0.5

def load_image_from_source(source: str) -> np.ndarray:
    """Load an image from a local path or a URL."""
    if source.startswith("http://") or source.startswith("https://"):
        try:
            req = urllib.request.urlopen(source)
            arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
            img = cv2.imdecode(arr, -1)
            if img is None:
                raise ValueError("Failed to decode image from URL")
            return img
        except Exception as e:
            raise ValueError(f"Failed to download image from URL: {e}")
    else:
        img = cv2.imread(source)
        if img is None:
            raise ValueError(f"Failed to load image from local path: {source}")
        return img

@app.post("/predict", response_model=BatchInferenceResponse)
async def predict_anti_spoofing(request: PredictionRequest):
    if model is None or detector is None:
        return {"code": 500, "results": [], "message": "Models not loaded properly."}

    batch_results = []
    
    for source in request.sources:
        try:
            # Load the image
            image = load_image_from_source(source)
            
            # Detect faces
            faces = detector.detect(image)
            faces = [f for f in faces if f.confidence >= request.confidence]
            
            if not faces:
                batch_results.append({
                    "source": source,
                    "faces": [],
                    "error": ""
                })
                continue
                
            results = []
            for face in faces:
                result = predict(image, face.bbox, model, config, device)
                results.append({
                    "label": result["label"],
                    "score": result["score"],
                    "bbox": result["bbox"]
                })
                
            batch_results.append({
                "source": source,
                "faces": results,
                "error": ""
            })
            
        except ValueError as ve:
            batch_results.append({
                "source": source,
                "faces": [],
                "error": str(ve)
            })
        except Exception as e:
            batch_results.append({
                "source": source,
                "faces": [],
                "error": f"Internal error: {str(e)}"
            })

    # Return 200 with the batch results.
    return {"code": 200, "results": batch_results, "message": ""}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
