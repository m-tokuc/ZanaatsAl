"""
ZanaatsAl API Kontratı
Hanife (Frontend) için standartlaştırılmış API yanıtları
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class ProductVision(BaseModel):
    """Ürün Vision Analizi Sonucu"""
    kategori: str
    materyal: str
    stil: str
    hedef_kitle: str
    anahtar_kelimeler: List[str]
    fiyat_araligi: str
    platform_uyumlulugu: List[str]

class MarketData(BaseModel):
    """Pazar Araştırması Verisi"""
    etsy_results: Dict[str, Any]
    amazon_results: Dict[str, Any]
    price_analysis: Dict[str, Any]
    customer_insights: Dict[str, Any]

class StrategyReport(BaseModel):
    """E-İhracat Strateji Raporu"""
    urun_degerlendirmesi: Dict[str, str]
    fiyatlama_stratejisi: Dict[str, Any]
    pazarlama_metni: Dict[str, str]
    platform_stratejisi: Dict[str, Any]
    riskler: List[str]

class AnalysisResponse(BaseModel):
    """Tam Analiz Yanıtı"""
    success: bool
    message: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Sağlık Kontrolü Yanıtı"""
    status: str
    api_key_configured: bool
    serper_configured: bool
    orchestrator_ready: bool
    version: str

# API Yanı Şablonları
class APIResponse:
    """Standart API yanıtları"""
    
    @staticmethod
    def success(data: Dict[str, Any], message: str = "İşlem başarılı") -> AnalysisResponse:
        return AnalysisResponse(
            success=True,
            message=message,
            timestamp=datetime.now().isoformat(),
            data=data
        )
    
    @staticmethod
    def error(message: str, error_code: str = "GENERAL_ERROR") -> AnalysisResponse:
        return AnalysisResponse(
            success=False,
            message=message,
            timestamp=datetime.now().isoformat(),
            error=error_code
        )
    
    @staticmethod
    def health_check() -> HealthResponse:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        return HealthResponse(
            status="healthy",
            api_key_configured=bool(os.getenv("GOOGLE_API_KEY")),
            serper_configured=bool(os.getenv("SERPER_API_KEY")),
            orchestrator_ready=True,  # Bu dinamik kontrol edilebilir
            version="0.1.0"
        )

# Endpoint Dokümantasyonu
ENDPOINT_DOCS = {
    "/": {
        "method": "GET",
        "description": "API bilgilerini ve endpoint listesini döndürür",
        "response": {
            "message": "ZanaatsAl API'ye hoş geldiniz!",
            "version": "0.1.0",
            "status": "active",
            "endpoints": {
                "health": "/health",
                "analyze": "/analyze (POST - Upload image for full analysis)"
            }
        }
    },
    "/health": {
        "method": "GET",
        "description": "API servislerinin durumunu kontrol eder",
        "response": "HealthResponse modeli"
    },
    "/analyze": {
        "method": "POST",
        "description": "Ürün görselini analiz eder ve tam e-ihracat stratejisi üretir",
        "parameters": {
            "file": "multipart/form-data - Ürün görseli (jpg, png, webp)"
        },
        "response": "AnalysisResponse modeli",
        "flow": [
            "1. Vision analizi (Gemini 2.5 Flash)",
            "2. Pazar araştırması (Serper.dev - Etsy/Amazon)",
            "3. Strateji üretimi (E-İhracat Danışmanı)",
            "4. JSON formatında tam rapor"
        ],
        "error_handling": [
            "Vision hatası → Genel strateji ile devam",
            "Pazar verisi yok → Vision verisiyle strateji",
            "API hatası → Detaylı hata mesajı"
        ]
    }
}
