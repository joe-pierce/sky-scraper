import os
import requests
import base64
from io import BytesIO
import numpy as np
from PIL import Image
from numpy.typing import NDArray
import plotly.express as px

prompts = {
    "standard": "Turn into a stylised photo realistic city skyline image of these buildings preserving the same number of buildings and their proportions."
}


# Convert your numpy rgb to PNG bytes
def rgb_to_png_bytes(rgb: NDArray, factor=4) -> bytes:
    buf = BytesIO()
    img = Image.fromarray(rgb[::-1, :].astype("uint8"))
    w, h = img.size
    img = img.resize((w * factor, h * factor), Image.LANCZOS)
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def png_bytes_to_array(png_bytes: bytes) -> np.ndarray:
    img = Image.open(BytesIO(png_bytes)).convert("RGB")
    return np.array(img)


def enhance(img: NDArray, style="standard") -> bytes:
    img = rgb_to_png_bytes(img)
    url = r"https://api.replicate.com/v1/predictions"

    headers = {
        "Authorization": f"Bearer {os.environ['REPLICATE_API_TOKEN']}",
        "Content-Type": "application/json",
        "Prefer": "wait",  # wait until finished
    }

    # Replicate accepts either URLs or base64-encoded images for img2img.
    # Here we'll use base64.
    b64_img = base64.b64encode(img).decode("utf-8")

    data = {
        "version": "prunaai/flux-kontext-dev:2f311ad6069d6cb2ec28d46bb0d1da5148a983b56f4f2643d2d775d39d11e44b",
        "input": {
            "seed": -1,
            "prompt": prompts["standard"],
            "guidance": 3.5,
            "image_size": 1024,
            "speed_mode": "Real Time",
            "aspect_ratio": "match_input_image",
            "img_cond_path": f"data:image/png;base64,{b64_img}",
            "output_format": "png",
            "output_quality": 80,
            "num_inference_steps": 30,
        },
    }

    r = requests.post(url, headers=headers, json=data, timeout=300)
    r.raise_for_status()
    out = r.json()

    # Replicate usually returns a list of URLs in output
    image_url = out.get("output")
    if not image_url:
        raise RuntimeError(f"No output in response: {out}")

    # fetch the first result
    resp = requests.get(image_url)
    resp.raise_for_status()
    fig = px.imshow(png_bytes_to_array(resp.content), origin="upper", aspect="equal")
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        # title=f"Buildings: {num_buildings}, heights {min_h}-{max_h}, widths {min_w}-{max_w}",
        xaxis_visible=False,
        yaxis_visible=False,
        autosize=True,
    )
    return fig
