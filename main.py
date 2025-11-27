import tweepy
import feedparser
import time
import requests
import io
import random
import threading
import sys
from flask import Flask
from difflib import SequenceMatcher
from datetime import datetime

# --- ŞİFRELERİNİ BURAYA GİR ---
API_KEY = "Nu1x3YBFqmvfeW0q6h1djklvY"
API_SECRET = "jA7vwzubDvhk70i7q9CdH7l7CpRYmlj2xhaOb9awsPW7zudsDu"
ACCESS_TOKEN = "1992901155874324481-E1Cuznb26jDe2JN7owzdqsagimfUT9"
ACCESS_SECRET = "f4tQxRjiFWAQcKEU4Runrw4q0LkRIlaL4o1fR455fty5A"

# --- KAYNAKLAR ---
RSS_VE_KATEGORI = [
    ("https://www.haberturk.com/rss/siyaset.xml", "siyaset"),
    ("https://t24.com.tr/rss", "genel"),
    ("https://www.trthaber.com/sondakika.rss", "siyaset"),
    ("https://www.ntv.com.tr/son-dakika.rss", "genel"),
    ("https://www.gazeteduvar.com.tr/rss", "genel"),
    ("http://feeds.bbci.co.uk/turkce/rss.xml", "genel"),
    ("https://tr.euronews.com/rss", "dunya"),
    ("https://www.webtekno.com/rss.xml", "teknoloji"),
    ("https://www.donanimhaber.com/rss/tum/", "teknoloji")
]

# --- ETİKETLER ---
GENEL_TAGLAR = ["#SonDakika", "#Haber", "#Gündem", "#Türkiye", "#News"]
KONU_SOZLUGU = {
    "cumhurbaşkanı": "#Cumhurbaşkanı", "erdoğan": "#RTE", "bakan": "#Bakanlık",
    "meclis": "#TBMM", "chp": "#CHP", "ak parti": "#AKParti", "mhp": "#MHP",
    "iyi parti": "#İYİParti", "dem parti": "#DEM", "özgür özel": "#ÖzgürÖzel",
    "imamoğlu": "#İmamoğlu", "yavaş": "#MansurYavaş", "seçim": "#Seçim",
    "ankara": "#Ankara", "istanbul": "#İstanbul", "izmir": "#İzmir",
    "dolar": "#Ekonomi", "euro": "#Ekonomi", "altın": "#Altın", "borsa": "#Bist100",
    "abd": "#ABD", "rusya": "#Rusya", "ukrayna": "#Ukrayna", "gazze": "#Gazze",
    "avrupa": "#Avrupa", "yapay zeka": "#YapayZeka", "apple": "#Teknoloji"
}
EMOJI_POOL = ["🚨", "⚡", "🔴", "🔥", "📢", "🏛️", "🌍", "🇹🇷", "📡"]

app = Flask(__name__)

@app.route('/')
def home():
    return "SENTINEL V12.1 (LINKLI MOD) AKTIF"

def log_yaz(mesaj):
    print(mesaj, flush=True)
    sys.stdout.flush()

def gorsel_linkini_bul(entry):
    if hasattr(entry, 'media_thumbnail') and len(entry.media_thumbnail) > 0:
        return entry.media_thumbnail[0]['url']
    if hasattr(entry, 'enclosures') and len(entry.enclosures) > 0:
        for enclosure in entry.enclosures:
            if enclosure.type.startswith('image/'):
                return enclosure.href
    if hasattr(entry, 'links'):
        for link in entry.links:
            if link.type.startswith('image/'):
                return link.href
    return None

def etiketleri_belirle(baslik, kategori):
    baslik_kucuk = baslik.lower()
    etiketler = []
    if kategori == "siyaset": etiketler.append("#Siyaset")
    elif kategori == "teknoloji": etiketler.append("#Teknoloji")
    elif kategori == "dunya": etiketler.append("#Dünya")
    else: etiketler.append("#SonDakika")
    
    for kelime, etiket in KONU_SOZLUGU.items():
        if kelime in baslik_kucuk and etiket not in etiketler:
            etiketler.append(etiket)
            
    while len(etiketler) < 3:
        secilen = random.choice(GENEL_TAGLAR)
        if secilen not in etiketler: etiketler.append(secilen)
    return " ".join(etiketler[:4])

def botu_calistir():
    log_yaz("🛡️ SENTINEL (V12.1 - Linkli Tek Atış) Başlatılıyor...")
    paylasilan_basliklar = []
    client = None
    api_v1 = None

    try:
        client = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET)
        auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
        api_v1 = tweepy.API(auth)
        me = client.get_me()
        log_yaz(f"✅ Twitter Girişi Başarılı: @{me.data.username}")
    except Exception as e:
        log_yaz(f"❌ Giriş Hatası: {e}")

    log_yaz("💾 Mevcut haberler hafızaya alınıyor...")
    for url, kat in RSS_VE_KATEGORI:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                paylasilan_basliklar.append(entry.title)
        except: pass
    log_yaz("✅ Hafıza hazır. Nöbet başladı.")

    while True:
        try:
            log_yaz(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Taranıyor...")
            yeni_haber_var_mi = False
            random.shuffle(RSS_VE_KATEGORI)

            for url, kategori in RSS_VE_KATEGORI:
                feed = feedparser.parse(url)
                if not feed.entries: continue

                for i in range(1):
                    haber = feed.entries[i]
                    baslik = haber.title
                    link = haber.link
                    
                    if baslik in paylasilan_basliklar: continue
                    if any(SequenceMatcher(None, baslik.lower(), eski.lower()).ratio() > 0.65 for eski in paylasilan_basliklar):
                        continue

                    log_yaz(f"⚡ YENİ HABER: {baslik}")
                    
                    ozel_etiketler = etiketleri_belirle(baslik, kategori)
                    emoji = random.choice(EMOJI_POOL)
                    
                    # --- DEĞİŞİKLİK BURADA: LİNKİ METNE EKLEDİK ---
                    tweet_metni = f"{emoji} {baslik}\n\n{ozel_etiketler}\n\n🔗 {link}"
                    
                    media_id = None
                    img_url = gorsel_linkini_bul(haber)
                    
                    if img_url and api_v1:
                        try:
                            r = requests.get(img_url, timeout=10)
                            file = io.BytesIO(r.content)
                            media = api_v1.media_upload(filename="haber.jpg", file=file)
                            media_id = media.media_id
                        except: pass

                    if client:
                        try:
                            if media_id:
                                resp = client.create_tweet(text=tweet_metni, media_ids=[media_id])
                            else:
                                resp = client.create_tweet(text=tweet_metni)

                            tweet_id = resp.data['id']
                            log_yaz(f"   🐦 TWEET GİTTİ! ID: {tweet_id}")
                            
                            paylasilan_basliklar.append(baslik)
                            if len(paylasilan_basliklar) > 60: paylasilan_basliklar.pop(0)
                            yeni_haber_var_mi = True
                            
                            # 1 SAAT BEKLEME (GÜVENLİK İÇİN ŞART)
                            log_yaz("   🛑 HIZ KORUMASI: 1 SAAT bekleniyor...")
                            time.sleep(3600)
                            break 

                        except tweepy.errors.TooManyRequests:
                            log_yaz("   ❌ 429 HIZ SINIRI! 2 SAAT Uyku...")
                            time.sleep(7200)
                        except Exception as e:
                            log_yaz(f"   Tweet Hatası: {e}")

                if yeni_haber_var_mi: break

            if not yeni_haber_var_mi:
                log_yaz("   (Yeni haber yok, bekleniyor...)")
                time.sleep(600)

        except Exception as gen_e:
            log_yaz(f"Döngü Hatası: {gen_e}")
            time.sleep(60)

if __name__ == "__main__":
    t = threading.Thread(target=botu_calistir)
    t.start()
    app.run(host='0.0.0.0', port=8080)
