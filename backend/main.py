from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import logging
from dotenv import load_dotenv
from orchestrator_service import ZanaatsAlOrchestrator
from api_contract import APIResponse, ENDPOINT_DOCS

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
    print("✅ ZanaatsAl Orkestratör başarıyla yüklendi")
except Exception as e:
    print(f"❌ Orkestratör yüklenemedi: {str(e)}")
    orchestrator = None

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
        logger.info("Mock analysis triggered")
        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'message': 'Mock analiz başarılı.',
                'data': {
                    "baslik": "El Yapımı Seramik Vazo (Mock)",
                    "export_strategy": {
                        "urun_pozisyonlandirma": {
                            "benzersiz_deger_oneri": "Özgün tasarım ve premium malzeme birleşimi",
                            "farklasilma_stratejisi": "Premium materyal ve tamamen el işçiliği ile fabrikasyon ürünlerden ayrışır.",
                            "hedef_pazar_segmenti": "Özel tasarımlara ilgi duyan kitle."
                        },
                        "fiyatlandirma_stratejisi": {
                            "onerilen_fiyat_araligi": "45.00 - 65.00 USD",
                            "fiyatlandirma_mantigi": "Premium materyal ve el işçiliği vurgusu ile orta-üst segment",
                            "psikolojik_fiyatlandirma": "49.99 USD veya 54.99 USD"
                        },
                        "platform_stratejisi": {
                            "oncelikli_platformlar": ["Etsy", "Amazon Handmade"],
                            "platform_ozel_stratejiler": "Etsy'de yapım aşaması videoları.",
                            "cross_promotion": "Instagram Reels üzerinden trafik sağlanmalı."
                        },
                        "pazarlama_ve_icerik": {
                            "ana_mesajlar": [
                                "Zamansız tasarım, uzun ömürlü kullanım.",
                                "Tamamen el yapımı ve sürdürülebilir.",
                                "Size özel benzersiz bir parça."
                            ],
                            "hedef_kitle_mesajlari": "Kaliteyi ve özgünlüğü arayanlara özel.",
                            "icerik_turleri": ["Yapım Aşaması Reels", "Detay Fotoğrafları"],
                            "seo_stratejisi": "Handmade artisan product, unique design, premium quality."
                        },
                        "ihracat_odakli_oneriler": {
                            "ulke_odaklari": ["ABD", "Birleşik Krallık", "Almanya"],
                            "kulturel_uyarlama": "Minimalist ve estetik odaklı sunum.",
                            "lojistik_onerileri": "Özel kutulu premium kargo gönderimi."
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

@app.get("/docs")
async def get_docs():
    """API dokümantasyonunu döndürür"""
    return APIResponse.success(ENDPOINT_DOCS, "API Dokümantasyonu")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
