# deploy and run deepseek OCR model on modal
import os
import warnings
from dataclasses import dataclass
from datetime import datetime   
from pathlib import Path

import modal


image_with_repo = (
    modal.Image.from_registry("nvidia/cuda:11.8.0-devel-ubuntu22.04", add_python="3.12")
    .apt_install("git", "libgl1", "libglib2.0-0", "curl")
    .run_commands(
        # Install uv for fast package management
        "pip install uv",
        # Install CUDA 11.8 PyTorch stack via uv with custom index
        "uv pip install --system torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 "
        "--index-url https://download.pytorch.org/whl/cu118",
        # Install extra utilities
        "uv pip install --system gdown requests pillow transformers accelerate",
        # Clone DeepSeek OCR repo
        "git clone https://github.com/deepseek-ai/DeepSeek-OCR.git /deepseek-ocr",
        # Download vLLM wheel (keep original filename for uv to parse version)
        "curl -L -o /tmp/vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl "
        "https://github.com/vllm-project/vllm/releases/download/v0.8.5/vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl",
        "uv pip install --system /tmp/vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl",
        # Install repo requirements
        "cd /deepseek-ocr && uv pip install --system -r requirements.txt",
        # Install flash-attn with CUDA_HOME set (nvcc available in devel image)
        "CUDA_HOME=/usr/local/cuda pip install flash-attn==2.7.3 --no-build-isolation",
    )
)

volume = modal.Volume.from_name("deepseekOCR", create_if_missing=True)
volume_path = (  # the path to the volume from within the container
    Path("/root") / "data"
)



app = modal.App("deepseekOCR", image=image_with_repo, volumes={volume_path: volume})


@app.function(
    gpu="A10G",
    timeout=3600,
    secrets=[modal.Secret.from_name("custom-secret")]
)
def run_deepseek_ocr(image_url=None, folder=None):
    import os
    import io
    import requests
    from PIL import Image

    from transformers import AutoModel, AutoTokenizer
    import torch

    telegram_bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    telegram_bot_id    = os.environ["TELEGRAM_BOT_ID"]

    def to_direct_download(url: str) -> str:
        if url and "drive.google.com" in url:
            if "/file/d/" in url:
                file_id = url.split("/file/d/")[1].split("/")[0]
                return f"https://drive.google.com/uc?id={file_id}"
            if "id=" in url:
                file_id = url.split("id=")[1].split("&")[0]
                return f"https://drive.google.com/uc?id={file_id}"
        return url

    # Download image from URL
    direct_image_url = to_direct_download(image_url)
    response = requests.get(direct_image_url)
    response.raise_for_status()
    image = Image.open(io.BytesIO(response.content)).convert("RGB")

    # Save image temporarily for the model
    temp_image_path = volume_path / "temp_image.jpg"
    image.save(temp_image_path)

    # Load model
    os.environ["CUDA_VISIBLE_DEVICES"] = '0'
    model_name = 'deepseek-ai/DeepSeek-OCR'

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_name,
        _attn_implementation='flash_attention_2',
        trust_remote_code=True,
        use_safetensors=True
    )
    model = model.eval().cuda().to(torch.bfloat16)

    # Run inference
    prompt = "<image>\n<|grounding|>Convert the document to markdown. "
    output_path = str(volume_path / "ocr_output")
    os.makedirs(output_path, exist_ok=True)

    res = model.infer(
        tokenizer,
        prompt=prompt,
        image_file=str(temp_image_path),
        output_path=output_path,
        base_size=1024,
        image_size=640,
        crop_mode=True,
        save_results=True,
        test_compress=True
    )

    return res


@app.local_entrypoint()
def main():
    print("Running DeepSeek OCR on Modal…")
    result = run_deepseek_ocr.remote(
        image_url="https://drive.google.com/file/d/1swFgWi97Hx-A5PEWlL9irq9B5zbq2xUn/view?usp=drive_link"
    )
    print(result)