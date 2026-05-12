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
    
    def run_full_analysis(self, image_path: str) -> Dict:
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
                return {'error': 'Vision analizi başarısız'}
            
            # Adım 2: Pazar Araştırması
            print("\n🔍 Adım 2: Pazar Araştırması")
            market_result = self._run_market_research(vision_result['anahtar_kelimeler'])
            if not market_result:
                return {'error': 'Pazar araştırması başarısız'}
            
            # Adım 3: Strateji Üretimi
            print("\n🧠 Adım 3: E-İhracat ve Satış Stratejisi Üretimi")
            strategy_result = self._generate_export_strategy(vision_result, market_result)
            if not strategy_result:
                return {'error': 'Strateji üretimi başarısız'}
            
            # Nihai Rapor
            final_report = {
                'analysis_timestamp': self._get_timestamp(),
                'product_vision': vision_result,
                'market_research': market_result,
                'export_strategy': strategy_result,
                'success': True
            }
            
            print("\n🎯 Tam Otonom Analiz Tamamlandı!")
            return final_report
            
        except Exception as e:
            print(f"❌ Analiz hatası: {str(e)}")
            return {
                'error': f'Analiz sırasında hata oluştu: {str(e)}',
                'success': False
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
    
    def _generate_export_strategy(self, vision_data: Dict, market_data: Dict) -> Optional[Dict]:
        """
        Vision ve pazar verilerine dayalı E-ihracat stratejisi üretir
        """
        try:
            # Strateji prompt'u oluştur
            strategy_prompt = self._create_strategy_prompt(vision_data, market_data)
            
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
    
    def _create_strategy_prompt(self, vision_data: Dict, market_data: Dict) -> str:
        """
        Strateji üretimi için Gemini prompt'u oluşturur
        """
        prompt = f"""
        SEN BİR E-İHRACAT DANIŞMANISIN. Aşağıdaki verileri analiz ederek profesyonel bir E-İhracat ve Satış Stratejisi hazırla:
        
        === ÜRÜN VİZYON ANALİZİ ===
        Kategori: {vision_data.get('kategori', 'N/A')}
        Materyal: {vision_data.get('materyal', 'N/A')}
        Stil: {vision_data.get('stil', 'N/A')}
        Hedef Kitle: {vision_data.get('hedef_kitle', 'N/A')}
        Anahtar Kelimeler: {', '.join(vision_data.get('anahtar_kelimeler', []))}
        Fiyat Aralığı: {vision_data.get('fiyat_araligi', 'N/A')}
        
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
                "farklasilma_stratejisi": "Rakiplerden nasıl ayrışılacak",
                "hedef_pazar_segmenti": "Odaklanılacak pazar segmenti"
            }},
            "fiyatlandirma_stratejisi": {{
                "onerilen_fiyat_araligi": "USD cinsinden fiyat aralığı",
                "fiyatlandirma_mantigi": "Premium/mid-range/budget",
                "psikolojik_fiyatlandirma": "Örnek fiyat noktaları"
            }},
            "platform_stratejisi": {{
                "oncelikli_platformlar": ["Etsy", "Amazon", "Instagram"],
                "platform_ozel_stratejiler": "Her platform için özel yaklaşım",
                "cross_promotion": "Platformlar arası promosyon"
            }},
            "pazarlama_ve_icerik": {{
                "ana_mesajlar": ["Ana pazarlama mesajları"],
                "hedef_kitle_mesajlari": "Farklı kitlelere özel mesajlar",
                "icerik_turleri": ["Video", "Blog", "Social Media"],
                "seo_stratejisi": "Anahtar kelime stratejisi"
            }},
            "operasyonel_plan": {{
                "adimlar": ["Aylık bazda adımlar"],
                "kpi_metrikleri": ["Başarı ölçütleri"],
                "riskler": ["Potansiyel riskler ve çözümler"]
            }},
            "ihracat_odakli_oneriler": {{
                "ulke_odaklari": ["Öncelikli ülkeler"],
                "kulturel_uyarlama": "Kültürel farklılıklara göre uyarlama",
                "lojistik_onerileri": "Uluslararası gönderim stratejisi"
            }}
        }}
        
        Lütfen sadece JSON formatında cevap ver, ek açıklama yapma.
        """
        
        return prompt
    
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
