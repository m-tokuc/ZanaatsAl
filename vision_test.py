import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Load environment variables
load_dotenv()

def test_vision_analysis(image_path: str):
    """
    Gemini 1.5 Flash ile ürün görsel analizi testi
    """
    
    # API anahtarını yapılandır
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ HATA: GOOGLE_API_KEY bulunamadı!")
        print("📝 Lütfen .env dosyasına API anahtarınızı ekleyin:")
        print("cp .env.example .env")
        return None
    
    genai.configure(api_key=api_key)
    
    # Mevcut modelleri listele
    print("📋 Mevcut modeller:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
    
    try:
        # Gemini 2.5 Flash modelini seç
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Görüntüyü yükle
        image = Image.open(image_path)
        
        # Analiz prompt'u
        prompt = """
        Bu ürünün e-ticaret için analizini yap ve JSON formatında cevap ver:
        
        {
            "kategori": "ürünün ana kategorisi (örn: deri çanta, takı, seramik)",
            "materyal": "ana malzeme (örn: deri, gümüş, kil)",
            "stil": "tasarım stili (örn: modern, vintage, bohem, minimalist)",
            "hedef_kitle": "potansiyel müşteri profili",
            "anahtar_kelimeler": ["etiket1", "etiket2", "etiket3"],
            "fiyat_araligi": "düşük/orta/yüksek",
            "platform_uyumlulugu": ["Etsy", "Amazon", "Instagram"]
        }
        
        Sadece JSON formatında cevap ver, ek açıklama yapma.
        """
        
        print(f"🔍 Görüntü analiz ediliyor: {image_path}")
        
        # Analizi yap
        response = model.generate_content([prompt, image])
        
        # Debug: Raw response
        print(f"🔍 Raw response: {response.text}")
        
        # JSON cevabını parse et (markdown code block'ını temizle)
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]  # ```json kaldır
        if response_text.endswith('```'):
            response_text = response_text[:-3]  # ``` kaldır
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        
        print("✅ Analiz başarılı!")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
        
    except Exception as e:
        print(f"❌ Analiz sırasında hata: {str(e)}")
        return None

def main():
    """
    Test fonksiyonu - örnek bir görselle test
    """
    print("🚀 ZanaatsAl Vision Test Başlatılıyor...")
    print("=" * 50)
    
    # Test için örnek görsel yolu
    test_image_path = "ipad_case.jpeg"
    
    if not os.path.exists(test_image_path):
        print(f"⚠️  Test görseli bulunamadı: {test_image_path}")
        print("📁 Lütfen test_products klasörü oluşturup bir ürün görseli ekleyin")
        return
    
    result = test_vision_analysis(test_image_path)
    
    if result:
        print("\n🎯 Vision Test Başarılı!")
        print("📊 Sonuçlar yukarıda gösterildi.")
    else:
        print("\n❌ Vision Test Başarısız!")

if __name__ == "__main__":
    main()
