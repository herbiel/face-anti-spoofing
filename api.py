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

class InferenceResponse(BaseModel):
    code: int
    faces: list[InferenceResult]
    message: str = ""

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

@app.get("/predict", response_model=InferenceResponse)
async def predict_anti_spoofing(
    source: str = Query(..., description="Local file path or image URL"),
    confidence: float = Query(0.5, description="Face detection confidence threshold")
):
    if model is None or detector is None:
        return {"code": 500, "faces": [], "message": "Models not loaded properly."}

    try:
        # Load the image
        image = load_image_from_source(source)
        
        # Detect faces
        faces = detector.detect(image)
        faces = [f for f in faces if f.confidence >= confidence]
        
        if not faces:
            return {"code": 200, "faces": [], "message": ""}
            
        results = []
        for face in faces:
            result = predict(image, face.bbox, model, config, device)
            results.append({
                "label": result["label"],
                "score": result["score"],
                "bbox": result["bbox"]
            })
            
        return {"code": 200, "faces": results, "message": ""}
        
    except ValueError as ve:
        return {"code": 500, "faces": [], "message": str(ve)}
    except Exception as e:
        return {"code": 500, "faces": [], "message": f"Internal server error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
