# Face Anti-Spoofing

[![Downloads](https://img.shields.io/github/downloads/yakhyo/face-anti-spoofing/total)](https://github.com/yakhyo/face-anti-spoofing/releases)
[![GitHub Repo stars](https://img.shields.io/github/stars/yakhyo/face-anti-spoofing)](https://github.com/yakhyo/face-anti-spoofing/stargazers)

Minimal inference utilities for silent face anti-spoofing using **MiniFASNetV1SE** and **MiniFASNetV2** models.

> [!TIP]  
> The models and functionality in this repository are **integrated into [UniFace](https://github.com/yakhyo/uniface)** — an all-in-one face analysis toolkit.  
> [![PyPI Version](https://img.shields.io/pypi/v/uniface.svg)](https://pypi.org/project/uniface/) [![GitHub Stars](https://img.shields.io/github/stars/yakhyo/uniface)](https://github.com/yakhyo/uniface/stargazers) [![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)


|             Real              |             Fake              |             Fake              |
| :---------------------------: | :---------------------------: | :---------------------------: |
| ![Real](assets/result_T1.jpg) | ![Fake](assets/result_F1.jpg) | ![Fake](assets/result_F2.jpg) |

## Installation

This project now uses `uv` for dependency management, replacing `requirements.txt`.

```bash
# Install for CPU-only instances (Highly recommended for Linux deployments to save ~2GB CUDA binaries)
uv sync --extra cpu

# Or install for GPU instances (CUDA)
uv sync --extra gpu
```

## Usage

### FastAPI Background Service

We now provide a standard REST API powered by FastAPI. 
For detailed API usage and request formats, see [API Documentation](api_docs.md).
For production deployment strategies (Gunicorn/Systemd), see [Deployment Guide](deployment_guide.md).

```bash
# Run the API server locally
uv run uvicorn api:app --host 0.0.0.0 --port 8000
```
### Image Inference

```bash
uv run main.py --source assets/image.jpg --weight weights/MiniFASNetV2.pth --output result.jpg --view
```

### Webcam Inference

```bash
uv run main.py --source 0 --weight weights/MiniFASNetV2.pth --view
```

### Options

| Argument       | Default | Description                          |
| -------------- | ------- | ------------------------------------ |
| `--weight`     | -       | Path to model weights (.pth)         |
| `--model`      | `v2`    | Model variant (`v1se` or `v2`)       |
| `--source`     | `0`     | Image path or camera index           |
| `--output`     | -       | Path to save output (image or video) |
| `--view`       | -       | Display inference results            |
| `--confidence` | `0.5`   | Face detection confidence threshold  |

## ONNX Export

```bash
python onnx_export.py --weight weights/MiniFASNetV2.pth --model v2 --dynamic
```

## ONNX Inference

```bash
python onnx_inference.py --model weights/MiniFASNetV2.onnx --scale 2.7
```

## Model Weights

| Model          | Parameters | Crop Scale | Download                                                                                                                                                                                                   |
| -------------- | ---------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| MiniFASNetV1SE | ~0.43M     | 4.0        | [PyTorch](https://github.com/yakhyo/face-anti-spoofing/releases/download/weights/MiniFASNetV1SE.pth) \| [ONNX](https://github.com/yakhyo/face-anti-spoofing/releases/download/weights/MiniFASNetV1SE.onnx) |
| MiniFASNetV2   | ~0.43M     | 2.7        | [PyTorch](https://github.com/yakhyo/face-anti-spoofing/releases/download/weights/MiniFASNetV2.pth) \| [ONNX](https://github.com/yakhyo/face-anti-spoofing/releases/download/weights/MiniFASNetV2.onnx)     |

## Reference

Based on [Silent-Face-Anti-Spoofing](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing)
