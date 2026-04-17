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

---

## ⚠️ Legal & Ethical Notice

> **This tool is provided for educational and authorized security research purposes ONLY.**
