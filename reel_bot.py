import os
import json
import random
import requests
import feedparser
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from googletrans import Translator
from moviepy.editor import ImageClip, AudioFileClip

PAGE_ID = "1020689164470492"
PAGE_ACCESS_TOKEN = "EAIFMs5yoDt0BRaZBnr8ZCFXX3AY6swXBZBsP6bcgJlQBr0OAxIQI9rfnT2dx2nVfPaUST5XsFgPdDSYX82BHdFAaPGkBZBqZBdrW43lcF5gpOYZCp74K6n0gh5fgd1U5ewm7FtcNbU9ZAbP6ZAX1X4f5qhNvE1jg6b1KfIZCF5looE0z41sVwo80iNoZAxD5QSkrXHId9IArdpOAUZCoVspdX9GBQjpux7O6YedvyTY6N6wrZApnfw1FZCl5AU2QZD"

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

if not os.path.exists(POSTED_FILE):
    json.dump([], open(POSTED_FILE, "w"))

try:
    posted = json.load(open(POSTED_FILE))
except:
    posted = []

translator = Translator()

print("🎬 Sinhala Auto Reel Bot Started")

articles = []

for feed in RSS_FEEDS:
    data = feedparser.parse(feed)
    for entry in data.entries[:10]:
        if entry.link not in posted:
            articles.append(entry)

if not articles:
    print("No new articles")
    exit()

news = random.choice(articles)
title_en = news.title
link = news.link

try:
    title_si = translator.translate(title_en, dest="si").text
except:
    title_si = title_en

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

tts = gTTS(text=script, lang="si")
tts.save(VOICE_FILE)

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

audio = AudioFileClip(VOICE_FILE)
clip = ImageClip(IMAGE_FILE).set_duration(audio.duration).set_audio(audio)

clip.write_videofile(
    VIDEO_FILE,
    fps=24,
    codec="libx264",
    audio_codec="aac"
)

print("✅ Video created")

# ===============================
# FACEBOOK REELS AUTO UPLOAD
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

with open(VIDEO_FILE, "rb") as video_file:
    upload_headers = {
        "Authorization": f"OAuth {PAGE_ACCESS_TOKEN}",
        "offset": "0",
        "file_size": str(os.path.getsize(VIDEO_FILE)),
    }

    upload_res = requests.post(upload_url, headers=upload_headers, data=video_file)

print("UPLOAD:", upload_res.text)

finish_data = {
    "upload_phase": "finish",
    "video_id": video_id,
    "description": caption,
    "access_token": PAGE_ACCESS_TOKEN
}

finish_res = requests.post(start_url, data=finish_data)
finish_json = finish_res.json()

print("FINISH:", finish_json)

if finish_res.status_code == 200 and ("success" in finish_json or "post_id" in finish_json or "id" in finish_json):
    print("✅ REEL POSTED SUCCESSFULLY")
    posted.append(link)
    json.dump(posted, open(POSTED_FILE, "w"))
else:
    print("❌ REEL POST FAILED")
