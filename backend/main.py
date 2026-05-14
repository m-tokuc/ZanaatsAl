from fastapi import FastAPI, UploadFile, File, HTTPException
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
    """API ana sayfası - endpoint dokümantasyonu"""
    return APIResponse.success(ENDPOINT_DOCS, "ZanaatsAl API'ye hoş geldiniz!")

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
async def analyze_product(file: UploadFile = File(...)):
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
    # Servis kontrolü
    if not orchestrator:
        logger.error("Orchestrator service not ready")
        raise HTTPException(
            status_code=503, 
            detail="Orkestratör servisi hazır değil. Lütfen daha sonra tekrar deneyin."
        )
    
    # Dosya validasyonu
    if not file.content_type.startswith('image/'):
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(
            status_code=400, 
            detail="Lütfen geçerli bir resim dosyası yükleyin (JPG, PNG, WebP)"
        )
    
    # Dosya boyutu kontrolü (max 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413, 
            detail="Dosya boyutu çok büyük. Lütfen 10MB'dan küçük bir resim yükleyin."
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
        result = await orchestrator.run_full_analysis_async(temp_file_path)
        
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
                status_code=500,
                content=APIResponse.error(
                    message=f"Analiz sırasında hata oluştu: {error_msg}",
                    error_code="ANALYSIS_FAILED"
                ).dict()
            )
    
    except HTTPException:
        # HTTP hatalarını yeniden fırlat
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in analyze_product: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=APIResponse.error(
                message="Beklenmedik bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
                error_code="INTERNAL_ERROR"
            ).dict()
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
