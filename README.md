# HaFa's EyE v3.0 — Advanced OSINT People Finder

<p align="center">
  <b>🔍 Find anyone from their photo — NO API KEYS REQUIRED 🔍</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0.0-cyan?style=for-the-badge" alt="version">
  <img src="https://img.shields.io/badge/python-3.8+-blue?style=for-the-badge" alt="python">
  <img src="https://img.shields.io/badge/API_Keys-NONE_NEEDED-green?style=for-the-badge" alt="no-api">
  <img src="https://img.shields.io/badge/license-Educational-red?style=for-the-badge" alt="license">
</p>

---

## ⚡ What It Does

HaFa's EyE is an **advanced OSINT facial recognition & people finder** tool. Given a photo of a person, it:

1. **🧠 Detects & crops faces** — Using dlib & face_recognition (optional)
2. **📷 Extracts EXIF metadata** — Camera model, GPS coordinates, timestamps, author
3. **🔍 Searches 5 engines simultaneously** — Google Lens, Yandex, Bing, TinEye, Baidu
4. **🦆 Name searches DuckDuckGo** — Finds social profiles from discovered names
5. **👤 Enumerates 15+ social platforms** — Instagram, X, Facebook, LinkedIn, TikTok, etc.
6. **📊 Generates professional reports** — Rich terminal UI, JSON export, HTML export

**All without any API keys.** Pure reverse image search + web scraping.

---

## 🚀 Quick Start

```bash
# Clone & install
git clone https://github.com/0ngkur/wizards-queen-hafas-eye.git
cd Wizards-Queen-Hafas-Eye
pip install -r requirements.txt

# Run a hunt
python hafa_eye.py target_photo.jpg

# Full hunt with all outputs
python hafa_eye.py target_photo.jpg --verbose -o report.json --html report.html
```

---

## 📋 Usage

```
python hafa_eye.py <image> [OPTIONS]

Arguments:
  image                   Path to the target image

Options:
  -v, --verbose           Enable verbose output
  -o, --output FILE       Save JSON report
  --html FILE             Save HTML report
  --no-faces              Skip face detection (search image as-is)
  --no-social             Skip social profile enumeration
  --engines ENGINE [...]  Use specific engines only
                          Choices: google, yandex, bing, tineye, baidu
```

### Examples

```bash
# Basic hunt
python hafa_eye.py photo.jpg

# Verbose + JSON output
python hafa_eye.py photo.jpg -v -o results.json

# HTML report
python hafa_eye.py photo.jpg --html report.html

# Only Google + Yandex
python hafa_eye.py photo.jpg --engines google yandex

# No face detection (faster, for logos/objects too)
python hafa_eye.py photo.jpg --no-faces

# Skip social enumeration (faster)
python hafa_eye.py photo.jpg --no-social
```

---

## 🔧 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    HaFa's EyE v3.0                      │
├─────────┬───────────┬───────────┬───────────┬───────────┤
│  EXIF   │   Face    │  Reverse  │   Name    │  Social   │
│  Intel  │ Analyzer  │  Image    │ Extractor │  Profile  │
│ Module  │ & Cropper │  Search   │           │  Enumer.  │
├─────────┴───────────┼───────────┤           ├───────────┤
│                     │ • Google  │           │ 15+ sites │
│  Pillow / OpenCV    │ • Yandex  │ Heuristic │ Parallel  │
│  face_recognition   │ • Bing    │ NLP       │ Checking  │
│                     │ • TinEye  │           │           │
│                     │ • Baidu   │           │           │
├─────────────────────┴───────────┴───────────┴───────────┤
│              Result Processor & Deduplicator             │
├──────────────┬──────────────────┬────────────────────────┤
│  Rich UI     │  JSON Export     │  HTML Report           │
└──────────────┴──────────────────┴────────────────────────┘
```

---

## 📊 Output Formats

### Terminal (Rich UI)
Beautiful color-coded tables with progress bars, categorized results, and confidence scores.

### JSON Report
Complete machine-readable output including facial encodings, EXIF data, all results, and social profiles.

### HTML Report
Professional dark-themed report you can open in any browser and share.

---

## ⚠️ Legal & Ethical Notice

> **This tool is provided for educational and authorized security research purposes ONLY.**
>
> - Do NOT use for stalking, harassment, or unauthorized surveillance
> - Respect all applicable privacy laws (GDPR, CCPA, etc.)
> - Automated scraping may violate platform Terms of Service
> - You are responsible for ensuring your use is legal in your jurisdiction
> - Always obtain proper authorization before conducting OSINT investigations

---

## 🏗️ Dependencies

| Package | Purpose | Required? |
|---------|---------|-----------|
| `requests` | HTTP requests | ✅ Yes |
| `beautifulsoup4` | HTML parsing | ✅ Yes |
| `numpy` | Numerical ops | ✅ Yes |
| `Pillow` | Image + EXIF | ✅ Yes |
| `rich` | Terminal UI | ⚡ Recommended |
| `opencv-python` | Image processing | 🔧 Optional |
| `face-recognition` | Face detection | 🔧 Optional |
| `dlib` | ML backend | 🔧 Optional |

> **Note**: The tool works without `opencv-python`, `face-recognition`, and `dlib` — it will simply skip face detection and search the full image instead.

---

## 📝 License

Educational and research use only. See the ethical notice above.
