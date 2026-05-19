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
        
        # Dinamik Fiyatlandırma Motoru (Mock/Sunum Modu için)
        cat_prices = {
            'Çanta & Cüzdan': ('1,200.00 TL - 2,400.00 TL', '45.00 USD - 85.00 USD'),
            'Giyim & Moda': ('850.00 TL - 1,950.00 TL', '35.00 USD - 75.00 USD'),
            'Ayakkabı': ('1,800.00 TL - 3,800.00 TL', '65.00 USD - 140.00 USD'),
            'Takı & Aksesuar': ('350.00 TL - 950.00 TL', '15.00 USD - 40.00 USD'),
            'Teknoloji Aksesuarları (iPad Kılıfı vb.)': ('750.00 TL - 1,600.00 TL', '28.00 USD - 60.00 USD'),
            'Ev & Yaşam': ('900.00 TL - 2,800.00 TL', '35.00 USD - 100.00 USD'),
            'Dekorasyon & Sanat': ('1,500.00 TL - 5,500.00 TL', '55.00 USD - 200.00 USD'),
            'Mutfak Gereçleri': ('450.00 TL - 1,400.00 TL', '18.00 USD - 50.00 USD'),
            'Kozmetik & Kişisel Bakım': ('300.00 TL - 850.00 TL', '12.00 USD - 32.00 USD'),
            'Hobi & Oyuncak': ('400.00 TL - 1,200.00 TL', '15.00 USD - 45.00 USD'),
            'Diğer': ('500.00 TL - 1,500.00 TL', '20.00 USD - 60.00 USD')
        }
        
        tr_price, global_price = cat_prices.get(category if category else 'Diğer', ('600.00 TL - 1,800.00 TL', '25.00 USD - 70.00 USD'))

        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'message': '[SUNUM MODU] Analiz başarıyla tamamlandı.',
                'data': {
                    "baslik": f"{user_material} {user_category} (Simüle Edildi)",
                    "export_strategy": {
                        "marketing_hook": f"Handcrafted with love — meet the {user_material} {user_category} that tells your story. ✨",
                        "suggested_social_media_post": f"✨ Introducing our stunning handmade {user_category} crafted from premium {user_material}! 🎨\n\nEvery piece tells a story of tradition, skill, and artistry passed down through generations. Perfect as a gift or a treat for yourself! 🛍️\n\n{user_desc[:80]}...\n\n#Handmade #Artisan #TurkishCraft #{user_material.replace(' ', '')} #{user_category.replace(' ', '')} #EtsySeller #ShopSmall #MadeWithLove #UniqueGifts #HandcraftedGoods #ArtisanMade #BuyArtisan #SlowFashion",
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
                                "seo_kelimeleri": f"{user_category}, {user_material}, el yapımı, tasarım"
                            },
                            "global_strateji": {
                                "platformlar": ["Etsy", "Amazon Handmade", "Shopify"],
                                "seo_kelimeleri": f"Handmade {user_category}, {user_material} gift, artisan {user_category}"
                            }
                        },
                        "pazarlama_ve_icerik": {
                            "urun_aciklamasi_tr": f"{user_material} malzemeden titizlikle üretilmiş bu {user_category}, {user_desc}. Zanaatkar ellerden çıkan bu parça, hem dayanıklılığı hem de estetiği bir arada sunuyor.",
                            "urun_aciklamasi_en": f"This {user_category} is meticulously crafted from {user_material}. {user_desc} This piece from artisan hands offers both durability and aesthetics together.",
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
