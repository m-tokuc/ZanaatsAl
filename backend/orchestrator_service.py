import os
import json
from typing import Dict, Optional
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
from vision_test import test_vision_analysis
from serper_service import MarketResearchAgent

# Load environment variables
load_dotenv()

class ZanaatsAlOrchestrator:
    """
    ZanaatsAl Ana Orkestratör Servisi
    Vision ve Market Research servislerini entegre ederek tam otonom analiz akışı sağlar
    """
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY bulunamadı! .env dosyasını kontrol edin.")
        
        genai.configure(api_key=self.api_key)
        self.strategy_model = genai.GenerativeModel('gemini-2.5-flash')
        self.market_agent = MarketResearchAgent()
    
    async def run_full_analysis_async(self, image_path: str, description: Optional[str] = None, category: Optional[str] = None, material: Optional[str] = None) -> Dict:
        """
        Tam otonom analiz akışı:
        1. Vision analizi
        2. Pazar araştırması
        3. E-ihracat stratejisi üretimi
        """
        print("🚀 ZanaatsAl Tam Otonom Analiz Başlatılıyor...")
        print("=" * 60)
        
        try:
            # Adım 1: Vision Analizi
            print("📸 Adım 1: Ürün Vision Analizi")
            vision_result = self._run_vision_analysis(image_path)
            if not vision_result:
                return {'error': 'Vision analizi başarısız', 'success': False}
            
            # Adım 2: Pazar Araştırması (Fallback ile)
            print("\n🔍 Adım 2: Pazar Araştırması")
            market_result = self._run_market_research(vision_result['anahtar_kelimeler'])
            
            # Pazar verisi bulunamazsa fallback strateji
            if not market_result or market_result.get('total_results', 0) == 0:
                print("⚠️ Pazar verisi bulunamadı, genel strateji ile devam ediliyor...")
                market_result = self._generate_fallback_market_data(vision_result)
            
            # Adım 3: Strateji Üretimi
            print("\n🧠 Adım 3: E-İhracat ve Satış Stratejisi Üretimi")
            strategy_result = self._generate_export_strategy(vision_result, market_result, description, category, material)
            if not strategy_result:
                # Strateji üretimi başarısız olursa basit fallback
                strategy_result = self._generate_fallback_strategy(vision_result)
            
            # Nihai Rapor
            final_report = {
                'analysis_timestamp': self._get_timestamp(),
                'product_vision': vision_result,
                'market_research': market_result,
                'export_strategy': strategy_result,
                'success': True,
                'warnings': [] if market_result else ['Pazar verisi bulunamadı, genel strateji kullanıldı']
            }
            
            print("\n🎯 Tam Otonom Analiz Tamamlandı!")
            return final_report
            
        except Exception as e:
            print(f"❌ Analiz hatası: {str(e)}")
            return {
                'error': f'Analiz sırasında hata oluştu: {str(e)}',
                'success': False,
                'fallback_used': True
            }
    
    def _run_vision_analysis(self, image_path: str) -> Optional[Dict]:
        """
        Vision analizi yapar
        """
        try:
            # Vision test fonksiyonunu kullan
            result = test_vision_analysis(image_path)
            return result
        except Exception as e:
            print(f"❌ Vision analizi hatası: {str(e)}")
            return None
    
    def _run_market_research(self, keywords: list) -> Optional[Dict]:
        """
        Pazar araştırması yapar
        """
        try:
            result = self.market_agent.analyze_competitor_data(keywords)
            return result
        except Exception as e:
            print(f"❌ Pazar araştırması hatası: {str(e)}")
            return None
    
    def _generate_export_strategy(self, vision_data: Dict, market_data: Dict, description: Optional[str] = None, category: Optional[str] = None, material: Optional[str] = None) -> Optional[Dict]:
        """
        Vision ve pazar verilerine dayalı E-ihracat stratejisi üretir
        """
        try:
            # Strateji prompt'u oluştur
            strategy_prompt = self._create_strategy_prompt(vision_data, market_data, description, category, material)
            
            print("📝 Strateji analizi yapılıyor...")
            
            # Gemini ile strateji üret
            response = self.strategy_model.generate_content(strategy_prompt)
            
            # JSON formatında strateji parse et
            strategy_text = response.text.strip()
            if strategy_text.startswith('```json'):
                strategy_text = strategy_text[7:]
            if strategy_text.endswith('```'):
                strategy_text = strategy_text[:-3]
            strategy_text = strategy_text.strip()
            
            try:
                strategy_result = json.loads(strategy_text)
            except json.JSONDecodeError:
                # JSON parse başarısız olursa, metni olarak döndür
                strategy_result = {
                    'strategy_text': strategy_text,
                    'format': 'raw_text'
                }
            
            print("✅ Strateji üretimi başarılı!")
            return strategy_result
            
        except Exception as e:
            print(f"❌ Strateji üretimi hatası: {str(e)}")
            return None
    
    def _create_strategy_prompt(self, vision_data: Dict, market_data: Dict, description: Optional[str] = None, category: Optional[str] = None, material: Optional[str] = None) -> str:
        """
        Strateji üretimi için Gemini prompt'u oluşturur
        """
        prompt = f"""
        SEN BİR E-İHRACAT DANIŞMANISIN. Aşağıdaki verileri analiz ederek profesyonel bir E-İhracat ve Satış Stratejisi hazırla:
        
        === ÜRÜN VİZYON ANALİZİ VE KULLANICI VERİLERİ ===
        Kategori (Yapay Zeka): {vision_data.get('kategori', 'N/A')}
        Kategori (Kullanıcı Seçimi): {category if category else 'Belirtilmedi'}
        Materyal (Kullanıcı Seçimi): {material if material else 'Belirtilmedi'}
        Materyal (Yapay Zeka): {vision_data.get('materyal', 'N/A')}
        Stil: {vision_data.get('stil', 'N/A')}
        Hedef Kitle: {vision_data.get('hedef_kitle', 'N/A')}
        Anahtar Kelimeler: {', '.join(vision_data.get('anahtar_kelimeler', []))}
        Fiyat Aralığı: {vision_data.get('fiyat_araligi', 'N/A')}
        Satıcı/Kullanıcı Açıklaması: {description if description else 'Belirtilmedi'}
        
        === PAZAR ARAŞTIRMASI ===
        Etsy Sonuçları: {market_data.get('etsy_results', {}).get('total_found', 0)} ürün bulundu
        Amazon Sonuçları: {market_data.get('amazon_results', {}).get('total_found', 0)} ürün bulundu
        
        Fiyat Analizi:
        - Ortalama Fiyat: ${market_data.get('price_analysis', {}).get('average_price', 'N/A')}
        - Min Fiyat: ${market_data.get('price_analysis', {}).get('min_price', 'N/A')}
        - Max Fiyat: ${market_data.get('price_analysis', {}).get('max_price', 'N/A')}
        
        Müşteri Yorumları:
        - Analiz Edilen Yorum: {market_data.get('customer_insights', {}).get('total_reviews_analyzed', 0)}
        - Pozitif Oran: %{market_data.get('customer_insights', {}).get('sentiment_analysis', {}).get('positive_percentage', 0)}
        
        === İSTENEN STRATEJİ FORMATI ===
        JSON formatında şu alanları içeren kapsamlı bir strateji hazırla:
        
        {{
            "urun_pozisyonlandirma": {{
                "benzersiz_deger_oneri": "Ürünün benzersiz satış noktası",
                "hedef_pazar_segmenti": "Odaklanılacak pazar segmenti"
            }},
            "fiyatlandirma_stratejisi": {{
                "tr_fiyat_tl": "Türkiye pazarı için tahmini fiyat aralığı (TL, örn: 450 - 600 TL)",
                "global_fiyat_usd": "Global pazar için tahmini fiyat aralığı (USD, örn: $35 - $50)"
            }},
            "pazar_ve_seo": {{
                "tr_stratejisi": {{
                    "platformlar": ["Trendyol", "Shopier", "Hepsiburada"],
                    "seo_kelimeleri": "Türkiye için Türkçe SEO anahtar kelimeleri"
                }},
                "global_strateji": {{
                    "platformlar": ["Etsy", "Amazon", "Shopify"],
                    "seo_kelimeleri": "Global pazar için İngilizce SEO anahtar kelimeleri"
                }}
            }},
            "pazarlama_ve_icerik": {{
                "urun_aciklamasi_tr": "Satıcının doğrudan kopyalayıp ürününe yapıştırabileceği ikna edici Türkçe e-ticaret açıklaması",
                "urun_aciklamasi_en": "Satıcının doğrudan kopyalayıp ürününe yapıştırabileceği ikna edici İngilizce e-ticaret açıklaması (Translated description)",
                "ana_mesajlar": ["Ana pazarlama mesajları"]
            }}
        }}
        
        Lütfen sadece JSON formatında cevap ver, ek açıklama yapma.
        """
        
        return prompt
    
    def _generate_fallback_market_data(self, vision_data: Dict) -> Dict:
        """
        Pazar verisi bulunamazsa genel fallback verileri üretir
        """
        return {
            'keywords_analyzed': vision_data.get('anahtar_kelimeler', []),
            'etsy_results': {'total_found': 0, 'top_products': []},
            'amazon_results': {'total_found': 0, 'top_products': []},
            'price_analysis': {
                'average_price': 15.0,
                'min_price': 8.0,
                'max_price': 25.0,
                'price_range': 17.0,
                'total_products_analyzed': 0,
                'note': 'Genel pazar tahmini kullanıldı'
            },
            'customer_insights': {
                'total_reviews_analyzed': 0,
                'sentiment_analysis': {
                    'positive_percentage': 70.0,
                    'negative_percentage': 10.0,
                    'neutral_percentage': 20.0
                },
                'sample_reviews': [],
                'key_insights': ['Yeterli veri bulunamadı, genel varsayımlar kullanıldı']
            },
            'research_timestamp': self._get_timestamp(),
            'fallback_used': True
        }
    
    def _generate_fallback_strategy(self, vision_data: Dict) -> Dict:
        """
        Strateji üretimi başarısız olursa basit fallback strateji
        """
        return {
            'urun_degerlendirmesi': {
                'benzersiz_deger_oneri': vision_data.get('stil', 'Modern') + ' tasarım',
                'farklasilma_stratejisi': 'Kalite ve estetik odaklı',
                'hedef_pazar_segmenti': vision_data.get('hedef_kitle', 'Genel kullanıcılar')
            },
            'fiyatlandirma_stratejisi': {
                'onerilen_fiyat_araligi': '10-25 USD',
                'fiyatlandirma_mantigi': 'Mid-range',
                'psikolojik_fiyatlandirma': '14.99, 19.99, 24.99'
            },
            'pazarlama_ve_icerik': {
                'ana_mesajlar': [
                    f"{vision_data.get('kategori', 'Ürün')} için kaliteli çözüm",
                    "Modern ve şık tasarım",
                    "Uygun fiyat, yüksek kalite"
                ],
                'seo_stratejisi': 'Anahtar kelime optimizasyonu yapılacak',
                'icerik_turleri': ['Görsel', 'Video', 'Açıklama']
            },
            'platform_stratejisi': {
                'oncelikli_platformlar': ['Etsy', 'Amazon', 'Instagram'],
                'platform_ozel_stratejiler': 'Her platform için özel yaklaşım',
                'cross_promotion': 'Platformlar arası entegrasyon'
            },
            'ihracat_odakli_oneriler': {
                'ulke_odaklari': ['ABD', 'Almanya', 'UK'],
                'kulturel_uyarlama': 'Yerel dil ve kültürel uyarlama',
                'lojistik_onerileri': 'Uluslararası kargo çözümleri'
            },
            'fallback_used': True
        }
    
    def _get_timestamp(self) -> str:
        """
        Zaman damgası oluşturur
        """
        from datetime import datetime
        return datetime.now().isoformat()

# Test fonksiyonu
def test_orchestrator():
    """
    Orkestratör servisi test
    """
    try:
        orchestrator = ZanaatsAlOrchestrator()
        
        # Test görseli
        test_image = "ipad_case.jpeg"
        
        print("🧪 ZanaatsAl Orkestratör Test Başlatılıyor...")
        print(f"📸 Test görseli: {test_image}")
        
        result = orchestrator.run_full_analysis(test_image)
        
        if result.get('success', False):
            print("\n📊 TAM OTONOM ANALİZ RAPORU:")
            print("=" * 50)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Test başarısız: {result.get('error', 'Bilinmeyen hata')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test hatası: {str(e)}")
        return None

if __name__ == "__main__":
    test_orchestrator()
