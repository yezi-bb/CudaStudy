#!/usr/bin/env python3
"""Read a DICOM file: dump tags to output/, export frames to output/images/."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pydicom
from PIL import Image
from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse DICOM tags and export image frames.")
    parser.add_argument(
        "dcm",
        nargs="?",
        default="20260710093903.dcm",
        help="Path to .dcm file (default: 20260710093903.dcm)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output",
        help="Output directory (default: output)",
    )
    return parser.parse_args()


def print_key_info(ds: pydicom.Dataset) -> None:
    rows = getattr(ds, "Rows", "?")
    cols = getattr(ds, "Columns", "?")
    frames = getattr(ds, "NumberOfFrames", 1)
    ts = ""
    if hasattr(ds, "file_meta") and hasattr(ds.file_meta, "TransferSyntaxUID"):
        ts = str(ds.file_meta.TransferSyntaxUID)

    print("---- DICOM Info ----")
    print(f"PatientName : {getattr(ds, 'PatientName', '')}")
    print(f"PatientID   : {getattr(ds, 'PatientID', '')}")
    print(f"StudyDate   : {getattr(ds, 'StudyDate', '')}")
    print(f"Modality    : {getattr(ds, 'Modality', '')}")
    print(f"SOPClassUID : {getattr(ds, 'SOPClassUID', '')}")
    print(f"ImageType   : {getattr(ds, 'ImageType', '')}")
    print(f"Rows x Cols : {rows} x {cols}")
    print(f"Frames      : {frames}")
    print(f"TransferSyntax: {ts}")
    print("--------------------")


def save_tags(ds: pydicom.Dataset, tag_path: Path) -> None:
    tag_path.parent.mkdir(parents=True, exist_ok=True)
    tag_path.write_text(str(ds), encoding="utf-8", errors="replace")
    print(f"Tags saved: {tag_path}")


def split_frames(arr: np.ndarray) -> list[np.ndarray]:
    if arr.ndim == 2:
        return [arr]
    if arr.ndim == 3:
        # (H, W, C) color vs (N, H, W) multi-frame
        if arr.shape[-1] in (3, 4) and arr.shape[0] > 4:
            return [arr]
        return [arr[i] for i in range(arr.shape[0])]
    if arr.ndim == 4:
        return [arr[i] for i in range(arr.shape[0])]
    raise RuntimeError(f"Unexpected pixel array shape: {arr.shape}")


def to_uint8(frame: np.ndarray, ds: pydicom.Dataset) -> np.ndarray:
    try:
        data = apply_modality_lut(frame, ds)
    except Exception:
        data = frame
    try:
        data = apply_voi_lut(data, ds)
    except Exception:
        pass

    data = np.asarray(data)
    if data.dtype == np.uint8 and (data.ndim == 2 or (data.ndim == 3 and data.shape[-1] in (3, 4))):
        out = data
    else:
        fmin = float(np.min(data))
        fmax = float(np.max(data))
        if fmax > fmin:
            data = (data - fmin) / (fmax - fmin) * 255.0
        else:
            data = np.zeros_like(data, dtype=np.float64)
        out = np.clip(data, 0, 255).astype(np.uint8)

    photo = str(getattr(ds, "PhotometricInterpretation", "MONOCHROME2"))
    if photo == "MONOCHROME1" and out.ndim == 2:
        out = 255 - out
    return out


def frame_to_image(u8: np.ndarray) -> Image.Image:
    if u8.ndim == 2:
        return Image.fromarray(u8, mode="L")
    if u8.ndim == 3 and u8.shape[-1] == 3:
        return Image.fromarray(u8, mode="RGB")
    if u8.ndim == 3 and u8.shape[-1] == 4:
        return Image.fromarray(u8, mode="RGBA")
    return Image.fromarray(u8)


def save_images(ds: pydicom.Dataset, img_dir: Path) -> int:
    img_dir.mkdir(parents=True, exist_ok=True)
    frames = split_frames(ds.pixel_array)
    print(f"Image frames: {len(frames)}, shape={frames[0].shape}, dtype={frames[0].dtype}")

    saved = 0
    for i, frame in enumerate(frames):
        im = frame_to_image(to_uint8(frame, ds))
        path = img_dir / f"{i}.bmp"
        im.save(path)
        saved += 1
        if i == 0 or i == len(frames) - 1 or (i + 1) % 50 == 0:
            print(f"  saved [{i + 1}/{len(frames)}] {path.name}")

    print(f"Images saved: {saved} -> {img_dir}")
    return saved


def main() -> int:
    args = parse_args()
    dcm_path = Path(args.dcm)
    out_dir = Path(args.output)
    img_dir = out_dir / "images"

    if not dcm_path.exists():
        print(f"DCM file not found: {dcm_path}", file=sys.stderr)
        return 1

    print(f"DCM file: {dcm_path.resolve()}")
    ds = pydicom.dcmread(str(dcm_path), force=True)
    print_key_info(ds)

    base = dcm_path.stem
    save_tags(ds, out_dir / f"{base}_tags.txt")
    save_images(ds, img_dir)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
