#!/usr/bin/env python3
\"\"\"
╔══════════════════════════════════════════════════════════════════════════════╗
║                        H a F a ' s   E y E   v3.0                         ║
║            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━               ║
║              ADVANCED OSINT FACIAL RECOGNITION & PEOPLE FINDER             ║
║                        ◆ NO API KEYS REQUIRED ◆                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

Multi-engine reverse image search, facial analysis, EXIF intel extraction,
social media profile enumeration, and automated OSINT report generation.

Author : HaFa Team
Version: 3.0.0
License: Educational / Research Use Only
\"\"\"

import os
import sys

# Fix Windows console encoding (must be before any print/output)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import io
import re
import json
import time
import hashlib
import struct
import base64
import argparse
import warnings
import tempfile
import threading
import traceback
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus, urlparse, urljoin, parse_qs
import datetime

# ──────────────────────────── Suppress Noise ─────────────────────────────────
warnings.filterwarnings('ignore')

# ──────────────────────────── Optional Imports ───────────────────────────────

# --- numpy (required) ---
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# --- OpenCV ---
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# --- face_recognition ---
try:
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False

# --- requests + bs4 ---
try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# --- Pillow ---
try:
    from PIL import Image, ExifTags
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# --- Rich (terminal UI) ---
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.text import Text
    from rich.columns import Columns
    from rich.rule import Rule
    from rich.live import Live
    from rich.tree import Tree
    from rich.align import Align
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# ──────────────────────────── Constants ───────────────────────────────────────

VERSION = \"3.0.0\"
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif'}

# Rotating user-agents to avoid detection
USER_AGENTS = [
    \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\",
    \"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0\",
    \"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15\",
    \"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\",
    \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0\",
]

# Social media platforms for profile enumeration
SOCIAL_PLATFORMS = OrderedDict([
    (\"Instagram\",    {\"url\": \"https://www.instagram.com/{}/\",       \"check\": \"instagram.com\"}),
    (\"Twitter/X\",    {\"url\": \"https://x.com/{}\",                    \"check\": \"x.com\"}),
    (\"Facebook\",     {\"url\": \"https://www.facebook.com/{}\",         \"check\": \"facebook.com\"}),
    (\"LinkedIn\",     {\"url\": \"https://www.linkedin.com/in/{}\",      \"check\": \"linkedin.com\"}),
    (\"TikTok\",       {\"url\": \"https://www.tiktok.com/@{}\",          \"check\": \"tiktok.com\"}),
    (\"YouTube\",      {\"url\": \"https://www.youtube.com/@{}\",         \"check\": \"youtube.com\"}),
    (\"Reddit\",       {\"url\": \"https://www.reddit.com/user/{}\",      \"check\": \"reddit.com\"}),
    (\"Pinterest\",    {\"url\": \"https://www.pinterest.com/{}/\",       \"check\": \"pinterest.com\"}),
    (\"Tumblr\",       {\"url\": \"https://{}.tumblr.com\",               \"check\": \"tumblr.com\"}),
    (\"GitHub\",       {\"url\": \"https://github.com/{}\",               \"check\": \"github.com\"}),
    (\"VKontakte\",    {\"url\": \"https://vk.com/{}\",                   \"check\": \"vk.com\"}),
    (\"Flickr\",       {\"url\": \"https://www.flickr.com/people/{}\",    \"check\": \"flickr.com\"}),
    (\"DeviantArt\",   {\"url\": \"https://www.deviantart.com/{}\",       \"check\": \"deviantart.com\"}),
    (\"Medium\",       {\"url\": \"https://medium.com/@{}\",              \"check\": \"medium.com\"}),
    (\"Snapchat\",     {\"url\": \"https://www.snapchat.com/add/{}\",     \"check\": \"snapchat.com\"}),
])


# ═══════════════════════════════════════════════════════════════════════════════
#                              UTILITY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

class _UserAgentRotator:
    \"\"\"Thread-safe rotating user-agent picker.\"\"\"
    def __init__(self):
        self._idx = 0
        self._lock = threading.Lock()

    def get(self) -> str:
        with self._lock:
            ua = USER_AGENTS[self._idx % len(USER_AGENTS)]
            self._idx += 1
            return ua

_ua = _UserAgentRotator()


def _log(msg: str, style: str = \"\"):
    \"\"\"Print a styled message using Rich if available, otherwise plain print.\"\"\"
    if RICH_AVAILABLE and console:
        console.print(msg, style=style)
    else:
        # strip rich markup for plain print
        clean = re.sub(r'\\[.*?\\]', '', msg)
        print(clean)


def _build_session() -> \"requests.Session\":
    \"\"\"Create a requests session with realistic browser headers.\"\"\"
    s = requests.Session()
    ua = _ua.get()
    s.headers.update({
        \"User-Agent\": ua,
        \"Accept\": \"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8\",
        \"Accept-Language\": \"en-US,en;q=0.9\",
        \"Accept-Encoding\": \"gzip, deflate\",
        \"DNT\": \"1\",
        \"Connection\": \"keep-alive\",
        \"Upgrade-Insecure-Requests\": \"1\",
    })
    return s


def _safe_request(method: str, url: str, session: \"requests.Session\" = None,
                  retries: int = 2, backoff: float = 1.5, **kwargs) -> Optional[\"requests.Response\"]:
    \"\"\"Make an HTTP request with retry logic and exponential backoff.\"\"\"
    kwargs.setdefault(\"timeout\", 20)
    kwargs.setdefault(\"allow_redirects\", True)
    sess = session or _build_session()
    for attempt in range(retries + 1):
        try:
            resp = getattr(sess, method)(url, **kwargs)
            if resp.status_code < 400:
                return resp
            if resp.status_code == 429:  # rate limited
                wait = backoff * (2 ** attempt)
                time.sleep(wait)
                continue
            return resp
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
            continue
        except Exception:
            break
    return None


def _compute_image_hash(image_path: str) -> str:
    \"\"\"Compute a perceptual hash (average hash) for deduplication.\"\"\"
    try:
        if PILLOW_AVAILABLE:
            img = Image.open(image_path).convert('L').resize((8, 8), Image.LANCZOS)
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            bits = ''.join('1' if p > avg else '0' for p in pixels)
            return hex(int(bits, 2))[2:].zfill(16)
    except Exception:
        pass
    # Fallback: MD5 of file content
    with open(image_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
#                         EXIF / METADATA INTEL MODULE
# ═══════════════════════════════════════════════════════════════════════════════

class ExifIntel:
    \"\"\"Extract OSINT-relevant metadata from image EXIF data.\"\"\"

    @staticmethod
    def extract(image_path: str) -> Dict:
        \"\"\"Return a dict with all extracted EXIF intelligence.\"\"\"
        intel = {
            \"has_exif\": False,
            \"camera_make\": None,
            \"camera_model\": None,
            \"software\": None,
            \"datetime_original\": None,
            \"datetime_digitized\": None,
            \"gps_lat\": None,
            \"gps_lon\": None,
            \"gps_altitude\": None,
            \"gps_google_maps_url\": None,
            \"image_width\": None,
            \"image_height\": None,
            \"orientation\": None,
            \"artist\": None,
            \"copyright\": None,
            \"description\": None,
            \"all_tags\": {},
        }
        if not PILLOW_AVAILABLE:
            return intel
        try:
            img = Image.open(image_path)
            exif_data = img._getexif()
            if not exif_data:
                return intel

            intel[\"has_exif\"] = True
            tag_map = {v: k for k, v in ExifTags.TAGS.items()}

            for tag_id, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                # store everything (convert bytes to repr for JSON)
                try:
                    json.dumps(value)
                    intel[\"all_tags\"][tag_name] = value
                except (TypeError, ValueError):
                    intel[\"all_tags\"][tag_name] = repr(value)

                if tag_name == \"Make\":
                    intel[\"camera_make\"] = str(value).strip()
                elif tag_name == \"Model\":
                    intel[\"camera_model\"] = str(value).strip()
                elif tag_name == \"Software\":
                    intel[\"software\"] = str(value).strip()
                elif tag_name == \"DateTimeOriginal\":
                    intel[\"datetime_original\"] = str(value)
                elif tag_name == \"DateTimeDigitized\":
                    intel[\"datetime_digitized\"] = str(value)
                elif tag_name == \"Artist\":
                    intel[\"artist\"] = str(value).strip()
                elif tag_name == \"Copyright\":
                    intel[\"copyright\"] = str(value).strip()
                elif tag_name == \"ImageDescription\":
                    intel[\"description\"] = str(value).strip()

            # GPS extraction
            gps_info = exif_data.get(tag_map.get(\"GPSInfo\"))
            if gps_info:
                lat = ExifIntel._gps_to_decimal(gps_info.get(2), gps_info.get(1))
                lon = ExifIntel._gps_to_decimal(gps_info.get(4), gps_info.get(3))
                if lat is not None and lon is not None:
                    intel[\"gps_lat\"] = lat
                    intel[\"gps_lon\"] = lon
                    intel[\"gps_google_maps_url\"] = f\"https://maps.google.com/?q={lat},{lon}\"
                alt = gps_info.get(6)
                if alt:
                    intel[\"gps_altitude\"] = float(alt)

            intel[\"image_width\"] = img.width
            intel[\"image_height\"] = img.height

        except Exception:
            pass
        return intel

    @staticmethod
    def _gps_to_decimal(coords, ref) -> Optional[float]:
        \"\"\"Convert GPS coordinates to decimal degrees.\"\"\"
        try:
            if not coords or not ref:
                return None
            degrees = float(coords[0])
            minutes = float(coords[1])
            seconds = float(coords[2])
            decimal = degrees + minutes / 60 + seconds / 3600
            if ref in ('S', 'W'):
                decimal = -decimal
            return round(decimal, 7)
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════════════════════════
#                     REVERSE IMAGE SEARCH ENGINES (NO API)
# ═══════════════════════════════════════════════════════════════════════════════

class SearchEngine:
    \"\"\"Base class for a reverse image search engine.\"\"\"
    name = \"Unknown\"
    icon = \"🔍\"

    def search(self, image_path: str, verbose: bool = False) -> List[Dict]:
        raise NotImplementedError


class GoogleImageSearch(SearchEngine):
    name = \"Google Lens\"
    icon = \"🟢\"

    def search(self, image_path: str, verbose: bool = False) -> List[Dict]:
        results = []
        try:
            session = _build_session()
            session.headers[\"Origin\"] = \"https://www.google.com\"
            session.headers[\"Referer\"] = \"https://www.google.com/\"

            with open(image_path, 'rb') as f:
                files = {
                    'encoded_image': (os.path.basename(image_path), f, 'image/jpeg'),
                    'image_content': ('', ''),
                }
                resp = _safe_request(\"post\", \"https://www.google.com/searchbyimage/upload\",
                                     session=session, files=files)

            if resp and resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Google Lens results
                for item in soup.find_all('div', class_='g')[:15]:
                    a = item.find('a')
                    h3 = item.find('h3')
                    snippet_div = item.find('div', class_='VwiC3b') or item.find('span', class_='aCOpRe')
                    if a and a.get('href') and not a['href'].startswith('/search'):
                        results.append({
                            'engine': self.name,
                            'url': a['href'],
                            'title': h3.get_text(strip=True) if h3 else \"\",
                            'snippet': snippet_div.get_text(strip=True) if snippet_div else \"\",
                            'category': self._categorize_url(a['href']),
                        })

                # Also try to extract \"Pages that include matching images\"
                for a_tag in soup.find_all('a')[:50]:
                    href = a_tag.get('href', '')
                    text = a_tag.get_text(strip=True)
                    if any(domain in href for domain in ['instagram.com', 'facebook.com', 'twitter.com',
                                                          'x.com', 'linkedin.com', 'tiktok.com',
                                                          'pinterest.com', 'vk.com', 'flickr.com']):
                        if href not in [r['url'] for r in results]:
                            results.append({
                                'engine': self.name,
                                'url': href,
                                'title': text,
                                'snippet': \"Social media match from Google\",
                                'category': 'social_media',
                            })
        except Exception as e:
            if verbose:
                _log(f\"  [dim]Google error: {e}[/dim]\")
        return results

    @staticmethod
    def _categorize_url(url: str) -> str:
        social = ['instagram.com', 'facebook.com', 'twitter.com', 'x.com',
                   'linkedin.com', 'tiktok.com', 'pinterest.com', 'vk.com']
        news = ['bbc.', 'cnn.', 'reuters.', 'apnews.', 'news.']
        if any(s in url for s in social):
            return 'social_media'
        if any(n in url for n in news):
            return 'news'
        return 'web'


class YandexImageSearch(SearchEngine):
    name = \"Yandex Images\"
    icon = \"🔴\"

    def search(self, image_path: str, verbose: bool = False) -> List[Dict]:
        results = []
        try:
            session = _build_session()
            session.headers[\"Referer\"] = \"https://yandex.com/images/\"

            # Step 1: Upload image
            with open(image_path, 'rb') as f:
                files = {'upfile': (os.path.basename(image_path), f, 'image/jpeg')}
                resp = _safe_request(\"post\",
                    \"https://yandex.com/images-apphost/image-download?images_avatars_size=orig&type=imageview\",
                    session=session, files=files)

            if not resp or resp.status_code != 200:
                return results

            # Step 2: Parse upload response for search URL
            try:
                data = resp.json()
            except Exception:
                # Fallback: try to find the CBIR ID in the response
                return results

            search_url = None
            if 'image_id' in data:
                search_url = f\"https://yandex.com/images/search?rpt=imageview&cbir_id={data['image_id']}\"
            elif 'blocks' in data:
                for block in data.get('blocks', []):
                    if 'params' in block and 'url' in block['params']:
                        search_url = \"https://yandex.com\" + block['params']['url']
                        break
            elif 'url' in data:
                search_url = f\"https://yandex.com/images/search?rpt=imageview&url={quote_plus(data['url'])}\"

            if not search_url:
                return results

            # Step 3: Get search results page
            resp2 = _safe_request(\"get\", search_url, session=session)
            if resp2 and resp2.status_code == 200:
                soup = BeautifulSoup(resp2.text, 'html.parser')

                # \"Sites with this image\" section
                for item in soup.find_all('a', class_='CbirSites-ItemTitle')[:15]:
                    if item.get('href'):
                        results.append({
                            'engine': self.name,
                            'url': item['href'],
                            'title': item.get_text(strip=True),
                            'snippet': \"Found on this site (Yandex)\",
                            'category': 'web',
                        })

                # Similar images / other results
                for item in soup.find_all('a', class_='serp-item__link')[:10]:
                    href = item.get('href', '')
                    if href and href not in [r['url'] for r in results]:
                        results.append({
                            'engine': self.name,
                            'url': href,
                            'title': item.get('title', '') or item.get_text(strip=True),
                            'snippet': \"\",
                            'category': 'web',
                        })

                # \"Other sizes\" results
                for item in soup.find_all('a', class_='CbirOtherSizes-Item')[:5]:
                    if item.get('href'):
                        results.append({
                            'engine': self.name,
                            'url': item['href'],
                            'title': \"Other image size\",
                            'snippet': \"\",
                            'category': 'image_variant',
                        })

        except Exception as e:
            if verbose:
                _log(f\"  [dim]Yandex error: {e}[/dim]\")
        return results


class BingVisualSearch(SearchEngine):
    name = \"Bing Visual Search\"
    icon = \"🔵\"

    def search(self, image_path: str, verbose: bool = False) -> List[Dict]:
        results = []
        try:
            session = _build_session()

            with open(image_path, 'rb') as f:
                files = {'image': ('image.jpg', f, 'image/jpeg')}
                resp = _safe_request(\"post\",
                    \"https://www.bing.com/images/search?view=detailv2&iss=sbiupload&FORM=SBIHMP&sbisrc=ImgDropper\",
                    session=session, files=files)

            if resp and resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # Pages that include this image
                for item in soup.find_all('a', class_='pagesIncludingImage')[:10]:
                    if item.get('href'):
                        results.append({
                            'engine': self.name,
                            'url': item['href'],
                            'title': item.get_text(strip=True),
                            'snippet': \"Page includes this image (Bing)\",
                            'category': 'web',
                        })

                # General link results
                for item in soup.find_all('a')[:60]:
                    href = item.get('href', '')
                    text = item.get_text(strip=True)
                    if (href.startswith('http') and
                        'bing.com' not in href and
                        'microsoft.com' not in href and
                        len(text) > 5 and
                        href not in [r['url'] for r in results]):
                        results.append({
                            'engine': self.name,
                            'url': href,
                            'title': text[:120],
                            'snippet': \"\",
                            'category': GoogleImageSearch._categorize_url(href),
                        })
                        if len(results) >= 15:
                            break

        except Exception as e:
            if verbose:
                _log(f\"  [dim]Bing error: {e}[/dim]\")
        return results


class TinEyeSearch(SearchEngine):
    name = \"TinEye\"
    icon = \"🟡\"

    def search(self, image_path: str, verbose: bool = False) -> List[Dict]:
        results = []
        try:
            session = _build_session()
            session.headers[\"Referer\"] = \"https://tineye.com/\"

            with open(image_path, 'rb') as f:
                files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
                resp = _safe_request(\"post\", \"https://tineye.com/search\", session=session, files=files)

            if resp and resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # Match count
                match_count_el = soup.find('h2', class_='search-results-header')
                if match_count_el and verbose:
                    _log(f\"  [dim]TinEye says: {match_count_el.get_text(strip=True)}[/dim]\")

                for item in soup.find_all('div', class_='match-row')[:15]:
                    link = item.find('a')
                    domain_span = item.find('span', class_='match-domain')
                    if link and link.get('href'):
                        results.append({
                            'engine': self.name,
                            'url': link['href'],
                            'title': domain_span.get_text(strip=True) if domain_span else \"TinEye Match\",
                            'snippet': f\"Found on {domain_span.get_text(strip=True)}\" if domain_span else \"\",
                            'category': 'web',
                        })

                # Also try the \"match\" class divs (older layout)
                for item in soup.find_all('div', class_='match')[:10]:
                    link = item.find('a')
                    if link and link.get('href') and link['href'] not in [r['url'] for r in results]:
                        results.append({
                            'engine': self.name,
                            'url': link['href'],
                            'title': \"TinEye Match\",
                            'snippet': \"\",
                            'category': 'web',
                        })

        except Exception as e:
            if verbose:
                _log(f\"  [dim]TinEye error: {e}[/dim]\")
        return results


class BaiduImageSearch(SearchEngine):
    name = \"Baidu Images\"
    icon = \"🟠\"

    def search(self, image_path: str, verbose: bool = False) -> List[Dict]:
        results = []
        try:
            session = _build_session()
            session.headers[\"Referer\"] = \"https://image.baidu.com/\"

            with open(image_path, 'rb') as f:
                img_bytes = f.read()

            # Baidu uses base64 encoded image upload
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')

            data = {
                'image': img_b64,
                'tn': 'pc',
                'from': 'pc',
                'image_source': 'PC_UPLOAD_SEARCH_FILE',
            }
            resp = _safe_request(\"post\", \"https://graph.baidu.com/upload\", session=session, data=data)

            if resp and resp.status_code == 200:
                try:
                    result_data = resp.json()
                    if result_data.get('data', {}).get('url'):
                        redirect_url = result_data['data']['url']
                        resp2 = _safe_request(\"get\", redirect_url, session=session)
                        if resp2 and resp2.status_code == 200:
                            soup = BeautifulSoup(resp2.text, 'html.parser')
                            for a_tag in soup.find_all('a')[:40]:
                                href = a_tag.get('href', '')
                                text = a_tag.get_text(strip=True)
                                if (href.startswith('http') and
                                    'baidu.com' not in href and
                                    len(text) > 3 and
                                    href not in [r['url'] for r in results]):
                                    results.append({
                                        'engine': self.name,
                                        'url': href,
                                        'title': text[:120],
                                        'snippet': \"Found via Baidu\",
                                        'category': 'web',
                                    })
                                    if len(results) >= 10:
                                        break
                except Exception:
                    pass

        except Exception as e:
            if verbose:
                _log(f\"  [dim]Baidu error: {e}[/dim]\")
        return results


class DuckDuckGoSearch(SearchEngine):
    \"\"\"Text-based people search on DuckDuckGo using names extracted from results.\"\"\"
    name = \"DuckDuckGo\"
    icon = \"🦆\"

    def search(self, image_path: str, verbose: bool = False) -> List[Dict]:
        \"\"\"Not used directly — see search_by_name().\"\"\"
        return []

    @staticmethod
    def search_by_name(name: str, verbose: bool = False) -> List[Dict]:
        \"\"\"Search DuckDuckGo for a person's name.\"\"\"
        results = []
        try:
            session = _build_session()
            query = quote_plus(f'\"{name}\" site:instagram.com OR site:facebook.com OR site:linkedin.com OR site:twitter.com')
            url = f\"https://html.duckduckgo.com/html/?q={query}\"

            resp = _safe_request(\"get\", url, session=session)
            if resp and resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for item in soup.find_all('a', class_='result__a')[:10]:
                    href = item.get('href', '')
                    title = item.get_text(strip=True)
                    # DuckDuckGo wraps URLs in a redirect
                    if 'uddg=' in href:
                        try:
                            actual_url = parse_qs(urlparse(href).query).get('uddg', [href])[0]
                        except Exception:
                            actual_url = href
                    else:
                        actual_url = href
                    if actual_url.startswith('http'):
                        results.append({
                            'engine': 'DuckDuckGo',
                            'url': actual_url,
                            'title': title,
                            'snippet': f\"Name search for: {name}\",
                            'category': GoogleImageSearch._categorize_url(actual_url),
                        })
        except Exception as e:
            if verbose:
                _log(f\"  [dim]DDG error: {e}[/dim]\")
        return results


# All available engines in priority order
ALL_ENGINES: List[SearchEngine] = [
    GoogleImageSearch(),
    YandexImageSearch(),
    BingVisualSearch(),
    TinEyeSearch(),
    BaiduImageSearch(),
]


# ═══════════════════════════════════════════════════════════════════════════════
#                       SOCIAL PROFILE ENUMERATION
# ═══════════════════════════════════════════════════════════════════════════════

class SocialProfileEnumerator:
    \"\"\"Check if a username exists on major social platforms (no API).\"\"\"

    @staticmethod
    def enumerate(username: str, verbose: bool = False) -> List[Dict]:
        \"\"\"Check multiple platforms in parallel for a given username.\"\"\"
        found = []
        username_clean = re.sub(r'[^\\w.]', '', username.lower())
        if len(username_clean) < 2:
            return found

        def _check_platform(platform_name: str, info: Dict) -> Optional[Dict]:
            try:
                url = info[\"url\"].format(username_clean)
                session = _build_session()
                resp = _safe_request(\"get\", url, session=session, retries=1, timeout=8)
                if resp and resp.status_code == 200:
                    # Basic validation: page content should contain the username
                    page_text = resp.text.lower()
                    if (username_clean in page_text or
                        'not found' not in page_text[:500].lower()):
                        return {
                            'platform': platform_name,
                            'url': url,
                            'username': username_clean,
                            'status': 'likely_exists',
                        }
            except Exception:
                pass
            return None

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(_check_platform, name, info): name
                for name, info in SOCIAL_PLATFORMS.items()
            }
            for future in as_completed(futures):
                result = future.result()
                if result:
                    found.append(result)

        return found


# ═══════════════════════════════════════════════════════════════════════════════
#                         NAME / IDENTITY EXTRACTOR
# ═══════════════════════════════════════════════════════════════════════════════

class NameExtractor:
    \"\"\"Extract potential names and usernames from search results.\"\"\"

    # Common non-name words to filter out
    STOP_WORDS = {
        'image', 'images', 'photo', 'photos', 'picture', 'pictures', 'stock',
        'search', 'results', 'result', 'page', 'pages', 'site', 'website',
        'click', 'view', 'download', 'uploaded', 'share', 'free', 'online',
        'best', 'home', 'about', 'contact', 'login', 'sign', 'pinterest',
        'instagram', 'facebook', 'twitter', 'linkedin', 'youtube', 'tiktok',
        'reddit', 'tumblr', 'flickr', 'getty', 'shutterstock', 'alamy',
        'dreamstime', 'wikipedia', 'wiki', 'google', 'bing', 'yahoo',
        'similar', 'related', 'more', 'other', 'size', 'resolution',
        'no title', 'untitled', 'unknown', 'n/a', 'image result',
    }

    @staticmethod
    def extract_names(search_results: List[Dict]) -> List[str]:
        \"\"\"Extract potential person names from search result titles and URLs.\"\"\"
        candidates = []
        seen = set()

        for result in search_results:
            title = result.get('title', '')
            url = result.get('url', '')

            # From title
            names = NameExtractor._extract_from_title(title)
            for name in names:
                key = name.lower()
                if key not in seen and len(name) > 3:
                    seen.add(key)
                    candidates.append(name)

            # From URL path (social media profile URLs)
            username = NameExtractor._extract_from_url(url)
            if username and username.lower() not in seen:
                seen.add(username.lower())
                candidates.append(username)

        return candidates[:10]  # limit to top 10

    @staticmethod
    def _extract_from_title(title: str) -> List[str]:
        \"\"\"Extract name-like substrings from a result title.\"\"\"
        if not title or len(title) < 4:
            return []

        # Clean the title
        title = re.sub(r'[|•·—–]', ' - ', title)
        parts = [p.strip() for p in title.split('-')]

        names = []
        for part in parts:
            part = part.strip()
            if len(part) < 3 or len(part) > 50:
                continue
            if part.lower() in NameExtractor.STOP_WORDS:
                continue
            # Check if it looks like a name (2-4 capitalized words)
            words = part.split()
            if 1 <= len(words) <= 4:
                if all(w[0].isupper() or w[0] == '@' for w in words if len(w) > 0):
                    if not any(sw in part.lower() for sw in NameExtractor.STOP_WORDS):
                        names.append(part)
        return names

    @staticmethod
    def _extract_from_url(url: str) -> Optional[str]:
        \"\"\"Extract a username from a social media URL.\"\"\"
        try:
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            social_domains = ['instagram.com', 'twitter.com', 'x.com',
                            'facebook.com', 'linkedin.com', 'tiktok.com',
                            'github.com', 'pinterest.com', 'vk.com']
            if any(d in parsed.netloc for d in social_domains):
                segments = path.split('/')
                if segments:
                    username = segments[-1] if segments[-1] else (segments[-2] if len(segments) > 1 else None)
                    if username and len(username) > 1 and username not in ('in', 'p', 'status', 'post'):
                        return username.lstrip('@')
        except Exception:
            pass
        return None


# ═══════════════════════════════════════════════════════════════════════════════
#                         FACE ANALYSIS & CROPPING
# ═══════════════════════════════════════════════════════════════════════════════

class FaceAnalyzer:
    \"\"\"Detect, analyze and crop faces from images.\"\"\"

    @staticmethod
    def detect_and_analyze(image_path: str, verbose: bool = False) -> Dict:
        \"\"\"Full facial analysis pipeline.\"\"\"
        result = {
            \"image_path\": image_path,
            \"faces_detected\": 0,
            \"face_analyses\": [],
            \"facial_encodings\": [],
            \"cropped_face_paths\": [],
        }

        if not CV2_AVAILABLE or not FACE_REC_AVAILABLE:
            _log(\"[yellow]⚠ OpenCV/face_recognition not installed — using image-only mode[/yellow]\")
            result[\"faces_detected\"] = -1  # signal that face detection was skipped
            return result

        try:
            image = cv2.imread(image_path)
            if image is None:
                _log(f\"[red]✗ Cannot read image: {image_path}[/red]\")
                return result

            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Detect faces
            locations = face_recognition.face_locations(rgb, model='hog')
            encodings = face_recognition.face_encodings(rgb, locations) if locations else []

            result[\"faces_detected\"] = len(locations)

            for i, (loc, enc) in enumerate(zip(locations, encodings)):
                top, right, bottom, left = loc
                w, h = right - left, bottom - top

                # Facial landmarks
                landmarks = face_recognition.face_landmarks(rgb, [loc])
                landmark_summary = {}
                if landmarks:
                    landmark_summary = {k: len(v) for k, v in landmarks[0].items()}

                face_info = {
                    \"face_id\": i + 1,
                    \"location\": {\"top\": top, \"right\": right, \"bottom\": bottom, \"left\": left},
                    \"dimensions\": {\"width\": w, \"height\": h},
                    \"area_px\": w * h,
                    \"landmarks_detected\": landmark_summary,
                    \"encoding_dims\": len(enc),
                }
                result[\"face_analyses\"].append(face_info)
                result[\"facial_encodings\"].append(enc.tolist())

                # Crop face with padding for better reverse image search
                pad = int(max(w, h) * 0.4)
                y1 = max(0, top - pad)
                y2 = min(rgb.shape[0], bottom + pad)
                x1 = max(0, left - pad)
                x2 = min(rgb.shape[1], right + pad)
                cropped = image[y1:y2, x1:x2]

                # Save cropped face
                crop_dir = os.path.join(os.path.dirname(image_path), \"hafa_faces\")
                os.makedirs(crop_dir, exist_ok=True)
                crop_path = os.path.join(crop_dir, f\"face_{i+1}.jpg\")
                cv2.imwrite(crop_path, cropped)
                result[\"cropped_face_paths\"].append(crop_path)

                if verbose:
                    _log(f\"  [dim]Face {i+1}: {w}×{h}px, landmarks: {len(landmark_summary)} groups[/dim]\")

        except Exception as e:
            _log(f\"[red]✗ Face analysis error: {e}[/red]\")
            traceback.print_exc()

        return result


# ═══════════════════════════════════════════════════════════════════════════════
#                        RESULT DEDUPLICATION & SCORING
# ═══════════════════════════════════════════════════════════════════════════════

class ResultProcessor:
    \"\"\"Deduplicate, score, and categorize search results.\"\"\"

    SOCIAL_DOMAINS = {
        'instagram.com': 'Instagram', 'facebook.com': 'Facebook',
        'twitter.com': 'Twitter/X', 'x.com': 'Twitter/X',
        'linkedin.com': 'LinkedIn', 'tiktok.com': 'TikTok',
        'youtube.com': 'YouTube', 'reddit.com': 'Reddit',
        'pinterest.com': 'Pinterest', 'vk.com': 'VKontakte',
        'flickr.com': 'Flickr', 'github.com': 'GitHub',
        'tumblr.com': 'Tumblr', 'deviantart.com': 'DeviantArt',
        'medium.com': 'Medium', 'snapchat.com': 'Snapchat',
    }

    @staticmethod
    def process(raw_results: List[Dict]) -> List[Dict]:
        \"\"\"Deduplicate by URL domain+path, assign confidence scores, sort.\"\"\"
        seen_urls = set()
        processed = []

        for r in raw_results:
            url = r.get('url', '')
            if not url:
                continue

            # Normalize URL for dedup
            try:
                parsed = urlparse(url)
                key = f\"{parsed.netloc}{parsed.path}\".rstrip('/').lower()
            except Exception:
                key = url.lower()

            if key in seen_urls:
                continue
            seen_urls.add(key)

            # Assign confidence score
            score = ResultProcessor._compute_score(r)

            # Re-categorize based on domain
            category = r.get('category', 'web')
            for domain, platform in ResultProcessor.SOCIAL_DOMAINS.items():
                if domain in url:
                    category = 'social_media'
                    r['platform_name'] = platform
                    break

            r['confidence'] = score
            r['category'] = category
            processed.append(r)

        # Sort: social media first, then by confidence
        processed.sort(key=lambda x: (
            0 if x['category'] == 'social_media' else 1,
            -x['confidence']
        ))
        return processed

    @staticmethod
    def _compute_score(result: Dict) -> float:
        \"\"\"Heuristic confidence score 0.0 – 1.0.\"\"\"
        score = 0.3  # base

        url = result.get('url', '')
        title = result.get('title', '')
        snippet = result.get('snippet', '')

        # Social media boost
        if any(d in url for d in ResultProcessor.SOCIAL_DOMAINS):
            score += 0.3

        # Has a real title
        if title and len(title) > 5:
            score += 0.1

        # Has snippet
        if snippet and len(snippet) > 10:
            score += 0.05

        # Multiple engines found it
        # (this would be applied externally in aggregation)

        return min(score, 1.0)


# ═══════════════════════════════════════════════════════════════════════════════
#                           REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

class ReportGenerator:
    \"\"\"Generate professional OSINT reports in multiple formats.\"\"\"

    @staticmethod
    def generate_rich_report(analysis: Dict, exif: Dict, results: List[Dict],
                              names: List[str], social_profiles: List[Dict],
                              search_time: float):
        \"\"\"Print a beautiful Rich-formatted report to the terminal.\"\"\"
        if not RICH_AVAILABLE:
            ReportGenerator._generate_plain_report(analysis, exif, results, names, social_profiles, search_time)
            return

        console.print()
        console.print(Rule(\"[bold cyan]HAFA'S EYE — OSINT INTELLIGENCE REPORT[/bold cyan]\", style=\"cyan\"))
        console.print()

        # ── Target Overview ──
        overview_table = Table(title=\"🎯 Target Overview\", box=box.ROUNDED, show_header=False,
                                border_style=\"cyan\", expand=False)
        overview_table.add_column(\"Field\", style=\"bold\")
        overview_table.add_column(\"Value\")
        overview_table.add_row(\"Image\", str(analysis.get('image_path', 'N/A')))
        overview_table.add_row(\"Faces Detected\", str(analysis.get('faces_detected', 0)))
        overview_table.add_row(\"Search Duration\", f\"{search_time:.1f}s\")
        overview_table.add_row(\"Total Results\", str(len(results)))
        overview_table.add_row(\"Social Profiles\", str(len(social_profiles)))
        overview_table.add_row(\"Names Discovered\", ', '.join(names[:5]) if names else \"None\")
        overview_table.add_row(\"Timestamp\", datetime.datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\"))
        console.print(overview_table)
        console.print()

        # ── Face Analysis ──
        faces = analysis.get('face_analyses', [])
        if faces:
            face_table = Table(title=\"🧠 Facial Analysis\", box=box.ROUNDED, border_style=\"magenta\")
            face_table.add_column(\"#\", style=\"bold\")
            face_table.add_column(\"Size (px)\")
            face_table.add_column(\"Area\")
            face_table.add_column(\"Landmarks\")
            face_table.add_column(\"Cropped\")
            for f in faces:
                dims = f.get('dimensions', {})
                face_table.add_row(
                    str(f['face_id']),
                    f\"{dims.get('width', '?')}×{dims.get('height', '?')}\",
                    f\"{f.get('area_px', 0):,}\",
                    str(len(f.get('landmarks_detected', {}))),
                    \"✅\" if f['face_id'] <= len(analysis.get('cropped_face_paths', [])) else \"❌\",
                )
            console.print(face_table)
            console.print()

        # ── EXIF Intelligence ──
        if exif.get('has_exif'):
            exif_table = Table(title=\"📷 EXIF / Metadata Intelligence\", box=box.ROUNDED,
                               show_header=False, border_style=\"yellow\")
            exif_table.add_column(\"Field\", style=\"bold\")
            exif_table.add_column(\"Value\")
            for key in ['camera_make', 'camera_model', 'software', 'datetime_original',
                         'artist', 'copyright', 'description']:
                val = exif.get(key)
                if val:
                    exif_table.add_row(key.replace('_', ' ').title(), str(val))
            if exif.get('gps_lat'):
                exif_table.add_row(\"📍 GPS\", f\"{exif['gps_lat']}, {exif['gps_lon']}\")
                exif_table.add_row(\"🗺️  Map Link\", exif.get('gps_google_maps_url', ''))
            console.print(exif_table)
            console.print()

        # ── Search Results (grouped) ──
        social_results = [r for r in results if r.get('category') == 'social_media']
        web_results = [r for r in results if r.get('category') != 'social_media']

        if social_results:
            social_table = Table(title=\"🌐 Social Media Matches\", box=box.ROUNDED, border_style=\"green\")
            social_table.add_column(\"#\", style=\"bold\", width=3)
            social_table.add_column(\"Platform\", style=\"bold cyan\")
            social_table.add_column(\"Title\", max_width=40)
            social_table.add_column(\"URL\", max_width=55, style=\"underline blue\")
            social_table.add_column(\"Engine\")
            social_table.add_column(\"Score\", justify=\"right\")
            for i, r in enumerate(social_results[:20], 1):
                score = r.get('confidence', 0)
                score_color = \"green\" if score > 0.6 else \"yellow\" if score > 0.4 else \"dim\"
                social_table.add_row(
                    str(i),
                    r.get('platform_name', r.get('engine', '')),
                    (r.get('title', '')[:38] + '…') if len(r.get('title', '')) > 40 else r.get('title', ''),
                    r.get('url', '')[:53],
                    r.get('engine', ''),
                    f\"[{score_color}]{score:.0%}[/{score_color}]\",
                )
            console.print(social_table)
            console.print()

        if web_results:
            web_table = Table(title=\"🔗 Web Appearances\", box=box.ROUNDED, border_style=\"blue\")
            web_table.add_column(\"#\", style=\"bold\", width=3)
            web_table.add_column(\"Title\", max_width=45)
            web_table.add_column(\"URL\", max_width=55, style=\"underline blue\")
            web_table.add_column(\"Engine\")
            for i, r in enumerate(web_results[:15], 1):
                web_table.add_row(
                    str(i),
                    (r.get('title', '')[:43] + '…') if len(r.get('title', '')) > 45 else r.get('title', ''),
                    r.get('url', '')[:53],
                    r.get('engine', ''),
                )
            console.print(web_table)
            console.print()

        # ── Social Profile Enumeration ──
        if social_profiles:
            sp_table = Table(title=\"👤 Enumerated Social Profiles\", box=box.ROUNDED, border_style=\"magenta\")
            sp_table.add_column(\"Platform\", style=\"bold\")
            sp_table.add_column(\"Username\")
            sp_table.add_column(\"URL\", style=\"underline blue\")
            sp_table.add_column(\"Status\")
            for sp in social_profiles:
                sp_table.add_row(
                    sp.get('platform', ''),
                    sp.get('username', ''),
                    sp.get('url', ''),
                    \"[green]Likely exists[/green]\" if sp.get('status') == 'likely_exists' else \"[dim]Unknown[/dim]\",
                )
            console.print(sp_table)
            console.print()

        # ── Discovered Names ──
        if names:
            name_panel = Panel(
                \"\\n\".join([f\"  • {n}\" for n in names]),
                title=\"🏷️  Discovered Names / Usernames\",
                border_style=\"yellow\", expand=False,
            )
            console.print(name_panel)
            console.print()

        # Footer
        console.print(Panel(
            \"[yellow]⚠️  This tool is for authorized security research & education only.\\n\"
            \"Respect privacy laws (GDPR, CCPA). Unauthorized surveillance is illegal.[/yellow]\",
            border_style=\"red\",
        ))
        console.print()

    @staticmethod
    def _generate_plain_report(analysis, exif, results, names, social_profiles, search_time):
        \"\"\"Fallback plain text report if Rich is not available.\"\"\"
        print(\"\\n\" + \"═\" * 80)
        print(\"          HAFA'S EYE — OSINT INTELLIGENCE REPORT\")
        print(\"═\" * 80)
        print(f\"  Image       : {analysis.get('image_path', 'N/A')}\")
        print(f\"  Faces       : {analysis.get('faces_detected', 0)}\")
        print(f\"  Results     : {len(results)}\")
        print(f\"  Time        : {search_time:.1f}s\")
        print(f\"  Names Found : {', '.join(names[:5]) if names else 'None'}\")
        print(\"─\" * 80)

        if exif.get('has_exif'):
            print(\"\\n📷 EXIF METADATA:\")
            for k in ['camera_make', 'camera_model', 'software', 'datetime_original', 'artist']:
                v = exif.get(k)
                if v:
                    print(f\"  {k}: {v}\")
            if exif.get('gps_lat'):
                print(f\"  GPS: {exif['gps_lat']}, {exif['gps_lon']}\")
                print(f\"  Map: {exif.get('gps_google_maps_url', '')}\")

        if results:
            print(f\"\\n🔍 SEARCH RESULTS ({len(results)}):\")
            for i, r in enumerate(results[:25], 1):
                cat = \"🌐\" if r.get('category') == 'social_media' else \"🔗\"
                print(f\"  {cat} [{r.get('engine', '')}] {r.get('title', '')[:50]}\")
                print(f\"     {r.get('url', '')}\")

        if social_profiles:
            print(f\"\\n👤 SOCIAL PROFILES ({len(social_profiles)}):\")
            for sp in social_profiles:
                print(f\"  ✓ {sp['platform']}: {sp['url']}\")

        print(\"\\n⚠️  Educational / authorized research use only.\")
        print(\"═\" * 80)

    @staticmethod
    def save_json(filepath: str, analysis: Dict, exif: Dict, results: List[Dict],
                  names: List[str], social_profiles: List[Dict], search_time: float):
        \"\"\"Save complete results as JSON.\"\"\"
        report = {
            \"tool\": \"HaFa's EyE\",
            \"version\": VERSION,
            \"timestamp\": datetime.datetime.now().isoformat(),
            \"search_duration_seconds\": round(search_time, 2),
            \"target_image\": analysis.get('image_path'),
            \"faces_detected\": analysis.get('faces_detected', 0),
            \"face_analyses\": analysis.get('face_analyses', []),
            \"cropped_faces\": analysis.get('cropped_face_paths', []),
            \"exif_intelligence\": {k: v for k, v in exif.items() if k != 'all_tags' and v is not None},
            \"exif_all_tags\": exif.get('all_tags', {}),
            \"discovered_names\": names,
            \"search_results\": results,
            \"social_profiles_enumerated\": social_profiles,
            \"total_results\": len(results),
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        _log(f\"[green]💾 JSON report saved → {filepath}[/green]\")

    @staticmethod
    def save_html(filepath: str, analysis: Dict, exif: Dict, results: List[Dict],
                  names: List[str], social_profiles: List[Dict], search_time: float):
        \"\"\"Save a professional HTML report.\"\"\"
        social_results = [r for r in results if r.get('category') == 'social_media']
        web_results = [r for r in results if r.get('category') != 'social_media']

        html = f\"\"\"<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>HaFa's EyE — OSINT Report</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#0a0a0f;color:#e0e0e0;padding:2rem}}
.container{{max-width:1100px;margin:0 auto}}
h1{{text-align:center;font-size:2rem;background:linear-gradient(135deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.3rem}}
.subtitle{{text-align:center;color:#888;margin-bottom:2rem}}
.card{{background:#12121a;border:1px solid #252530;border-radius:12px;padding:1.5rem;margin-bottom:1.5rem}}
.card h2{{color:#00d4ff;font-size:1.1rem;margin-bottom:1rem;border-bottom:1px solid #252530;padding-bottom:.5rem}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;color:#888;padding:.5rem;font-weight:500;border-bottom:1px solid #252530}}
td{{padding:.5rem;border-bottom:1px solid #1a1a25}}
a{{color:#00d4ff;text-decoration:none}}
a:hover{{text-decoration:underline}}
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.75rem;font-weight:600}}
.badge-social{{background:#1a3a1a;color:#4ade80}}
.badge-web{{background:#1a1a3a;color:#60a5fa}}
.score{{font-weight:700}}
.score-high{{color:#4ade80}}
.score-med{{color:#facc15}}
.score-low{{color:#888}}
.warning{{background:#2a1a0a;border:1px solid #f59e0b;border-radius:8px;padding:1rem;margin-top:2rem;color:#fbbf24;text-align:center}}
.gps-link{{color:#f59e0b}}
</style>
</head>
<body>
<div class=\"container\">
<h1>🔍 HaFa's EyE — OSINT Intelligence Report</h1>
<p class=\"subtitle\">Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · v{VERSION}</p>

<div class=\"card\">
<h2>🎯 Target Summary</h2>
<table>
<tr><td><strong>Image</strong></td><td>{analysis.get('image_path','N/A')}</td></tr>
<tr><td><strong>Faces Detected</strong></td><td>{analysis.get('faces_detected',0)}</td></tr>
<tr><td><strong>Search Time</strong></td><td>{search_time:.1f}s</td></tr>
<tr><td><strong>Total Results</strong></td><td>{len(results)}</td></tr>
<tr><td><strong>Names Discovered</strong></td><td>{', '.join(names[:5]) if names else 'None'}</td></tr>
</table>
</div>
\"\"\"
        # EXIF card
        if exif.get('has_exif'):
            html += '<div class=\"card\"><h2>📷 EXIF Metadata Intelligence</h2><table>'
            for k in ['camera_make','camera_model','software','datetime_original','artist','copyright']:
                v = exif.get(k)
                if v:
                    html += f'<tr><td><strong>{k.replace(\"_\",\" \").title()}</strong></td><td>{v}</td></tr>'
            if exif.get('gps_lat'):
                html += f'<tr><td><strong>📍 GPS</strong></td><td>{exif[\"gps_lat\"]}, {exif[\"gps_lon\"]} — <a class=\"gps-link\" href=\"{exif.get(\"gps_google_maps_url\",\"\")}\" target=\"_blank\">Open in Maps</a></td></tr>'
            html += '</table></div>'

        # Social media results
        if social_results:
            html += '<div class=\"card\"><h2>🌐 Social Media Matches</h2><table><tr><th>#</th><th>Platform</th><th>Title</th><th>URL</th><th>Engine</th><th>Score</th></tr>'
            for i, r in enumerate(social_results[:25], 1):
                sc = r.get('confidence', 0)
                sc_cls = 'score-high' if sc > 0.6 else 'score-med' if sc > 0.4 else 'score-low'
                html += f'<tr><td>{i}</td><td>{r.get(\"platform_name\",r.get(\"engine\",\"\"))}</td><td>{r.get(\"title\",\"\")[:50]}</td><td><a href=\"{r[\"url\"]}\" target=\"_blank\">{r[\"url\"][:60]}</a></td><td>{r.get(\"engine\",\"\")}</td><td class=\"score {sc_cls}\">{sc:.0%}</td></tr>'
            html += '</table></div>'

        # Web results
        if web_results:
            html += '<div class=\"card\"><h2>🔗 Web Appearances</h2><table><tr><th>#</th><th>Title</th><th>URL</th><th>Engine</th></tr>'
            for i, r in enumerate(web_results[:20], 1):
                html += f'<tr><td>{i}</td><td>{r.get(\"title\",\"\")[:55]}</td><td><a href=\"{r[\"url\"]}\" target=\"_blank\">{r[\"url\"][:65]}</a></td><td>{r.get(\"engine\",\"\")}</td></tr>'
            html += '</table></div>'

        # Social profiles
        if social_profiles:
            html += '<div class=\"card\"><h2>👤 Enumerated Social Profiles</h2><table><tr><th>Platform</th><th>Username</th><th>URL</th><th>Status</th></tr>'
            for sp in social_profiles:
                html += f'<tr><td>{sp[\"platform\"]}</td><td>{sp.get(\"username\",\"\")}</td><td><a href=\"{sp[\"url\"]}\" target=\"_blank\">{sp[\"url\"]}</a></td><td><span class=\"badge badge-social\">Likely exists</span></td></tr>'
            html += '</table></div>'

        html += \"\"\"
<div class=\"warning\">
⚠️ This report is for authorized security research & educational purposes only.<br>
Respect privacy laws (GDPR, CCPA). Unauthorized surveillance is illegal.
</div>
</div></body></html>\"\"\"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        _log(f\"[green]💾 HTML report saved → {filepath}[/green]\")


# ═══════════════════════════════════════════════════════════════════════════════
#                          MAIN HAFA'S EYE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class HafaEye:
    \"\"\"
    HaFa's EyE v3.0 — The OSINT People Finder.

    Workflow:
      1. Load & validate the target image
      2. Extract EXIF / metadata intelligence
      3. Detect and crop faces
      4. Run parallel reverse image searches across 5+ engines
      5. Search each cropped face separately for better results
      6. Extract names / usernames from results
      7. Enumerate social profiles for discovered names
      8. Text-search discovered names via DuckDuckGo
      9. Deduplicate, score, and rank all results
     10. Generate professional reports (terminal, JSON, HTML)
    \"\"\"

    BANNER = r\"\"\"
    ██╗  ██╗ █████╗ ███████╗ █████╗ ███████╗    ███████╗██╗   ██╗███████╗
    ██║  ██║██╔══██╗██╔════╝██╔══██╗██╔════╝    ██╔════╝╚██╗ ██╔╝██╔════╝
    ███████║███████║█████╗  ███████║███████╗     █████╗   ╚████╔╝ █████╗  
    ██╔══██║██╔══██║██╔══╝  ██╔══██║╚════██║    ██╔══╝    ╚██╔╝  ██╔══╝  
    ██║  ██║██║  ██║██║     ██║  ██║███████║    ███████╗   ██║   ███████╗
    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝    ╚══════╝   ╚═╝   ╚══════╝
                  ◆  ADVANCED OSINT PEOPLE FINDER  ◆
                   «  NO API KEYS REQUIRED  v3.0  »
    \"\"\"

    def __init__(self, verbose: bool = False, engines: List[str] = None):
        self.verbose = verbose
        self.engines = self._init_engines(engines)
        self._display_banner()

    def _init_engines(self, engine_names: Optional[List[str]]) -> List[SearchEngine]:
        \"\"\"Initialize selected search engines.\"\"\"
        if not engine_names:
            return ALL_ENGINES[:]
        name_map = {e.name.lower(): e for e in ALL_ENGINES}
        selected = []
        for n in engine_names:
            eng = name_map.get(n.lower())
            if eng:
                selected.append(eng)
        return selected if selected else ALL_ENGINES[:]

    def _display_banner(self):
        \"\"\"Show the startup banner.\"\"\"
        if RICH_AVAILABLE and console:
            console.print(Panel(
                Align.center(Text(self.BANNER.strip(), style=\"bold cyan\")),
                border_style=\"cyan\", expand=False, padding=(0, 2),
            ))
            console.print(Panel(
                \"[bold red]⚠️  ETHICAL USE ONLY[/bold red]\\n\"
                \"• For authorized OSINT research & education only\\n\"
                \"• Respect privacy laws (GDPR, CCPA, etc.)\\n\"
                \"• Unauthorized surveillance is [bold]illegal[/bold]\",
                border_style=\"red\", expand=False,
            ))
        else:
            print(self.BANNER)
            print(\"⚠️  ETHICAL USE ONLY — For authorized research & education only\")
            print(\"─\" * 60)

    def _check_image(self, path: str) -> bool:
        \"\"\"Validate the image file.\"\"\"
        if not os.path.isfile(path):
            _log(f\"[red]✗ File not found: {path}[/red]\")
            return False
        ext = Path(path).suffix.lower()
        if ext not in SUPPORTED_FORMATS:
            _log(f\"[red]✗ Unsupported format: {ext}  (supported: {', '.join(SUPPORTED_FORMATS)})[/red]\")
            return False
        return True

    def hunt(self, image_path: str, output_json: str = None, output_html: str = None,
             skip_faces: bool = False, skip_social_enum: bool = False) -> Dict:
        \"\"\"
        🔥 Main OSINT hunt pipeline.

        Args:
            image_path: Path to the target face image.
            output_json: Optional path to save JSON report.
            output_html: Optional path to save HTML report.
            skip_faces: Skip face detection (search image as-is).
            skip_social_enum: Skip social profile enumeration.

        Returns:
            Complete results dictionary.
        \"\"\"
        start_time = time.time()

        # ── Step 0: Validate ──
        image_path = os.path.abspath(image_path)
        if not self._check_image(image_path):
            return {}

        _log(f\"\\n[bold cyan]🎯 Target:[/bold cyan] {image_path}\")
        _log(f\"[bold cyan]⏱  Started:[/bold cyan] {datetime.datetime.now().strftime('%H:%M:%S')}\")
        _log(f\"[bold cyan]🔧 Engines:[/bold cyan] {', '.join(e.name for e in self.engines)}\")

        # ── Step 1: EXIF Intel ──
        _log(\"\\n[bold]📷 Phase 1 — Extracting EXIF Intelligence...[/bold]\")
        exif_intel = ExifIntel.extract(image_path)
        if exif_intel.get('has_exif'):
            interesting_keys = ['camera_make', 'camera_model', 'software',
                                'datetime_original', 'artist', 'gps_lat']
            found_tags = [k for k in interesting_keys if exif_intel.get(k)]
            _log(f\"  [green]✓ EXIF data found:[/green] {len(found_tags)} useful tags\")
            if exif_intel.get('gps_lat'):
                _log(f\"  [yellow]📍 GPS COORDINATES FOUND: {exif_intel['gps_lat']}, {exif_intel['gps_lon']}[/yellow]\")
                _log(f\"  [yellow]🗺️  {exif_intel['gps_google_maps_url']}[/yellow]\")
        else:
            _log(\"  [dim]No EXIF metadata found (stripped or unavailable)[/dim]\")

        # ── Step 2: Face Detection ──
        _log(\"\\n[bold]🧠 Phase 2 — Facial Detection & Analysis...[/bold]\")
        if skip_faces:
            analysis = {\"image_path\": image_path, \"faces_detected\": 0,
                        \"face_analyses\": [], \"facial_encodings\": [], \"cropped_face_paths\": []}
            _log(\"  [dim]Face detection skipped (--no-faces flag)[/dim]\")
        else:
            analysis = FaceAnalyzer.detect_and_analyze(image_path, verbose=self.verbose)
            n = analysis.get('faces_detected', 0)
            if n > 0:
                _log(f\"  [green]✓ Detected {n} face(s) — cropped & saved[/green]\")
            elif n == 0:
                _log(\"  [yellow]⚠ No faces detected — searching full image[/yellow]\")
            else:
                _log(\"  [yellow]⚠ Face libraries not installed — using full image mode[/yellow]\")

        # ── Step 3: Multi-Engine Reverse Image Search ──
        _log(f\"\\n[bold]🔍 Phase 3 — Reverse Image Search ({len(self.engines)} engines)...[/bold]\")
        all_raw_results = []

        # Search with original image
        images_to_search = [image_path]
        # Add cropped faces for targeted search
        cropped = analysis.get('cropped_face_paths', [])
        if cropped:
            images_to_search.extend(cropped[:3])  # limit to first 3 faces
            _log(f\"  [dim]Searching original + {len(cropped[:3])} cropped face(s)[/dim]\")

        for img in images_to_search:
            img_label = \"ORIGINAL\" if img == image_path else f\"FACE-{images_to_search.index(img)}\"

            if RICH_AVAILABLE and console:
                with Progress(
                    SpinnerColumn(),
                    TextColumn(\"[progress.description]{task.description}\"),
                    BarColumn(bar_width=20),
                    TextColumn(\"{task.completed}/{task.total}\"),
                    console=console, transient=True,
                ) as progress:
                    task = progress.add_task(f\"[cyan]Searching [{img_label}]...\", total=len(self.engines))
                    for engine in self.engines:
                        progress.update(task, description=f\"[cyan]{engine.icon} {engine.name} [{img_label}]\")
                        engine_results = engine.search(img, verbose=self.verbose)
                        for r in engine_results:
                            r['source_image'] = img_label
                        all_raw_results.extend(engine_results)
                        _log(f\"  {engine.icon} {engine.name}: [green]{len(engine_results)}[/green] results\")
                        progress.advance(task)
            else:
                for engine in self.engines:
                    print(f\"  {engine.icon} Searching {engine.name} [{img_label}]...\")
                    engine_results = engine.search(img, verbose=self.verbose)
                    for r in engine_results:
                        r['source_image'] = img_label
                    all_raw_results.extend(engine_results)
                    print(f\"    → {len(engine_results)} results\")

        _log(f\"\\n  [bold]Raw results collected: {len(all_raw_results)}[/bold]\")

        # ── Step 4: Name Extraction ──
        _log(\"\\n[bold]🏷️  Phase 4 — Name & Identity Extraction...[/bold]\")
        names = NameExtractor.extract_names(all_raw_results)
        if names:
            _log(f\"  [green]✓ Discovered {len(names)} potential name(s):[/green]\")
            for n in names[:5]:
                _log(f\"    • {n}\")
        else:
            _log(\"  [dim]No names could be extracted from results[/dim]\")

        # ── Step 5: DuckDuckGo Name Search ──
        if names:
            _log(\"\\n[bold]🦆 Phase 5 — DuckDuckGo Name Search...[/bold]\")
            for name in names[:3]:
                ddg_results = DuckDuckGoSearch.search_by_name(name, verbose=self.verbose)
                all_raw_results.extend(ddg_results)
                _log(f\"  🦆 \\\"{name}\\\": [green]{len(ddg_results)}[/green] results\")
                time.sleep(1.5)  # be polite to DDG

        # ── Step 6: Social Profile Enumeration ──
        social_profiles = []
        if not skip_social_enum and names:
            _log(\"\\n[bold]👤 Phase 6 — Social Profile Enumeration...[/bold]\")
            for name in names[:3]:
                # Try different username formats
                usernames = set()
                usernames.add(name.lower().replace(' ', ''))
                usernames.add(name.lower().replace(' ', '_'))
                usernames.add(name.lower().replace(' ', '.'))
                parts = name.lower().split()
                if len(parts) >= 2:
                    usernames.add(parts[0] + parts[-1])
                    usernames.add(parts[0][0] + parts[-1])
                    usernames.add(parts[0] + '.' + parts[-1])

                for uname in usernames:
                    _log(f\"  [dim]Enumerating @{uname}...[/dim]\")
                    profiles = SocialProfileEnumerator.enumerate(uname, verbose=self.verbose)
                    social_profiles.extend(profiles)
                    time.sleep(0.5)

            if social_profiles:
                _log(f\"  [green]✓ Found {len(social_profiles)} potential profile(s)[/green]\")
            else:
                _log(\"  [dim]No confirmed profiles found[/dim]\")
        elif skip_social_enum:
            _log(\"\\n  [dim]Social profile enumeration skipped (--no-social flag)[/dim]\")

        # ── Step 7: Process & Deduplicate ──
        _log(\"\\n[bold]🧹 Phase 7 — Deduplication & Scoring...[/bold]\")
        processed_results = ResultProcessor.process(all_raw_results)
        _log(f\"  [green]✓ {len(all_raw_results)} raw → {len(processed_results)} unique results[/green]\")

        search_time = time.time() - start_time

        # ── Step 8: Generate Reports ──
        _log(f\"\\n[bold]📊 Phase 8 — Report Generation...[/bold]\")
        ReportGenerator.generate_rich_report(
            analysis, exif_intel, processed_results, names, social_profiles, search_time
        )

        if output_json:
            ReportGenerator.save_json(output_json, analysis, exif_intel, processed_results,
                                      names, social_profiles, search_time)
        if output_html:
            ReportGenerator.save_html(output_html, analysis, exif_intel, processed_results,
                                      names, social_profiles, search_time)

        # Auto-save JSON if no output specified
        if not output_json and not output_html:
            auto_json = os.path.splitext(image_path)[0] + \"_hafa_report.json\"
            ReportGenerator.save_json(auto_json, analysis, exif_intel, processed_results,
                                      names, social_profiles, search_time)

        _log(f\"\\n[bold green]✅ Hunt complete in {search_time:.1f}s — {len(processed_results)} results found[/bold green]\")

        return {
            \"analysis\": analysis,
            \"exif\": exif_intel,
            \"results\": processed_results,
            \"names\": names,
            \"social_profiles\": social_profiles,
            \"search_time\": search_time,
        }


# ═══════════════════════════════════════════════════════════════════════════════
#                            CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description=\"HaFa's EyE v3.0 — Advanced OSINT People Finder (No API Keys Required)\",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=\"\"\"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  EXAMPLES:
    %(prog)s photo.jpg                           # Full OSINT hunt
    %(prog)s photo.jpg --verbose                 # Verbose output
    %(prog)s photo.jpg -o report.json            # Save JSON report
    %(prog)s photo.jpg --html report.html        # Save HTML report
    %(prog)s photo.jpg --no-faces                # Skip face detection
    %(prog)s photo.jpg --no-social               # Skip social enumeration
    %(prog)s photo.jpg --engines google yandex   # Use specific engines only
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⚠️  For authorized security research & education only.
        \"\"\",
    )

    parser.add_argument(\"image\", help=\"Path to the target image\")
    parser.add_argument(\"-v\", \"--verbose\", action=\"store_true\", help=\"Enable verbose output\")
    parser.add_argument(\"-o\", \"--output\", help=\"Output JSON report path\")
    parser.add_argument(\"--html\", help=\"Output HTML report path\")
    parser.add_argument(\"--no-faces\", action=\"store_true\", help=\"Skip face detection (search image as-is)\")
    parser.add_argument(\"--no-social\", action=\"store_true\", help=\"Skip social profile enumeration\")
    parser.add_argument(\"--engines\", nargs='+',
                       choices=['google', 'yandex', 'bing', 'tineye', 'baidu'],
                       help=\"Select specific search engines (default: all)\")

    args = parser.parse_args()

    # Map engine names
    engine_map = {
        'google': 'Google Lens',
        'yandex': 'Yandex Images',
        'bing': 'Bing Visual Search',
        'tineye': 'TinEye',
        'baidu': 'Baidu Images',
    }
    engine_names = [engine_map[e] for e in args.engines] if args.engines else None

    # Initialize and run
    eye = HafaEye(verbose=args.verbose, engines=engine_names)
    result = eye.hunt(
        image_path=args.image,
        output_json=args.output,
        output_html=args.html,
        skip_faces=args.no_faces,
        skip_social_enum=args.no_social,
    )

    return 0 if result else 1


if __name__ == \"__main__\":
    sys.exit(main())
