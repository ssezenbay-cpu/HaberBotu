import tweepy
import feedparser
import time
import requests
import io
import random
import threading  # <--- SİHİRLİ KELİME BU
from flask import Flask # Render için gerekli
from difflib import SequenceMatcher
from datetime import datetime

# --- ŞİFRELERİNİ BURAYA GİR ---
API_KEY = "4PDFleEiAGaWDhm7vhkMY4A08"
API_SECRET = "sGItq90SLOPmMFX0exkIFQFmA8IvnwsBgRI02LyqTkeCSGrLc7"
ACCESS_TOKEN = "1931002435113234432-8uBBxCmuje2pbtanLYRjeIkyGVNklp"
ACCESS_SECRET = "AL7kAYXPG4wRcX7o5spWdE11mIghLQ9hFcUSLQkSYyrhR"

# Kaynaklar
RSS_KAYNAKLARI = [
    "https://www.ntv.com.tr/son-dakika.rss",
    "https://www.cumhuriyet.com.tr/rss/son-dakika.xml",
    "https://www.gazeteduvar.com.tr/rss",
    "http://feeds.bbci.co.uk/turkce/rss.xml",
    "https://tr.euronews.com/rss",
    "https://www.bloomberght.com/rss",
    "https://tr.investing.com/rss/news.rss",
    "https://www.webtekno.com/rss.xml",
    "https://www.donanimhaber.com/rss/tum/",
    "https://www.ntvspor.net/rss",
]

# --- AKILLI ETİKET SİSTEMİ ---
GENEL_TAGLAR = ["#SonDakika", "#Haber", "#Gündem", "#Türkiye", "#News", "#Breaking"]
KONU_SOZLUGU = {
    "istanbul": "#İstanbul", "ankara": "#Ankara", "izmir": "#İzmir",
    "deprem": "#Deprem", "sarsıntı": "#Deprem", "afad": "#Deprem",
    "dolar": "#Ekonomi", "euro": "#Ekonomi", "altın": "#Ekonomi",
    "borsa": "#Borsa", "bitcoin": "#Kripto", "fenerbahçe": "#FB",
    "galatasaray": "#GS", "beşiktaş": "#BJK", "trabzonspor": "#TS",
    "maç": "#Spor", "futbol": "#Spor", "apple": "#Teknoloji",
    "yapay zeka": "#YapayZeka"
}
EMOJI_POOL = ["🚨", "⚡", "🔴", "🔥", "📢", "💥", "🌍", "🇹🇷"]

# --- FLASK SUNUCUSU (RENDER İÇİN) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT CALISIYOR! 🟢"

# --- YARDIMCI FONKSİYONLAR ---
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

def akilli_etiket_sec(baslik):
    baslik_kucuk = baslik.lower()
    secilenler = []
    for kelime, etiket in KONU_SOZLUGU.items():
        if kelime in baslik_kucuk and etiket not in secilenler:
            secilenler.append(etiket)
    while len(secilenler) < 2:
        rastgele = random.choice(GENEL_TAGLAR)
        if rastgele not in secilenler: secilenler.append(rastgele)
    return " ".join(secilenler[:3])

# --- ANA BOT MOTORU (THREAD OLARAK ÇALIŞACAK) ---
def botu_calistir():
    print("🛡️ GLOBAL ALARM (Threading Modu) Başlatılıyor...")
    paylasilan_basliklar = []
    
    client = None
    api_v1 = None

    # Bağlantı Kur
    try:
        client = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET)
        auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
        api_v1 = tweepy.API(auth)
        me = client.get_me()
        print(f"✅ Twitter Girişi Başarılı: @{me.data.username}")
    except Exception as e:
        print(f"❌ Twitter Giriş Hatası: {e}")

    # ISINMA TURU
    print("💾 Haberler hafızaya alınıyor...")
    for url in RSS_KAYNAKLARI:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                paylasilan_basliklar.append(entry.title)
        except: pass
    print("✅ Hafıza hazır. Nöbet başladı.")

    while True:
        print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Taranıyor...")
        yeni_haber_var_mi = False

        for url in RSS_KAYNAKLARI:
            try:
                feed = feedparser.parse(url)
                if not feed.entries: continue

                for i in range(1):
                    haber = feed.entries[i]
                    baslik = haber.title
                    link = haber.link
                    
                    if baslik in paylasilan_basliklar: continue
                    if any(SequenceMatcher(None, baslik.lower(), eski.lower()).ratio() > 0.65 for eski in paylasilan_basliklar):
                        continue

                    print(f"⚡ YENİ HABER: {baslik}")
                    
                    ozel_etiketler = akilli_etiket_sec(baslik)
                    emoji = random.choice(EMOJI_POOL)
                    tweet_metni = f"{emoji} {baslik}\n\n{ozel_etiketler}"
                    
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
                            print(f"   🐦 TWEET GİTTİ! ID: {tweet_id}")
                            
                            time.sleep(2)
                            client.create_tweet(text=f"🔗 Detaylar:\n{link}", in_reply_to_tweet_id=tweet_id)
                            
                            paylasilan_basliklar.append(baslik)
                            if len(paylasilan_basliklar) > 60: paylasilan_basliklar.pop(0)
                            yeni_haber_var_mi = True
                            
                            time.sleep(300) 
                        except Exception as e:
                            print(f"   Tweet Hatası: {e}")

            except Exception as e:
                continue

        if not yeni_haber_var_mi:
            print("   (Yeni haber yok, bekleniyor...)")
        
        time.sleep(600)

# --- BAŞLATMA MERKEZİ ---
if __name__ == "__main__":
    # 1. Botu arka planda (ayrı kanalda) başlat
    t = threading.Thread(target=botu_calistir)
    t.start()
    
    # 2. Web sunucusunu ana kanalda başlat (Render bunu bekliyor)
    app.run(host='0.0.0.0', port=8080)
