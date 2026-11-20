"""Bounded image decoding shared by API and offline evaluation."""
import io,warnings
import cv2,numpy as np
from PIL import Image,UnidentifiedImageError
MAX_PIXELS=12_000_000

def decode(raw):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if image.format not in ('JPEG', 'PNG', 'WEBP'): raise ValueError('仅支持 JPEG、PNG、WebP')
                if image.width * image.height > MAX_PIXELS: raise ValueError('图片不能超过 1200 万像素')
                image.load()
        img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if img is None: raise ValueError('无法解码图片')
        return img
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError('无效图片或图片尺寸过大') from exc

