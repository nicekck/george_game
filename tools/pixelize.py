#!/usr/bin/env python3
"""사진 -> 픽셀 아트 스프라이트 변환기.

배경 자동 제거(rembg) -> 피사체 크롭 -> 64x64 픽셀화 -> 색 팔레트 축소.
결과물: assets/george.png (투명 배경, nearest-neighbor 픽셀)
"""
import sys
import io
from PIL import Image
import numpy as np

SIZE = 64          # 최종 스프라이트 높이 (px). 폭은 비율 유지
PAD = 0.04         # 피사체 주변 여백 비율

def remove_bg(img: Image.Image) -> Image.Image:
    from rembg import remove
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    out = remove(buf.getvalue())
    return Image.open(io.BytesIO(out)).convert("RGBA")

def crop_to_subject(img: Image.Image) -> Image.Image:
    """알파 채널 기준으로 피사체에 꽉 맞춰 크롭(약간의 여백만)."""
    a = np.array(img)[:, :, 3]
    ys, xs = np.where(a > 24)
    if len(xs) == 0:
        return img
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    w, h = x1 - x0, y1 - y0
    px, py = int(w * PAD), int(h * PAD)
    x0 = max(0, x0 - px); y0 = max(0, y0 - py)
    x1 = min(img.width, x1 + px); y1 = min(img.height, y1 + py)
    return img.crop((x0, y0, x1, y1))

def quantize(img: Image.Image, colors: int = 32) -> Image.Image:
    """알파를 보존하며 RGB 팔레트를 축소(레트로 톤)."""
    arr = np.array(img)
    alpha = arr[:, :, 3]
    rgb = Image.fromarray(arr[:, :, :3]).convert("RGB")
    rgb = rgb.quantize(colors=colors, method=Image.MEDIANCUT).convert("RGB")
    out = np.dstack([np.array(rgb), alpha]).astype(np.uint8)
    # 반투명 가장자리는 깔끔하게 0/255로 정리
    out[:, :, 3] = np.where(out[:, :, 3] > 128, 255, 0)
    return Image.fromarray(out, "RGBA")

def pixelize(img: Image.Image, height: int = SIZE) -> Image.Image:
    w, h = img.size
    new_w = max(1, round(w * height / h))
    small = img.resize((new_w, height), Image.LANCZOS)
    return quantize(small, colors=32)

def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else "assets/george.png"
    img = Image.open(src).convert("RGBA")
    print(f"[1/4] loaded {img.size}")
    cut = remove_bg(img)
    print("[2/4] background removed")
    sq = crop_to_subject(cut)
    print(f"[3/4] cropped to subject {sq.size}")
    px = pixelize(sq)
    px.save(dst)
    print(f"[4/4] saved {dst} {px.size}")
    # 미리보기(8배 확대) 저장
    preview = px.resize((px.width * 8, px.height * 8), Image.NEAREST)
    preview.save(dst.replace(".png", "_preview.png"))
    print("preview saved")

if __name__ == "__main__":
    main()
