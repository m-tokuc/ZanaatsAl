from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import base64
import logging
from dotenv import load_dotenv
from orchestrator_service import ZanaatsAlOrchestrator
from api_contract import APIResponse, ENDPOINT_DOCS
from studio_service import StudioAIService

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="ZanaatsAl API",
    description="Yerel üreticilerin ürünlerini küresel pazarlara taşıyan Agentic e-ticaret asistanı",
    version="0.1.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
try:
    orchestrator = ZanaatsAlOrchestrator()
    print("[OK] ZanaatsAl Orkestrator basariyla yuklendi")
except Exception as e:
    print(f"[ERROR] Orkestrator yuklenemedi: {str(e)}")
    orchestrator = None

# Initialize Studio AI Service
try:
    studio_service = StudioAIService()
    print("[OK] Studio AI Servisi basariyla yuklendi")
except Exception as e:
    print(f"[ERROR] Studio AI Servisi yuklenemedi: {str(e)}")
    studio_service = None

@app.get("/")
async def root():
    """API ana sayfası"""
    return { 'status': 'ZanaatsAl API Aktif', 'version': '1.0' }

@app.get("/health")
async def health_check():
    """API servislerinin durumunu kontrol eder"""
    try:
        health_data = APIResponse.health_check()
        return JSONResponse(status_code=200, content=health_data.dict())
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/analyze")
async def analyze_product(
    file: UploadFile = File(...),
    mock: Optional[str] = None,
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    material: Optional[str] = Form(None)
):
    """
    Ürün görselini analiz eder ve tam e-ihracat stratejisi üretir
    
    Flow:
    1. Vision analizi (Gemini 2.5 Flash)
    2. Pazar araştırması (Serper.dev - Etsy/Amazon)
    3. Strateji üretimi (E-İhracat Danışmanı)
    4. JSON formatında tam rapor
    
    Error Handling:
    - Vision hatası → Genel strateji ile devam
    - Pazar verisi yok → Vision verisiyle strateji
    - API hatası → Detaylı hata mesajı
    """
    # Mock Kontrolü (Sunum sırasında internet/API çökmesine karşı)
    if mock and mock.lower() == 'true':
        logger.info(f"Returning dynamic mock response for: {category}, {material}")
        user_category = category if category else "Ürün"
        user_material = material if material else "Özel Malzeme"
        user_desc = description if description else "Kaliteli ve şık bir tasarım."
        
        # Gelişmiş Dinamik ve Akıllı Fiyatlandırma Motoru (Zanaatkar AI Fiyatlandırma Simülatörü v2.0)
        base_prices = {
            'Çanta & Cüzdan': (1500, 55),
            'Giyim & Moda': (1000, 38),
            'Ayakkabı': (2000, 75),
            'Takı & Aksesuar': (600, 22),
            'Teknoloji Aksesuarları (iPad Kılıfı vb.)': (900, 32),
            'Ev & Yaşam': (1100, 40),
            'Dekorasyon & Sanat': (1600, 60),
            'Mutfak Gereçleri': (550, 20),
            'Kozmetik & Kişisel Bakım': (450, 16),
            'Hobi & Oyuncak': (500, 18),
            'Diğer': (700, 25)
        }
        
        cat_key = category if category else 'Diğer'
        base_tl, base_usd = base_prices.get(cat_key, (700, 25))
        
        # 1) Zenginleştirilmiş Materyal, Teknik ve Zanaat Duyarlılık Çarpanları
        multiplier = 1.0
        text_to_search = f"{user_material} {user_desc} {cat_key}".lower()
        
        # [Kategori A: Ultra Lüks Metallar & Değerli Taşlar]
        if any(w in text_to_search for w in ["pırlanta", "diamond", "elmas"]):
            multiplier *= 7.0
        elif any(w in text_to_search for w in ["altın", "gold", "yakut", "safir", "zümrüt", "emerald", "ruby", "sapphire", "platin", "platinum"]):
            multiplier *= 5.8
        elif any(w in text_to_search for w in ["gümüş", "silver", "inci", "pearl", "kehribar", "amber"]):
            multiplier *= 2.3
        elif any(w in text_to_search for w in ["bronz", "bronze", "pirinç", "brass"]):
            multiplier *= 1.25
            
        # [Kategori B: Premium Kumaşlar & Doğal Malzemeler]
        if any(w in text_to_search for w in ["kaşmir", "cashmere", "ipek", "silk"]):
            multiplier *= 2.5
        elif any(w in text_to_search for w in ["deri", "leather", "süet", "suede"]):
            multiplier *= 1.55
        elif any(w in text_to_search for w in ["mermer", "marble", "granit"]):
            multiplier *= 1.85
        elif any(w in text_to_search for w in ["ahşap", "wood", "meşe", "oak", "ceviz", "walnut", "epoksi", "epoxy"]):
            multiplier *= 1.35
        elif any(w in text_to_search for w in ["cam", "glass", "seramik", "ceramic", "porselen", "porcelain"]):
            multiplier *= 1.45
            
        # [Kategori C: Zanaat ve Geleneksel Türk Üretim Teknikleri]
        if any(w in text_to_search for w in ["telkari", "filigree"]):
            multiplier *= 2.6  # Geleneksel telkari çok ince işçilik gerektirir
        elif any(w in text_to_search for w in ["çini", "tile", "ebru", "marbling"]):
            multiplier *= 2.0  # Geleneksel boyama/çini sanatı
        elif any(w in text_to_search for w in ["oyma", "carving", "üfleme", "blown"]):
            multiplier *= 1.5
        elif any(w in text_to_search for w in ["el yapımı", "el emeği", "handmade", "handcrafted", "artisan", "knitted", "örgü"]):
            multiplier *= 1.35
            
        # [Kategori D: Tarih, Antika & Müze Değeri]
        if any(w in text_to_search for w in ["müze", "museum", "tarihi", "historical", "saray", "palace"]):
            multiplier *= 3.8
        elif any(w in text_to_search for w in ["antika", "antique", "vintage", "retro", "1900", "1800", "osmanlı", "ottoman"]):
            multiplier *= 3.0
            
        # [Kategori E: Sınırlı Üretim & İmza Koleksiyonlar]
        if any(w in text_to_search for w in ["özel tasarım", "limited", "koleksiyon", "special", "unique", "imzalı", "signed"]):
            multiplier *= 1.45
            
        # [Kategori F: Detaylı Hikaye Anlatımı Primi]
        # Eğer ürünün hikayesi uzunsa ve marka değeri yüksekse ekstra değer çarpanı uygulanır
        if len(user_desc) > 120:
            multiplier *= 1.18
        elif len(user_desc) > 60:
            multiplier *= 1.08
            
        # Çarpanları uygula
        calc_tl = base_tl * multiplier
        calc_usd = base_usd * multiplier
        
        # 3) Her ürüne özel benzersiz imza sapması (Metin içeriğine göre milimetrik benzersiz kaymalar)
        # Deterministic olarak her benzersiz metin girdisine özgün, tutarlı bir fiyat aralığı üretir
        text_hash = sum(ord(c) for c in text_to_search) % 50
        variation_tl = (text_hash - 25) * (calc_tl * 0.008) # %12 civarı kontrollü salınım
        variation_usd = (text_hash - 25) * (calc_usd * 0.008)
        
        final_tl = max(180, calc_tl + variation_tl)
        final_usd = max(10, calc_usd + variation_usd)
        
        # Gerçekçi fiyat aralığı (%15 alt ve %15 üst limitler)
        tl_low = int(final_tl * 0.85)
        tl_high = int(final_tl * 1.15)
        usd_low = int(final_usd * 0.85)
        usd_high = int(final_usd * 1.15)
        
        # Profesyonel Türkçe binlik ayraçlı formatlama (Örn: 1.200 TL)
        tr_price = f"{tl_low:,} TL - {tl_high:,} TL".replace(",", ".")
        # Profesyonel Türkçe binlik ayraçlı Global Fiyat (Örn: 1.200 USD)
        global_price = f"{usd_low:,} USD - {usd_high:,} USD".replace(",", ".")

        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'message': '[SUNUM MODU] Analiz başarıyla tamamlandı.',
                'data': {
                    "baslik": f"{user_material} {user_category} (Simüle Edildi)",
                    "export_strategy": {
                        "marketing_hook": f"Sevgiyle ve el emeğiyle üretildi — hikayenizi anlatan benzersiz {user_material} {user_category}. ✨",
                        "suggested_social_media_post": f"✨ Birinci sınıf {user_material} malzemeden üretilen göz alıcı el yapımı {user_category} ile tanışın! 🎨\n\nHer detayında nesillerden nesillere aktarılan geleneksel zanaatın, sevginin ve emeğin hikayesi saklı. Kendiniz veya sevdikleriniz için eşsiz bir hediye! 🛍️\n\n{user_desc[:80]}...\n\n#ElYapimi #Zanaat #Tasarim #TurkZanaati #{user_material.replace(' ', '')} #{user_category.replace(' ', '')} #YerliUretim #Koleksiyon #Girisimci #Zanaatkar #OzelTasarim",
                        "urun_pozisyonlandirma": {
                            "benzersiz_deger_oneri": f"{user_material} kullanılarak üretilen bu {user_category}, {user_desc[:50]}... vizyonuyla fark yaratıyor.",
                            "hedef_pazar_segmenti": f"Premium {user_category} ve {user_material} ürünlerine ilgi duyan kitle."
                        },
                        "fiyatlandirma_stratejisi": {
                            "tr_fiyat_tl": tr_price,
                            "global_fiyat_usd": global_price
                        },
                        "pazar_ve_seo": {
                            "tr_stratejisi": {
                                "platformlar": ["Trendyol", "Shopier", "Hepsiburada"],
                                "seo_kelimeleri": f"{user_category}, {user_material}, el yapımı, tasarım, yerli zanaat"
                            },
                            "global_strateji": {
                                "platformlar": ["Etsy Global", "Amazon Handmade", "Shopify"],
                                "seo_kelimeleri": f"El yapımı {user_category}, {user_material} hediye, zanaatkar {user_category}, tasarım"
                            }
                        },
                        "pazarlama_ve_icerik": {
                            "urun_aciklamasi_tr": f"{user_material} malzemeden titizlikle üretilmiş bu {user_category}, {user_desc}. Zanaatkar ellerden çıkan bu parça, hem dayanıklılığı hem de estetiği bir arada sunuyor.",
                            "urun_aciklamasi_en": f"{user_material} malzemeden titizlikle üretilmiş bu {user_category}, {user_desc}. Zanaatkar ellerden çıkan bu parça, hem dayanıklılığı hem de estetiği bir arada sunuyor.",
                            "ana_mesajlar": [
                                f"Yüksek kaliteli {user_material} kalitesi.",
                                f"Özgün {user_category} tasarımı ve el emeği.",
                                "Sürdürülebilir üretim anlayışı."
                            ]
                        }
                    }
                }
            }
        )

    # Servis kontrolü
    if not orchestrator:
        logger.error("Orchestrator service not ready")
        return JSONResponse(
            status_code=200,
            content={
                'success': False,
                'message': 'Analiz sırasında teknik bir aksaklık oluştu: Orkestratör servisi hazır değil.',
                'data': None
            }
        )
    
    # Dosya validasyonu
    if not file.content_type.startswith('image/'):
        logger.warning(f"Invalid file type: {file.content_type}")
        return JSONResponse(
            status_code=200,
            content={
                'success': False,
                'message': 'Analiz sırasında teknik bir aksaklık oluştu: Lütfen geçerli bir resim dosyası yükleyin (JPG, PNG, WebP).',
                'data': None
            }
        )
    
    # Dosya boyutu kontrolü (max 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        return JSONResponse(
            status_code=200,
            content={
                'success': False,
                'message': "Analiz sırasında teknik bir aksaklık oluştu: Dosya boyutu çok büyük. Lütfen 10MB'dan küçük bir resim yükleyin.",
                'data': None
            }
        )
    
    temp_file_path = None
    
    try:
        logger.info(f"Starting analysis for file: {file.filename}")
        
        # Geçici dosya oluştur
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Tam otonom analizi çalıştır
        result = await orchestrator.run_full_analysis_async(
            temp_file_path, 
            description=description,
            category=category,
            material=material
        )
        
        if result.get('success', False):
            logger.info("Analysis completed successfully")
            return JSONResponse(
                status_code=200,
                content=APIResponse.success(
                    data=result,
                    message="Ürün analizi başarıyla tamamlandı. E-ihracat stratejiniz hazır!"
                ).dict()
            )
        else:
            error_msg = result.get('error', 'Bilinmeyen analiz hatası')
            logger.error(f"Analysis failed: {error_msg}")
            
            return JSONResponse(
                status_code=200,
                content={
                    'success': False,
                    'message': f"Analiz sırasında teknik bir aksaklık oluştu: {error_msg}",
                    'data': None
                }
            )
    
    except Exception as e:
        logger.error(f"Unexpected error in analyze_product: {str(e)}")
        return JSONResponse(
            status_code=200,
            content={
                'success': False,
                'message': f"Analiz sırasında teknik bir aksaklık oluştu: {str(e)}",
                'data': None
            }
        )
    
    finally:
        # Geçici dosyayı temizle
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"Temporary file cleaned: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean temp file: {str(e)}")

@app.post("/studio-ai")
async def studio_ai(
    file: UploadFile = File(...),
    background_type: str = Form("studio_white"),
):
    """
    Studio AI Endpoint
    ==================
    1. rembg ile arka planı siler → şeffaf PNG
    2. Gemini ile seçilen arka plan temasında profesyonel stüdyo ortamı ekler
    3. Sonuç JPEG görselini base64 olarak döndürür

    Desteklenen background_type değerleri:
    - studio_white, rustic_wood, minimal_marble,
      modern_concrete, nature_leaves, premium_black
    """
    if not studio_service:
        return JSONResponse(
            status_code=200,
            content={
                'success': False,
                'message': 'Studio AI servisi hazır değil.',
                'data': None
            }
        )

    if not file.content_type or not file.content_type.startswith('image/'):
        return JSONResponse(
            status_code=200,
            content={
                'success': False,
                'message': 'Lütfen geçerli bir resim dosyası yükleyin (JPG, PNG, WebP).',
                'data': None
            }
        )

    try:
        logger.info(f"🎨 Studio AI isteği alındı: {file.filename} (tema: {background_type})")
        image_bytes = await file.read()

        # Pipeline: arka plan sil → seçilen temada stüdyo ortamı ekle
        result_bytes = await studio_service.process_studio_ai(image_bytes, background_type)

        # JPEG → base64
        result_b64 = base64.b64encode(result_bytes).decode('utf-8')

        logger.info("✅ Studio AI: Profesyonel görsel başarıyla oluşturuldu.")
        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'message': 'Ürününüz başarıyla profesyonel stüdyo ortamına taşındı!',
                'data': {
                    'studio_image_base64': result_b64,
                    'mime_type': 'image/jpeg',
                    'background_type': background_type
                }
            }
        )

    except Exception as e:
        logger.error(f"❌ Studio AI hatası: {str(e)}")
        return JSONResponse(
            status_code=200,
            content={
                'success': False,
                'message': f'Studio AI işlemi sırasında bir hata oluştu: {str(e)}',
                'data': None
            }
        )


@app.get("/docs")
async def get_docs():
    """API dokümantasyonunu döndürür"""
    return APIResponse.success(ENDPOINT_DOCS, "API Dokümantasyonu")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
