# ZanaatsAl 🚀

ZanaatsAl, yerel üreticilerin, zanaatkarların ve el emeğiyle üretim yapanların e-ihracat süreçlerini tek bir ekrandan yönetebilmesi için geliştirilmiş yapay zeka destekli bir mobil asistandır. 

Amacımız; ürün fotoğrafı çekiminden pazar analizine ve dil bariyerine kadar uzanan zorlu operasyonları otonom hale getirerek, üreticinin sadece üretmeye odaklanmasını sağlamaktır.

## ✨ Temel Özellikler

* **🎨 AI Sanal Stüdyo:** Amatör çekilmiş ürün fotoğraflarının arka planı temizlenir. Yapay zeka ile ürünler profesyonel stüdyo konseptlerine (mermer, ahşap vb.) yerleştirilir. Işık (relighting) ve zemin gölgeleri hesaplanarak görseldeki yapaylık tamamen giderilir.
* **💰 Otonom Pazar Analizi:** Ürün görseli üzerinden analiz yapılarak Etsy ve Amazon gibi global platformlar taranır. Rakip analizleriyle birlikte Türkiye ve Global pazar için optimum satış fiyatı önerilir.
* **✍️ Native SEO & Metin Optimizasyonu:** Türkçe girilen kısa ürün bilgileri, doğrudan Amerikan e-ticaret pazarına uygun (native), akıcı ve SEO odaklı İngilizce satış metinlerine dönüştürülür. Robotik çeviriler kullanılmaz.
* **📱 Sosyal Medya Ajanı (Agentic):** Satışa hazır ürün için trend İngilizce hashtag'leri barındıran, paylaşıma hazır sosyal medya postları tek tıkla üretilir.

## 🛠️ Teknolojik Altyapı (Monorepo)

Projemiz `frontend` ve `backend` olarak iki ana yapıdan oluşmaktadır.

* **Frontend:** Flutter & Dart (Mobil Uygulama Arayüzü)
* **Backend:** Python, FastAPI (Yapay Zeka ve API Yönetimi)
* **AI Entegrasyonları:** Gemini (Metin ve Fiyatlandırma), Serper.dev (Market Research), Stable Diffusion / Image Processing (Görsel İşleme ve Gölgelendirme)

## 🚀 Kurulum ve Çalıştırma

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyebilirsiniz.

### 1. Backend (Python/FastAPI)
```bash
cd backend
# Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt

# .env dosyanızı oluşturup gerekli API anahtarlarını (Gemini, Serper vb.) girin.

# Sunucuyu başlatın
python main.py
