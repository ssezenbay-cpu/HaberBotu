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

# --- KAYNAKLAR VE KATEGORİLERİ (Euronews Dahil) ---
# Her linkin yanına o kaynağın kategorisini belirttik.
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

# --- GELİŞMİŞ ETİKET SİSTEMİ (V10.5) ---
GENEL_TAGLAR = ["#SonDakika", "#Haber", "#Gündem", "#Türkiye", "#News", "#Breaking"]

KONU_SOZLUGU = {
    # Siyaset & Ankara
    "cumhurbaşkanı": "#Cumhurbaşkanı", "erdoğan": "#RTE", "beştepe": "#Cumhurbaşkanlığı",
    "kabine": "#Kabine", "bakan": "#Bakanlık", "meclis": "#TBMM", "genel kurul": "#TBMM",
    "chp": "#CHP", "özgür özel": "#ÖzgürÖzel", "ak parti": "#AKParti", "akp": "#AKParti",
    "mhp": "#MHP", "bahçeli": "#DevletBahçeli", "iyi parti": "#İYİParti", "dem parti": "#DEM",
    "imamoğlu": "#İmamoğlu", "ibb": "#İstanbul", "yavaş": "#MansurYavaş", "abb": "#Ankara",
    "seçim": "#Seçim", "sandık": "#Seçim", "kayyum": "#Kayyum", "anayasa": "#Anayasa",
    "yargıtay": "#Yargı", "danıştay": "#Yargı", "savcı": "#Adliye", "mahkeme": "#Hukuk",

    # Ekonomi & Piyasalar
    "dolar": "#Dolar", "euro": "#Euro", "döviz": "#Ekonomi", "kur": "#Piyasa",
    "altın": "#Altın", "gram altın": "#Altın", "çeyrek": "#Altın",
    "borsa": "#Bist100", "bist": "#Borsa", "hisse": "#Borsa", "spk": "#SPK",
    "faiz": "#MerkezBankası", "tcmb": "#MerkezBankası", "ppk": "#FaizKararı",
    "enflasyon": "#Enflasyon", "tüik": "#Ekonomi", "zam": "#Ekonomi",
    "asgari ücret": "#AsgariÜcret", "emekli": "#Emekli", "memur": "#Memur",
    "bitcoin": "#Bitcoin", "btc": "#Kripto", "ethereum": "#ETH", "kripto": "#Kripto",
    "fed": "#FED", "petrol": "#Petrol", "brent": "#Petrol", "ihracat": "#İhracat",

    # Dünya & Jeopolitik
    "abd": "#ABD", "amerika": "#ABD", "trump": "#Trump", "biden": "#Biden",
    "rusya": "#Rusya", "putin": "#Putin", "ukrayna": "#Ukrayna", "zelenski": "#Ukrayna",
    "israil": "#İsrail", "filistin": "#Filistin", "gazze": "#Gazze", "hamas": "#Hamas",
    "iran": "#İran", "suriye": "#Suriye", "yunanistan": "#Yunanistan",
    "çin": "#Çin", "almanya": "#Almanya", "fransa": "#Fransa", "ingiltere": "#İngiltere",
    "ab": "#AB", "avrupa birliği": "#AB", "nato": "#NATO", "bm": "#BM",
    "azerbaycan": "#Azerbaycan", "karabağ": "#Karabağ",

    # Teknoloji & Bilim
    "yapay zeka": "#YapayZeka", "ai": "#AI", "chatgpt": "#YapayZeka",
    "apple": "#Apple", "iphone": "#iPhone", "ios": "#Teknoloji",
    "samsung": "#Samsung", "galaxy": "#Samsung", "android": "#Android",
    "huawei": "#Huawei", "xiaomi": "#Xiaomi", "google": "#Google",
    "elon musk": "#ElonMusk", "twitter": "#X", "instagram": "#Instagram", "whatsapp": "#WhatsApp",
    "uzay": "#Uzay", "nasa": "#NASA", "spacex": "#SpaceX", "tua": "#MilliUzayProgramı",
    "siber": "#SiberGüvenlik", "hacker": "#SiberGüvenlik", "yerli otomobil": "#Togg", "togg": "#Togg",

    # Spor
    "futbol": "#Futbol", "süper lig": "#SüperLig", "tff": "#Tff",
    "galatasaray": "#Galatasaray", "cimbom": "#GS",
    "fenerbahçe": "#Fenerbahçe", "kanarya": "#FB",
    "beşiktaş": "#Beşiktaş", "kartal": "#BJK",
    "trabzonspor": "#Trabzonspor", "fırtına": "#TS",
    "milli takım": "#BizimÇocuklar", "basketbol": "#Basketbol", "voleybol": "#FileninSultanları",

    # Günlük Yaşam
    "deprem": "#Deprem", "kandilli": "#Deprem", "afad": "#Deprem",
    "hava durumu": "#HavaDurumu", "kar": "#Meteoroloji", "yağmur": "#Meteoroloji",
    "kaza": "#SonDakika", "yangın": "#SonDakika", "polis": "#Asayiş",
    "istanbul": "#İstanbul", "ankara": "#Ankara", "izmir": "#İzmir",
    "üniversite": "#Eğitim", "meb": "#MEB", "okul": "#Eğitim", "sınav": "#ÖSYM"
}

EMOJI_POOL = ["🚨", "⚡", "🔴", "🔥", "📢", "🏛️", "🌍", "🇹🇷", "📡"]

# --- RENDER İÇİN WEB SUNUCUSU ---
app = Flask(__name__)

@app.route('/')
def home():
    return "SENTINEL HABER AJANSI AKTIF (V11.0)"

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

def etiketleri_belirle(baslik, kategori):
    baslik_kucuk = baslik.lower()
    etiketler = []

    # 1. Kategori Bazlı Zorunlu Etiketler
    if kategori == "siyaset":
        etiketler.append("#Siyaset")
    elif kategori == "teknoloji":
        etiketler.append("#Teknoloji")
    elif kategori == "dunya":
        etiketler.append("#Dünya")
    else:
        etiketler.append("#SonDakika")

    # 2. Kelime Bazlı Etiketler
    for kelime, etiket in KONU_SOZLUGU.items():
        if kelime in baslik_kucuk and etiket not in etiketler:
            etiketler.append(etiket)
            
    # 3. Eksik Kalırsa Tamamla
    while len(etiketler) < 3:
        secilen = random.choice(GENEL_TAGLAR)
        if secilen not in etiketler:
            etiketler.append(secilen)

    return " ".join(etiketler[:4])

# --- ANA BOT MOTORU ---
def botu_calistir():
    log_yaz("🛡️ SENTINEL (V11.0 - Final Sürüm) Başlatılıyor...")
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
    for url, kat in RSS_VE_KATEGORI:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                paylasilan_basliklar.append(entry.title)
        except: pass
    log_yaz("✅ Hafıza hazır. Nöbet başladı.")

    # 3. Sonsuz Döngü
    while True:
        try:
            log_yaz(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Taranıyor...")
            yeni_haber_var_mi = False
            
            # Listeyi karıştırarak tara (Hep aynı sırayla gitmesin)
            random.shuffle(RSS_VE_KATEGORI)

            for url, kategori in RSS_VE_KATEGORI:
                feed = feedparser.parse(url)
                if not feed.entries: continue

                # Sadece en tepedeki 1 habere bak
                for i in range(1):
                    haber = feed.entries[i]
                    baslik = haber.title
                    link = haber.link
                    
                    if baslik in paylasilan_basliklar: continue
                    if any(SequenceMatcher(None, baslik.lower(), eski.lower()).ratio() > 0.65 for eski in paylasilan_basliklar):
                        continue

                    log_yaz(f"⚡ YENİ HABER ({kategori}): {baslik}")
                    
                    ozel_etiketler = etiketleri_belirle(baslik, kategori)
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

                    # TWEET ATMA (Hata Korumalı)
                    basari = False
                    deneme_sayisi = 0
                    
                    if client:
                        while not basari and deneme_sayisi < 3:
                            try:
                                if media_id:
                                    resp = client.create_tweet(text=tweet_metni, media_ids=[media_id])
                                else:
                                    resp = client.create_tweet(text=tweet_metni)

                                tweet_id = resp.data['id']
                                log_yaz(f"   🐦 TWEET GİTTİ! ID: {tweet_id}")
                                
                                time.sleep(2)
                                client.create_tweet(text=f"🔗 Detaylar:\n{link}", in_reply_to_tweet_id=tweet_id)
                                
                                basari = True
                                yeni_haber_var_mi = True
                                paylasilan_basliklar.append(baslik)
                                if len(paylasilan_basliklar) > 60: paylasilan_basliklar.pop(0)

                            except tweepy.errors.TooManyRequests:
                                log_yaz("   ❌ 429 HIZ SINIRI! 2 SAAT Uyku...")
                                basari = True
                                time.sleep(7200)
                            except Exception as e:
                                deneme_sayisi += 1
                                log_yaz(f"   ⚠️ Hata ({deneme_sayisi}/3): {e}. Bekleniyor...")
                                time.sleep(30)

                    # Tweet gittiyse 1 SAAT bekle
                    if yeni_haber_var_mi:
                        log_yaz("   🛑 HIZ KORUMASI: 1 SAAT bekleniyor...")
                        time.sleep(3600)
                        break 

                if yeni_haber_var_mi: break

            if not yeni_haber_var_mi:
                log_yaz("   (Yeni haber yok, bekleniyor...)")
                time.sleep(600) # 10 Dakika ara

        except Exception as gen_e:
            log_yaz(f"Döngü Hatası: {gen_e}")
            time.sleep(60)

if __name__ == "__main__":
    t = threading.Thread(target=botu_calistir)
    t.start()
    app.run(host='0.0.0.0', port=8080)
