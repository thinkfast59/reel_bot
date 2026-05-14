import os
import re
import json
import time
import random
import requests
import feedparser
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
from googletrans import Translator
from moviepy.editor import ImageClip, AudioFileClip

PAGE_ID = "1020689164470492"
PAGE_ACCESS_TOKEN = "EAIFMs5yoDt0BReZCljKCTlLWF7bEI3supybEvkRQooWKtf8g45g9nKg2ZCGHudumMlVdXLp67MyhZCi3Eb1vCZCZBxZA0814L1sw6jW6zvZBdnZCSolUIZBylmUvDVc60HfeDWHJCAELklhzZBf7SCZAAPZCtATBU00uZA9ZCYVjjk4viehzcZACaVPVR7wsnu3mqPXcnTUG3YRG0wPZCQKpcMXkBkUyeW7cadEvSPiZBqOnWMpCqY684DOM0cGPZCCeoZD"

POSTED_FILE = "posted_reels.json"
IMAGE_FILE = "reel_bg.jpg"
VOICE_FILE = "voice.mp3"
VIDEO_FILE = "sinhala_reel.mp4"

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://feeds.bbci.co.uk/news/health/rss.xml",
]

translator = Translator()

# ===============================
# Helpers
# ===============================

def clean_text(text):
    if not text:
        return ""
    text = re.sub("<.*?>", "", text)
    text = text.replace("&amp;", "&").replace("&quot;", '"').replace("&nbsp;", " ")
    return text.strip()

def is_good_sinhala(text):
    if not text:
        return False

    sinhala_chars = sum(1 for c in text if "\u0D80" <= c <= "\u0DFF")
    bad_chars = text.count("�")

    if bad_chars > 0:
        return False

    if sinhala_chars < 5:
        return False

    return True

def safe_translate(text):
    try:
        translated = translator.translate(text, dest="si").text
        translated = clean_text(translated)

        if is_good_sinhala(translated):
            return translated

        return text

    except Exception:
        return text

def get_article_image(entry):
    # media:thumbnail
    if "media_thumbnail" in entry:
        try:
            return entry.media_thumbnail[0]["url"]
        except Exception:
            pass

    # media:content
    if "media_content" in entry:
        try:
            return entry.media_content[0]["url"]
        except Exception:
            pass

    # enclosures
    if "enclosures" in entry:
        try:
            for enc in entry.enclosures:
                if "image" in enc.get("type", ""):
                    return enc.get("href")
        except Exception:
            pass

    # image inside summary html
    if hasattr(entry, "summary"):
        match = re.search(r'<img[^>]+src="([^"]+)"', entry.summary)
        if match:
            return match.group(1)

    return None

def load_font(size):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSansSinhala-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerifSinhala-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansSinhala-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()

def wrap_text(text, max_chars=24, max_lines=7):
    words = text.split()
    lines = []
    line = ""

    for word in words:
        test = f"{line} {word}".strip()

        if len(test) <= max_chars:
            line = test
        else:
            if line:
                lines.append(line)
            line = word

    if line:
        lines.append(line)

    return "\n".join(lines[:max_lines])

def create_brand_background():
    img = Image.new("RGB", (1080, 1920), (12, 24, 48))
    draw = ImageDraw.Draw(img)

    for y in range(1920):
        shade = int(20 + (y / 1920) * 50)
        draw.line((0, y, 1080, y), fill=(8, shade, 70))

    return img

def create_background(article_image_url):
    if article_image_url:
        try:
            print("🖼 Using article image:", article_image_url)
            r = requests.get(article_image_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            img = Image.open(BytesIO(r.content)).convert("RGB")

            # cover crop to 1080x1920
            w, h = img.size
            target_ratio = 1080 / 1920
            img_ratio = w / h

            if img_ratio > target_ratio:
                new_w = int(h * target_ratio)
                left = (w - new_w) // 2
                img = img.crop((left, 0, left + new_w, h))
            else:
                new_h = int(w / target_ratio)
                top = (h - new_h) // 2
                img = img.crop((0, top, w, top + new_h))

            img = img.resize((1080, 1920))
            img = img.filter(ImageFilter.GaussianBlur(radius=2))
            return img

        except Exception as e:
            print("⚠️ Article image failed:", e)

    print("🖼 Using branded fallback background")
    return create_brand_background()

# ===============================
# Load posted
# ===============================

if not os.path.exists(POSTED_FILE):
    with open(POSTED_FILE, "w") as f:
        json.dump([], f)

try:
    with open(POSTED_FILE, "r") as f:
        posted = json.load(f)
except Exception:
    posted = []

print("🎬 Real Sinhala Reel Bot Started")

# ===============================
# Fetch news
# ===============================

articles = []

for feed in RSS_FEEDS:
    data = feedparser.parse(feed)

    for entry in data.entries[:15]:
        if hasattr(entry, "link") and entry.link not in posted:
            articles.append(entry)

if not articles:
    print("❌ No new articles")
    exit()

news = random.choice(articles)

title_en = clean_text(news.title)
link = news.link
summary_en = clean_text(getattr(news, "summary", ""))

title_si = safe_translate(title_en)
summary_si = safe_translate(summary_en) if summary_en else ""

article_image = get_article_image(news)

# ===============================
# Script + caption
# ===============================

if is_good_sinhala(title_si):
    voice_title = title_si
else:
    voice_title = title_en

script = f"""
ලෝක පුවත් සිංහලෙන්.

අද ප්‍රධාන පුවත.

{voice_title}

මෙය ලෝකයේ බොහෝ දෙනාගේ අවධානයට ලක්ව ඇති වැදගත් පුවතකි.

වැඩි විස්තර සඳහා World News in Sinhala පිටුව follow කරන්න.
"""

caption = f"""
🌍 ලෝක පුවත් සිංහලෙන්

🔥 {title_si}

👉 වැඩි විස්තර:
{link}

#ලෝකපුවත් #සිංහලපුවත් #WorldNews #BreakingNews
"""

# ===============================
# Voice
# ===============================

tts = gTTS(text=script, lang="si")
tts.save(VOICE_FILE)
print("🎙 Voice created")

# ===============================
# Image design
# ===============================

img = create_background(article_image)

# dark overlay
overlay = Image.new("RGB", (1080, 1920), (0, 0, 0))
img = Image.blend(img, overlay, 0.55)

draw = ImageDraw.Draw(img)

font_big = load_font(64)
font_medium = load_font(52)
font_small = load_font(40)

# top label
draw.rounded_rectangle((55, 80, 1025, 210), radius=40, fill=(0, 0, 0))
draw.text((95, 115), "🌍 ලෝක පුවත් සිංහලෙන්", fill="white", font=font_big)

# title card
draw.rounded_rectangle((55, 360, 1025, 1220), radius=45, fill=(0, 0, 0))
draw.text((95, 430), wrap_text(title_si, 24, 8), fill="white", font=font_medium)

# footer
draw.rounded_rectangle((55, 1540, 1025, 1720), radius=35, fill=(0, 0, 0))
draw.text((95, 1575), "වැඩි විස්තර සඳහා Follow කරන්න", fill="white", font=font_small)
draw.text((95, 1640), "World News in Sinhala", fill="white", font=font_small)

img.save(IMAGE_FILE, "JPEG", quality=95)
print("🖼 Image created")

# ===============================
# Create MP4 video
# ===============================

audio = AudioFileClip(VOICE_FILE)

clip = ImageClip(IMAGE_FILE).set_duration(audio.duration)
clip = clip.set_audio(audio)

clip.write_videofile(
    VIDEO_FILE,
    fps=30,
    codec="libx264",
    audio_codec="aac",
    preset="medium",
    ffmpeg_params=[
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-profile:v", "baseline",
        "-level", "3.1"
    ]
)

print("✅ Video created")

# ===============================
# Facebook Reel Upload
# ===============================

print("🚀 Starting Facebook Reel upload")

start_url = f"https://graph.facebook.com/v23.0/{PAGE_ID}/video_reels"

start_data = {
    "upload_phase": "start",
    "access_token": PAGE_ACCESS_TOKEN
}

start_res = requests.post(start_url, data=start_data)
start_json = start_res.json()

print("START:", start_json)

if "video_id" not in start_json or "upload_url" not in start_json:
    print("❌ Failed to start upload")
    exit()

video_id = start_json["video_id"]
upload_url = start_json["upload_url"]

file_size = os.path.getsize(VIDEO_FILE)

with open(VIDEO_FILE, "rb") as video_file:
    upload_headers = {
        "Authorization": f"OAuth {PAGE_ACCESS_TOKEN}",
        "offset": "0",
        "file_size": str(file_size),
    }

    upload_res = requests.post(upload_url, headers=upload_headers, data=video_file)

print("UPLOAD:", upload_res.text)

finish_data = {
    "upload_phase": "finish",
    "video_id": video_id,
    "video_state": "PUBLISHED",
    "description": caption,
    "access_token": PAGE_ACCESS_TOKEN
}

finish_res = requests.post(start_url, data=finish_data)
finish_json = finish_res.json()

print("FINISH:", finish_json)

# ===============================
# Check status
# ===============================

print("⏳ Checking Reel status")

ready = False

for i in range(18):
    time.sleep(10)

    status_url = f"https://graph.facebook.com/v23.0/{video_id}"

    status_params = {
        "fields": "status,permalink_url",
        "access_token": PAGE_ACCESS_TOKEN
    }

    status_res = requests.get(status_url, params=status_params)
    status_json = status_res.json()

    print("STATUS:", status_json)

    status = status_json.get("status", {})

    if isinstance(status, dict):
        if status.get("video_status") == "ready":
            ready = True
            print("✅ REEL READY")
            break

        if status.get("video_status") == "error":
            print("❌ FACEBOOK PROCESSING ERROR")
            break

# ===============================
# Save posted
# ===============================

if finish_res.status_code == 200 and finish_json.get("success") == True:
    print("✅ REEL UPLOAD ACCEPTED")

    posted.append(link)

    with open(POSTED_FILE, "w") as f:
        json.dump(posted, f)

    if ready:
        print("✅ Reel should appear on page")
    else:
        print("⚠️ Reel accepted but may still be processing")
else:
    print("❌ Reel failed")
