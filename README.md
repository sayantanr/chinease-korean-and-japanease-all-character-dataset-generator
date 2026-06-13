

---

# CJK Complete Synthetic Character Dataset (All Characters)

An industrial-grade, ultra-high-variance synthetic image dataset spanning the entire **CJK (Chinese, Japanese, Korean) Unicode spectrum**.

By utilizing dynamic multiprocessing paired with zero-disk in-memory streaming, this engine successfully evaluated over 102,000 Unicode slots. It aggressively discarded false-positive "tofu" rectangles to package **101,984 pristine character classes** and **2,039,680 total unique images** natively into a single compressed stream. It is structured out-of-the-box for drop-in use in modern OCR, Deep Learning, and Document Layout Analysis frameworks.

---

## 📊 Dataset Core Metrics

| Metric | Specification Details |
| --- | --- |
| **Total Character Classes** | **101,984** unique ideograph classes (Unicode-verified) |
| **Images Per Class** | 20 unique augmentations (10 Train / 10 Test) |
| **Total Image Volume** | **2,039,680** grayscale `.png` assets |
| **Source Typefaces** | Unified Jigmo Matrix (`JIGMO.TTF`, `JIGMO2.TTF`, `JIGMO3.TTF`) |
| **Target Output Format** | Comprehensive standard `ZIP_DEFLATED` Archive (Zip64 compliant) |
| **Total Package Size** | ~2.3 GB (Compressed Single Payload) |

---

## 🗺️ Unicode Blocks & Coverage Map

The dataset covers a total of 11 distinct CJK Unicode Planes, capturing rare historical characters, daily-use scripts, and deep supplementary ideograph extensions:

* **CJK Unified Ideographs Core:** `U+4E00` – `U+9FFF`
* **CJK Unified Ideographs Ext. A:** `U+3400` – `U+4DBF`
* **CJK Unified Ideographs Extensions B through I:** `U+20000` – `U+3347F`

---

## 🛠️ Data Augmentation & Variance Pipeline

Every individual glyph was generated on-the-fly inside an oversized vector viewport canvas ($96 \times 96\text{px}$) to prevent clipping before passing through a randomized 5-stage architectural distortion matrix:

1. **Scale Variance (Font Size):** Dynamically sampled across an interval from $28\text{pt}$ to $48\text{pt}$ (in steps of 4) to ensure spatial scale invariance.
2. **Stroke Weight Tuning:** Emulated printing/scanning bleeding artifacts via algorithmic filter adjustments:
* **30% Artificial Boldness:** Applied using morphological minimum filtering (`ImageFilter.MinFilter(3)`).
* **30% Artificial Thinning:** Applied using morphological maximum filtering (`ImageFilter.MaxFilter(3)`).
* **40% Regular Weight:** Native typeface stroke layout.


3. **Spatial Rotation:** Randomized pure bicubic rotational variance bounded tightly within a $\pm8^{\circ}$ envelope.
4. **2D Translation Jitter:** Random offsets applied within a $\pm3\text{px}$ X/Y vector grid before taking a sharp centered $64 \times 64\text{px}$ target crop.
5. **Gaussian Blur Distortion:** A 20% randomized probability pass injecting a blur radius of $0.1$ to $0.6$ pixels to simulate low-resolution or unfocused camera tracking.

---

## 🚫 Advanced "Tofu" / Blank Rectangle Filtering

A major technical challenge with broad CJK typefaces is handling missing glyph placeholders (affectionately called "tofu" boxes or blank fallback rectangles). Standard checking flags fail because typefaces map empty codes to structural placeholder boxes that look valid to Python.

This dataset implements a custom **Advanced Metrics Verification Engine**. Before any folder structure was built or image data written, the script queried the font's internal fallback error template character (`chr(0xFFFF)`). The raw bounding box mask metrics of every single target code point were mathematically compared against this template.

* If a code point generated an identical spatial signature to the font's error indicator, it was **discarded instantly**.
* **Result:** 100% clean data integrity. Zero blank square boxes or empty characters exist inside this zip file.

---

## 📂 Internal Directory Structure

The archive unpacks directly into standard folder-based image structures. This makes it instantly compatible with popular computer vision loaders such as PyTorch's `ImageFolder` or TensorFlow's `image_dataset_from_directory`.

```text
jigmo_dataset/
├── train/
│   ├── U_04E00/
│   │   ├── train_0.png
│   │   └── ... (up to train_9.png)
│   └── U_04E01/
└── test/
    ├── U_04E00/
    │   ├── test_0.png
    │   └── ... (up to test_9.png)
    └── U_04E01/

```

*Classes are neatly isolated using the hex identifier representation of their respective Unicode values (e.g., `U_04E00`).*

---

## ⚡ Performance Engineering Details

The pipeline was executed using a specialized, ultra-high-speed architecture:

* **In-Memory Stream Buffering:** Rather than executing slow disk writes for over 2 million small files (which creates massive file allocation table overhead in Windows), images were saved as raw PNG byte fragments in RAM (`io.BytesIO`) and streamed directly into the compressed archive container.
* **Linear CPU Core Scaling:** Multi-core execution was managed via a balanced background thread chunk allocation layout (`chunksize=250`), running at a sustained throughput of **~157.0 characters per second**.
* **Zip64 Container Architecture:** Utilizing explicit Zip64 structural layers (`allowZip64=True`) safely clears the standard ZIP boundary limitations (which crash when handling more than 65,535 individual file records).

---

## 📜 License

This asset pipeline and the generated dataset outputs are distributed under the open **CC0-1.0 (Creative Commons Public Domain Dedication)** license. You are free to copy, modify, distribute, and perform commercial machine learning model training on this work without asking for permission or attribution.
