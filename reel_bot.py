import os
import re
import json
import time
import random
import requests
import feedparser
from gtts import gTTS
from PIL import Image, ImageFilter
from io import BytesIO
from googletrans import Translator
from moviepy.editor import ImageClip, AudioFileClip

# ===============================
# FACEBOOK CONFIG
# ===============================

PAGE_ID = "1020689164470492"
PAGE_ACCESS_TOKEN = "EAIFMs5yoDt0BReZCljKCTlLWF7bEI3supybEvkRQooWKtf8g45g9nKg2ZCGHudumMlVdXLp67MyhZCi3Eb1vCZCZBxZA0814L1sw6jW6zvZBdnZCSolUIZBylmUvDVc60HfeDWHJCAELklhzZBf7SCZAAPZCtATBU00uZA9ZCYVjjk4viehzcZACaVPVR7wsnu3mqPXcnTUG3YRG0wPZCQKpcMXkBkUyeW7cadEvSPiZBqOnWMpCqY684DOM0cGPZCCeoZD"

# ===============================
# FILES
# ===============================

POSTED_FILE = "posted_reels.json"
IMAGE_FILE = "reel_bg.jpg"
VOICE_FILE = "voice.mp3"
VIDEO_FILE = "sinhala_reel.mp4"

# ===============================
# NEWS SOURCES
# ===============================

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://feeds.bbci.co.uk/news/health/rss.xml",
]

translator = Translator()

# ===============================
# HELPERS
# ===============================

def clean_text(text):
    if not text:
        return ""
    text = re.sub("<.*?>", "", text)
    text = text.replace("&amp;", "&")
    text = text.replace("&quot;", '"')
    text = text.replace("&nbsp;", " ")
    text = text.replace("\n", " ")
    return text.strip()

def is_good_sinhala(text):
    if not text:
        return False
    sinhala_chars = sum(1 for c in text if "\u0D80" <= c <= "\u0DFF")
    if "�" in text:
        return False
    return sinhala_chars >= 5

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
    if "media_thumbnail" in entry:
        try:
            return entry.media_thumbnail[0]["url"]
        except Exception:
            pass

    if "media_content" in entry:
        try:
            return entry.media_content[0]["url"]
        except Exception:
            pass

    if "enclosures" in entry:
        try:
            for enc in entry.enclosures:
                if "image" in enc.get("type", ""):
                    return enc.get("href")
        except Exception:
            pass

    if hasattr(entry, "summary"):
        match = re.search(r'<img[^>]+src="([^"]+)"', entry.summary)
        if match:
            return match.group(1)

    return None

def download_image(url):
    try:
        response = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        img = Image.open(BytesIO(response.content)).convert("RGB")
        return img

    except Exception as e:
        print("Image download failed:", e)
        return None

def cover_resize(img, target_w=1080, target_h=1920):

    w, h = img.size

    scale = max(target_w / w, target_h / h)

    new_w = int(w * scale)
    new_h = int(h * scale)

    img = img.resize((new_w, new_h))

    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2

    img = img.crop((
        left,
        top,
        left + target_w,
        top + target_h
    ))

    return img
def create_fallback_image():
    img_url = f"https://picsum.photos/1080/1920?random={random.randint(1,999999)}"
    img = download_image(img_url)

    if img:
    return cover_resize(img)

# responsive fallback gradient background
fallback = Image.new("RGB", (1080, 1920), (18, 24, 45))

# add smooth gradient
pixels = fallback.load()

for y in range(1920):
    r = int(18 + (y / 1920) * 20)
    g = int(24 + (y / 1920) * 35)
    b = int(45 + (y / 1920) * 60)

    for x in range(1080):
        pixels[x, y] = (r, g, b)

return fallback
def create_voice_script(title_si, summary_si):
    openings = [
        "ලෝක පුවත් සිංහලෙන් ඔබ වෙත අද ගෙන එන වැදගත්ම පුවත මෙන්න.",
        "අද ලෝකය පුරා අවධානය දිනාගත් පුවතක් පිළිබඳ විස්තරයි.",
        "මෙය මේ වන විට ජාත්‍යන්තර මාධ්‍යවල වැඩි අවධානයට ලක්ව ඇති පුවතක්.",
        "ලෝකයේ බොහෝ දෙනා කතා කරන නවතම පුවතක් දැන් ඔබට.",
    ]

    middle_lines = [
        "මෙම සිදුවීම පිළිබඳව තවදුරටත් වාර්තා ලැබෙමින් පවතින අතර, එය ඉදිරි දිනවලදී වැඩි බලපෑමක් ඇති කළ හැකිය.",
        "මෙය සාමාන්‍ය ජනතාවට, රජයන්ට, ව්‍යාපාරික ක්ෂේත්‍රයට හෝ දෛනික ජීවිතයට බලපාන වැදගත් කරුණක් විය හැකිය.",
        "මෙම පුවතේ පසුබිම හා ඉදිරි වර්ධනයන් පිළිබඳව ලොව පුරා බොහෝ දෙනා අවධානයෙන් සිටී.",
        "මෙම තත්ත්වය ඉදිරියේදී ආර්ථික, සමාජීය, තාක්ෂණික හෝ ආරක්ෂක පැතිවලටද බලපෑම් කළ හැකිය.",
    ]

    endings = [
        "මෙවැනි තවත් ලෝක පුවත් සිංහලෙන් දැනගැනීමට අපගේ පිටුව follow කරන්න.",
        "නවතම ලෝක පුවත් සඳහා World News in Sinhala සමඟ රැඳී සිටින්න.",
        "වැදගත් පුවත් ඔබට ඉක්මනින් දැනගැනීමට අපගේ පිටුව සමඟ සම්බන්ධව සිටින්න.",
        "මෙම පුවත පිළිබඳ නව තොරතුරු ලැබුණු විට අපි ඔබට යළිත් දැනුම් දෙන්නෙමු.",
    ]

    opening = random.choice(openings)
    middle = random.choice(middle_lines)
    ending = random.choice(endings)

    if summary_si and len(summary_si) > 20:
        detail = summary_si
    else:
        detail = title_si

    script = f"""
{opening}

ප්‍රධාන පුවත වන්නේ,

{title_si}

විස්තර අනුව,

{detail}

{middle}

{ending}
"""

    return script

# ===============================
# LOAD POSTED
# ===============================

if not os.path.exists(POSTED_FILE):
    with open(POSTED_FILE, "w") as f:
        json.dump([], f)

try:
    with open(POSTED_FILE, "r") as f:
        posted = json.load(f)
except Exception:
    posted = []

print("🎬 Sinhala Image Only Reel Bot Started")

# ===============================
# FETCH NEWS
# ===============================

articles = []

for feed in RSS_FEEDS:
    try:
        data = feedparser.parse(feed)

        for entry in data.entries[:15]:
            if hasattr(entry, "link") and entry.link not in posted:
                articles.append(entry)

    except Exception as e:
        print("Feed error:", e)

if not articles:
    print("❌ No new articles")
    exit()

news = random.choice(articles)

title_en = clean_text(news.title)
summary_en = clean_text(getattr(news, "summary", ""))
link = news.link

title_si = safe_translate(title_en)
summary_si = safe_translate(summary_en) if summary_en else ""

# ===============================
# CREATE VOICE
# ===============================

voice_script = create_voice_script(title_si, summary_si)

print("🎙 Voice script:")
print(voice_script)

tts = gTTS(text=voice_script, lang="si")
tts.save(VOICE_FILE)

print("🎙 Voice created")

# ===============================
# CREATE IMAGE BACKGROUND ONLY
# ===============================

article_image_url = get_article_image(news)

img = None

if article_image_url:
    print("🖼 Using article image:", article_image_url)
    img = download_image(article_image_url)

if img:
    img = cover_resize(img)
else:
    print("🖼 No article image. Using fallback image.")
    img = create_fallback_image()

# Slight blur + dark overlay for professional look
img = img.filter(ImageFilter.GaussianBlur(radius=1))

overlay = Image.new("RGB", (1080, 1920), (0, 0, 0))
img = Image.blend(img, overlay, 0.18)

img.save(IMAGE_FILE, "JPEG", quality=95)

print("🖼 Background image created")

# ===============================
# CREATE VIDEO
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
# FACEBOOK REEL UPLOAD
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

caption = f"""
🌍 ලෝක පුවත් සිංහලෙන්

🔥 {title_si}

👉 වැඩි විස්තර:
{link}

#ලෝකපුවත් #සිංහලපුවත් #WorldNews #BreakingNews
"""

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
# CHECK STATUS
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
# SAVE POSTED
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
