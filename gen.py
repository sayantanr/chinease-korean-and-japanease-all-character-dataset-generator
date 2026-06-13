import os
import random
import time
import sys
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import zipfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# --- SYSTEM MATCHED CONFIGURATION ---
WORKING_DIR = Path(r"C:\Users\Admin\fcuk")
FONT_FILES = [
    str(WORKING_DIR / "JIGMO.TTF"),
    str(WORKING_DIR / "JIGMO2.TTF"),
    str(WORKING_DIR / "JIGMO3.TTF")
]
OUTPUT_ZIP = WORKING_DIR / "jigmo_dataset_kaggleready.zip"
IMAGE_SIZE = (64, 64)

IMAGES_PER_CHAR_TRAIN = 10
IMAGES_PER_CHAR_TEST = 10

CJK_RANGES = [
    (0x4E00, 0x9FFF),   (0x3400, 0x4DBF),   (0x20000, 0x2A6DF),
    (0x2A700, 0x2B73F), (0x2B740, 0x2B81F), (0x2B820, 0x2CEAF),
    (0x2CEB0, 0x2EBEF), (0x30000, 0x3134F), (0x31350, 0x323AF),
    (0x2EBF0, 0x2EE5F), (0x323B0, 0x3347F)
]

_FONT_CACHE = {}

def get_cached_font(font_path, size):
    key = (font_path, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(font_path, size)
    return _FONT_CACHE[key]

def get_fallback_dimensions(font):
    """Retrieves the exact bounding frame size of the font's internal error box."""
    # 0xFFFF is a standard, non-rendering code point that forces the font's default error character
    return font.getmask(chr(0xFFFF)).getbbox()

def is_valid_glyph(char, font):
    """
    Advanced Metrics Verification: Filters out false-positive rectangles 
    by checking character layout signatures against the font's error glyph.
    """
    mask = font.getmask(char)
    bbox = mask.getbbox()
    
    # If it has no bounding box data at all, drop it immediately
    if bbox is None:
        return False
        
    fb_bbox = get_fallback_dimensions(font)
    if fb_bbox is not None:
        # Calculate width and height of the current character glyph
        char_w = bbox[2] - bbox[0]
        char_h = bbox[3] - bbox[1]
        
        # Calculate width and height of the known empty error box
        fb_w = fb_bbox[2] - fb_bbox[0]
        fb_h = fb_bbox[3] - fb_bbox[1]
        
        # If the size is identical to the missing-glyph fallback template, it's a rectangle box
        if char_w == fb_w and char_h == fb_h:
            return False
            
    return True

def apply_pipeline_variances(char, active_fonts):
    font_size = random.choice([28, 32, 36, 40, 44, 48])
    pad = int(IMAGE_SIZE[0] * 1.5)
    img_large = Image.new("L", (pad, pad), color=255)
    draw = ImageDraw.Draw(img_large)
    
    rendered = False
    for f_path in active_fonts:
        font = get_cached_font(f_path, font_size)
        
        if is_valid_glyph(char, font):
            bbox = draw.textbbox((0, 0), char, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (pad - w) // 2 - bbox[0]
            y = (pad - h) // 2 - bbox[1]
            draw.text((x, y), char, fill=0, font=font)
            rendered = True
            break
            
    if not rendered:
        return None

    # Apply data augmentations (Bold, Thin, Rotate, Translate, Blur)
    weight_roll = random.random()
    if weight_roll < 0.30:
        img_large = img_large.filter(ImageFilter.MinFilter(3))
    elif weight_roll < 0.60:
        img_large = img_large.filter(ImageFilter.MaxFilter(3))

    angle = random.uniform(-8, 8)
    img_rotated = img_large.rotate(angle, resample=Image.BICUBIC, fillcolor=255)
    
    shift_x = random.randint(-3, 3)
    shift_y = random.randint(-3, 3)
    
    start_x = (pad - IMAGE_SIZE[0]) // 2 + shift_x
    start_y = (pad - IMAGE_SIZE[1]) // 2 + shift_y
    final_img = img_rotated.crop((start_x, start_y, start_x + IMAGE_SIZE[0], start_y + IMAGE_SIZE[1]))
    
    if random.random() < 0.20:
        radius = random.uniform(0.1, 0.6)
        final_img = final_img.filter(ImageFilter.GaussianBlur(radius))
        
    return final_img

def worker_task(payload):
    char, active_fonts = payload
    
    # Pre-screen checking with our new validator at size 24
    supported = False
    for f in active_fonts:
        font = get_cached_font(f, 24)
        if is_valid_glyph(char, font):
            supported = True
            break
            
    if not supported:
        return None

    hex_id = f"U_{ord(char):05X}"
    image_data_batch = []
    
    import io
    for i in range(IMAGES_PER_CHAR_TRAIN):
        img = apply_pipeline_variances(char, active_fonts)
        if img:
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=False)
            image_data_batch.append((f"jigmo_dataset/train/{hex_id}/train_{i}.png", buf.getvalue()))
            
    for i in range(IMAGES_PER_CHAR_TEST):
        img = apply_pipeline_variances(char, active_fonts)
        if img:
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=False)
            image_data_batch.append((f"jigmo_dataset/test/{hex_id}/test_{i}.png", buf.getvalue()))
            
    return image_data_batch

def main():
    # Verify absolute uppercase file paths match your system's layout
    active_fonts = [f for f in FONT_FILES if os.path.exists(f)]
    if len(active_fonts) != 3:
        print(f"Error: Found {len(active_fonts)}/3 font files inside {WORKING_DIR}")
        print("Please make sure JIGMO.TTF, JIGMO2.TTF, and JIGMO3.TTF are all in that folder.")
        return

    print("Expanding 100k+ Unicode targets...")
    all_chars = [chr(cp) for start, end in CJK_RANGES for cp in range(start, end + 1)]
    
    print("\nStep 1: Generating dataset-metadata.json configuration...")
    metadata = {
        "title": "CJK All Characters Dataset",
        "id": "sayantanroy10121999/cjk-all-characters-dataset",
        "licenses": [{"name": "CC0-1.0"}]
    }
    with open(WORKING_DIR / "dataset-metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("Step 2: Starting parallel rendering and direct ZIP compression stream...")
    start_time = time.time()
    success_count = 0
    total_images = 0

    tasks = [(c, active_fonts) for c in all_chars]

    with zipfile.ZipFile(OUTPUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        with ProcessPoolExecutor() as executor:
            results = executor.map(worker_task, tasks, chunksize=250)
            
            for idx, batch in enumerate(results):
                if batch:
                    success_count += 1
                    for internal_path, img_bytes in batch:
                        archive.writestr(internal_path, img_bytes)
                        total_images += 1
                        
                if idx % 1000 == 0 and idx > 0:
                    elapsed = time.time() - start_time
                    speed = idx / elapsed
                    print(f" -> Processed: {idx}/{len(all_chars)} characters | Valid Classes: {success_count:,} | Speed: {speed:.1f} chars/sec        ", end="\r")

    print(f"\n\n=======================================================")
    print(" SUCCESS: Filtered In-Memory Zipping Complete!          ")
    print("=======================================================")
    print(f"Target Archive: {OUTPUT_ZIP.resolve()}")
    print(f"Total CLEAN Character Classes Packed: {success_count:,}")
    print(f"Total Images Compiled: {total_images:,}")
    print(f"Execution Duration: {time.time() - start_time:.1f} seconds")

if __name__ == "__main__":
    main()
