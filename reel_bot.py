import feedparser
import random
import requests
import textwrap
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from googletrans import Translator
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip

OUTPUT_IMAGE = "reel_bg.jpg"
VOICE_FILE = "voice.mp3"
OUTPUT_VIDEO = "sinhala_reel.mp4"

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://feeds.bbci.co.uk/news/health/rss.xml",
]

translator = Translator()

print("🎬 Sinhala Reel Bot Started")

articles = []

for feed in RSS_FEEDS:
    data = feedparser.parse(feed)
    for entry in data.entries[:10]:
        articles.append(entry)

if not articles:
    print("❌ No news found")
    exit()

news = random.choice(articles)

title_en = news.title

try:
    title_si = translator.translate(title_en, dest="si").text
except Exception:
    title_si = title_en

script = f"""
ලෝක පුවත් සිංහලෙන්.

අද ප්‍රධාන පුවත.

{title_si}

මෙම පුවත ලෝකයේ බොහෝ දෙනාගේ අවධානයට ලක් වී තිබේ.

වැඩි විස්තර සඳහා අපගේ පිටුව follow කරන්න.
"""

tts = gTTS(text=script, lang="si")
tts.save(VOICE_FILE)

img_url = f"https://picsum.photos/1080/1920?random={random.randint(1,999999)}"
img_data = requests.get(img_url, timeout=20).content

img = Image.open(BytesIO(img_data)).convert("RGB")
img = img.resize((1080, 1920))

overlay = Image.new("RGB", (1080, 1920), (0, 0, 0))
img = Image.blend(img, overlay, 0.50)

draw = ImageDraw.Draw(img)

try:
    font_title = ImageFont.truetype("DejaVuSans.ttf", 58)
    font_body = ImageFont.truetype("DejaVuSans.ttf", 48)
except:
    font_title = ImageFont.load_default()
    font_body = ImageFont.load_default()

header = "🌍 ලෝක පුවත් සිංහලෙන්"
wrapped_title = textwrap.fill(title_si, width=24)

draw.text((80, 160), header, fill="white", font=font_title)
draw.text((80, 430), wrapped_title, fill="white", font=font_body)
draw.text((80, 1600), "Follow කරන්න • World News in Sinhala", fill="white", font=font_body)

img.save(OUTPUT_IMAGE)

audio = AudioFileClip(VOICE_FILE)
clip = ImageClip(OUTPUT_IMAGE).set_duration(audio.duration)
clip = clip.set_audio(audio)

clip.write_videofile(
    OUTPUT_VIDEO,
    fps=24,
    codec="libx264",
    audio_codec="aac"
)

print("✅ Reel created:", OUTPUT_VIDEO)
