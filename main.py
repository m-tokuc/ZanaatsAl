from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
from dotenv import load_dotenv
from orchestrator_service import ZanaatsAlOrchestrator

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
    return {
        "message": "ZanaatsAl API'ye hoş geldiniz!",
        "version": "0.1.0",
        "status": "active",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze (POST - Upload image for full analysis)"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "serper_configured": bool(os.getenv("SERPER_API_KEY")),
        "orchestrator_ready": orchestrator is not None
    }

@app.post("/analyze")
async def analyze_product(file: UploadFile = File(...)):
    """
    Ürün görselini yükler ve tam otonom analiz yapar
    Vision + Market Research + E-İhracat Stratejisi
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orkestratör servisi hazır değil")
    
    # Dosya kontrolü
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Lütfen bir resim dosyası yükleyin")
    
    try:
        # Geçici dosya oluştur
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Tam otonom analizi çalıştır
            result = orchestrator.run_full_analysis(temp_file_path)
            
            if result.get('success', False):
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "Ürün analizi başarıyla tamamlandı",
                        "data": result
                    }
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "message": "Analiz sırasında hata oluştu",
                        "error": result.get('error', 'Bilinmeyen hata')
                    }
                )
        
        finally:
            # Geçici dosyayı temizle
            import os
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
