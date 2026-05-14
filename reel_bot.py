import os
import json
import time
import random
import requests
import feedparser
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from googletrans import Translator
from moviepy.editor import ImageClip, AudioFileClip

# ===============================
# FACEBOOK CONFIG
# ===============================

PAGE_ID = "1020689164470492"
PAGE_ACCESS_TOKEN = "EAIFMs5yoDt0BRaZBnr8ZCFXX3AY6swXBZBsP6bcgJlQBr0OAxIQI9rfnT2dx2nVfPaUST5XsFgPdDSYX82BHdFAaPGkBZBqZBdrW43lcF5gpOYZCp74K6n0gh5fgd1U5ewm7FtcNbU9ZAbP6ZAX1X4f5qhNvE1jg6b1KfIZCF5looE0z41sVwo80iNoZAxD5QSkrXHId9IArdpOAUZCoVspdX9GBQjpux7O6YedvyTY6N6wrZApnfw1FZCl5AU2QZD"

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
# LOAD POSTED
# ===============================

if not os.path.exists(POSTED_FILE):
    with open(POSTED_FILE, "w") as f:
        json.dump([], f)

try:
    with open(POSTED_FILE, "r") as f:
        posted = json.load(f)
except:
    posted = []

print("🎬 Sinhala Auto Reel Bot Started")

# ===============================
# GET NEWS
# ===============================

articles = []

for feed in RSS_FEEDS:
    data = feedparser.parse(feed)

    for entry in data.entries[:10]:
        if entry.link not in posted:
            articles.append(entry)

if not articles:
    print("❌ No new articles")
    exit()

news = random.choice(articles)

title_en = news.title
link = news.link

# ===============================
# TRANSLATE
# ===============================

try:
    title_si = translator.translate(title_en, dest="si").text
except:
    title_si = title_en

# ===============================
# SCRIPT + CAPTION
# ===============================

script = f"""
ලෝක පුවත් සිංහලෙන්.

අද ප්‍රධාන පුවත.

{title_si}

මෙම පුවත ලෝකයේ බොහෝ දෙනාගේ අවධානයට ලක් වී තිබේ.

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
# CREATE VOICE
# ===============================

tts = gTTS(text=script, lang="si")
tts.save(VOICE_FILE)

print("🎙 Voice created")

# ===============================
# CREATE IMAGE
# ===============================

img_url = f"https://picsum.photos/1080/1920?random={random.randint(1,999999)}"
img_data = requests.get(img_url, timeout=20).content

img = Image.open(BytesIO(img_data)).convert("RGB").resize((1080, 1920))

overlay = Image.new("RGB", (1080, 1920), (0, 0, 0))
img = Image.blend(img, overlay, 0.50)

draw = ImageDraw.Draw(img)

try:
    font_big = ImageFont.truetype("DejaVuSans.ttf", 60)
    font_small = ImageFont.truetype("DejaVuSans.ttf", 46)
except:
    font_big = ImageFont.load_default()
    font_small = ImageFont.load_default()

def wrap_text(text, max_chars=24):
    words = text.split()
    lines = []
    line = ""

    for word in words:
        if len(line + " " + word) <= max_chars:
            line += " " + word
        else:
            lines.append(line.strip())
            line = word

    if line:
        lines.append(line.strip())

    return "\n".join(lines)

draw.text((70, 160), "🌍 ලෝක පුවත් සිංහලෙන්", fill="white", font=font_big)
draw.text((70, 420), wrap_text(title_si), fill="white", font=font_small)
draw.text((70, 1600), "Follow කරන්න • World News in Sinhala", fill="white", font=font_small)

img.save(IMAGE_FILE, "JPEG", quality=95)

print("🖼 Image created")

# ===============================
# CREATE VIDEO
# ===============================

audio = AudioFileClip(VOICE_FILE)

clip = ImageClip(IMAGE_FILE).set_duration(audio.duration)
clip = clip.set_audio(audio)

clip.write_videofile(
    VIDEO_FILE,
    fps=24,
    codec="libx264",
    audio_codec="aac"
)

print("✅ Video created")

# ===============================
# FACEBOOK REELS UPLOAD — START
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
    print("❌ Failed to start Reel upload")
    exit()

video_id = start_json["video_id"]
upload_url = start_json["upload_url"]

# ===============================
# UPLOAD VIDEO FILE
# ===============================

file_size = os.path.getsize(VIDEO_FILE)

with open(VIDEO_FILE, "rb") as video_file:
    upload_headers = {
        "Authorization": f"OAuth {PAGE_ACCESS_TOKEN}",
        "offset": "0",
        "file_size": str(file_size),
    }

    upload_res = requests.post(
        upload_url,
        headers=upload_headers,
        data=video_file
    )

print("UPLOAD:", upload_res.text)

# ===============================
# FINISH + PUBLISH REEL
# ===============================

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
# CHECK REEL STATUS
# ===============================

print("⏳ Checking Reel processing status...")

ready = False

for i in range(12):
    time.sleep(10)

    status_url = f"https://graph.facebook.com/v23.0/{video_id}"

    status_params = {
        "fields": "status,permalink_url",
        "access_token": PAGE_ACCESS_TOKEN
    }

    status_res = requests.get(status_url, params=status_params)
    status_json = status_res.json()

    print("STATUS:", status_json)

    if "status" in status_json:
        status = status_json["status"]

        if isinstance(status, dict):
            video_status = status.get("video_status")

            if video_status == "ready":
                print("✅ REEL READY")
                ready = True
                break

            if video_status == "error":
                print("❌ REEL PROCESSING ERROR")
                break

# ===============================
# SAVE POSTED
# ===============================

if finish_res.status_code == 200 and finish_json.get("success") == True:
    print("✅ REEL UPLOAD ACCEPTED BY FACEBOOK")

    posted.append(link)

    with open(POSTED_FILE, "w") as f:
        json.dump(posted, f)

    if ready:
        print("✅ REEL SHOULD NOW APPEAR ON PAGE")
    else:
        print("⚠️ REEL ACCEPTED BUT STILL PROCESSING")
else:
    print("❌ REEL POST FAILED")
