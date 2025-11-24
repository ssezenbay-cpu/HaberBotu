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

# --- ŞİFRELERİNİ BURAYA GİR (Tırnakların içine) ---
API_KEY = "Nu1x3YBFqmvfeW0q6h1djklvY"
API_SECRET = "jA7vwzubDvhk70i7q9CdH7l7CpRYmlj2xhaOb9awsPW7zudsDu"
ACCESS_TOKEN = "1992901155874324481-E1Cuznb26jDe2JN7owzdqsagimfUT9"
ACCESS_SECRET = "f4tQxRjiFWAQcKEU4Runrw4q0LkRIlaL4o1fR455fty5A"

# --- SENTINEL ÖZEL KAYNAK LİSTESİ (Siyaset, Gündem & Teknoloji) ---
RSS_KAYNAKLARI = [
    # 1. SİYASET VE ANKARA GÜNDEMİ (Ağır Toplar)
    "https://www.haberturk.com/rss/siyaset.xml",   # Sadece siyaset
    "https://t24.com.tr/rss",                      # Derinlikli haber
    "https://www.trthaber.com/sondakika.rss",      # Resmi açıklamalar
    
    # 2. GENEL SON DAKİKA (Güvenilir Ajanslar)
    "https://www.ntv.com.tr/son-dakika.rss",
    "https://www.gazeteduvar.com.tr/rss",
    "http://feeds.bbci.co.uk/turkce/rss.xml",
    
    # 3. TEKNOLOJİ & GELECEK (Marka Kimliği İçin)
    "https://www.webtekno.com/rss.xml",
]

# --- AKILLI ETİKET SİSTEMİ ---
GENEL_TAGLAR = ["#SonDakika", "#Haber", "#Gündem", "#Türkiye", "#Siyaset"]
KONU_SOZLUGU = {
    # Siyaset & Gündem
    "cumhurbaşkanı": "#Cumhurbaşkanı", "erdoğan": "#RTE", "bakan": "#Bakanlık",
    "meclis": "#TBMM", "chp": "#CHP", "ak parti": "#AKParti", "mhp": "#MHP",
    "iyi parti": "#İYİParti", "dem parti": "#DEM", "özgür özel": "#ÖzgürÖzel",
    "imamoğlu": "#İmamoğlu", "yavaş": "#MansurYavaş", "seçim": "#Seçim",
    "ankara": "#Ankara", "istanbul": "#İstanbul", "izmir": "#İzmir",
    
    # Ekonomi & Dünya
    "dolar": "#Ekonomi", "euro": "#Ekonomi", "altın": "#Altın", "borsa": "#Bist100",
    "enflasyon": "#Ekonomi", "faiz": "#MerkezBankası",
    "abd": "#ABD", "rusya": "#Rusya", "ukrayna": "#Ukrayna", "gazze": "#Gazze",
    
    # Teknoloji
    "yapay zeka": "#YapayZeka", "apple": "#Teknoloji", "samsung": "#Teknoloji",
    "elon musk": "#Teknoloji", "uzay": "#Uzay", "bilim": "#Bilim"
}
EMOJI_POOL = ["🚨", "⚡", "🔴", "🔥", "📢", "🏛️", "🌍", "🇹🇷", "📡"]

# --- RENDER İÇİN WEB SUNUCUSU ---
app = Flask(__name__)

@app.route('/')
def home():
    return "SENTINEL HABER AJANSI AKTİF (V8.0)"

# --- YARDIMCI FONKSİYONLAR ---
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

# --- ANA BOT MOTORU ---
def botu_calistir():
    log_yaz("🛡️ SENTINEL (V8.0 - Siyaset & Teknoloji) Başlatılıyor...")
    paylasilan_basliklar = []
    client = None
    api_v1 = None

    # 1. Twitter Bağlantısı
    try:
        client = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_SECRET, access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET)
        auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
        api_v1 = tweepy.API(auth)
        me = client.get_me()
        log_yaz(f"✅ Twitter Girişi Başarılı: @{me.data.username}")
    except Exception as e:
        log_yaz(f"❌ Giriş Hatası: {e}")

    # 2. Isınma Turu
    log_yaz("💾 Mevcut haberler hafızaya alınıyor...")
    for url in RSS_KAYNAKLARI:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: 
                paylasilan_basliklar.append(entry.title)
        except: pass
    log_yaz(f"✅ Hafıza hazır ({len(paylasilan_basliklar)} haber). Nöbet başladı.")

    # 3. Sonsuz Döngü
    while True:
        try:
            log_yaz(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Ankara ve Dünya Taranıyor...")
            yeni_haber_var_mi = False

            for url in RSS_KAYNAKLARI:
                feed = feedparser.parse(url)
                if not feed.entries: continue

                # Sadece en yeni habere bak
                for i in range(1):
                    haber = feed.entries[i]
                    baslik = haber.title
                    link = haber.link
                    
                    if baslik in paylasilan_basliklar: continue
                    if any(SequenceMatcher(None, baslik.lower(), eski.lower()).ratio() > 0.65 for eski in paylasilan_basliklar):
                        continue

                    log_yaz(f"⚡ YENİ GELİŞME: {baslik}")
                    
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
                            log_yaz(f"   🐦 TWEET BAŞARIYLA GÖNDERİLDİ! ID: {tweet_id}")
                            
                            time.sleep(2)
                            client.create_tweet(text=f"🔗 Detaylar:\n{link}", in_reply_to_tweet_id=tweet_id)
                            
                            paylasilan_basliklar.append(baslik)
                            if len(paylasilan_basliklar) > 60: paylasilan_basliklar.pop(0)
                            yeni_haber_var_mi = True
                            
                            # YENİ HESAP KORUMASI: Tweet sonrası 15 dakika bekle
                            log_yaz("   ⏳ Güvenlik beklemesi: 15 dakika mola...")
                            time.sleep(900) 

                        except tweepy.errors.TooManyRequests:
                            log_yaz("   ❌ 429 HIZ SINIRI! Bot 30 dakika zorunlu uykuya geçiyor...")
                            time.sleep(1800)
                        except Exception as e:
                            log_yaz(f"   Tweet Hatası: {e}")

            if not yeni_haber_var_mi:
                log_yaz("   (Yeni haber yok, bekleniyor...)")
            
            time.sleep(600) # 10 Dakika ara ver

        except Exception as gen_e:
            log_yaz(f"Genel Döngü Hatası: {gen_e}")
            time.sleep(60)

if __name__ == "__main__":
    t = threading.Thread(target=botu_calistir)
    t.start()
    app.run(host='0.0.0.0', port=8080)
