"""
ZanaatsAl Studio AI Servisi
============================
İş Akışı:
  1. Gelen resimden rembg ile arka plan silinir → şeffaf PNG elde edilir
  2. Şeffaf PNG base64'e çevrilerek Gemini'nin görsel analiz modeline gönderilir
  3. Gemini, ürünü profesyonel stüdyo ortamında (mermer tezgah, ahşap arka plan)
     yeniden render eder ve sonuç base64 PNG olarak döndürülür
"""

import io
import os
import base64
import logging
import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image
from rembg import remove as rembg_remove
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sabitler
# ---------------------------------------------------------------------------
STUDIO_PROMPT = (
    "Sen bir profesyonel ürün fotoğraf editörüsün. "
    "Bu resimde arka planı tamamen kaldırılmış ve yalnızca ürün görünmekte. "
    "Ürünü minimalist bir mermer tezgahın üzerine doğal biçimde yerleştir. "
    "Ortamı şu özelliklerle tamamla: profesyonel stüdyo ışıklandırması (soft-box), "
    "doğal yumuşak gölgeler, şık sıcak tonlu ahşap arka plan dokusu, "
    "stüdyo bokeh efekti (hafif bulanık arka plan derinliği). "
    "KRITIK KURAL: Ürünün kendi şeklini, rengini, dokusunu veya detaylarını "
    "kesinlikle değiştirme. Sadece arka planı ve ortamı ekle. "
    "Sonuç; Etsy, Amazon veya Trendyol gibi global e-ticaret platformlarında "
    "satışa hazır, profesyonel bir ürün görseli olmalı."
)

MAX_IMAGE_SIZE = (1024, 1024)   # Gemini'ye gönderilecek max boyut
JPEG_QUALITY   = 90


# ---------------------------------------------------------------------------
# Yardımcı Fonksiyonlar
# ---------------------------------------------------------------------------

def _resize_if_needed(img: Image.Image, max_size: tuple = MAX_IMAGE_SIZE) -> Image.Image:
    """Resim boyutunu LANCZOS ile küçültür, oranı korur."""
    img.thumbnail(max_size, Image.LANCZOS)
    return img


def _image_to_base64(img: Image.Image, fmt: str = "PNG") -> str:
    """PIL Image'ı base64 string'e çevirir."""
    buf = io.BytesIO()
    img.save(buf, format=fmt, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _base64_to_image(b64_str: str) -> Image.Image:
    """base64 string'i PIL Image'a çevirir."""
    raw = base64.b64decode(b64_str)
    return Image.open(io.BytesIO(raw))


# ---------------------------------------------------------------------------
# Ana Sınıf
# ---------------------------------------------------------------------------

class StudioAIService:
    """
    ZanaatsAl Studio AI: Arka plan kaldırma + Profesyonel stüdyo ortamı oluşturma.
    """

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY bulunamadı! .env dosyasını kontrol edin.")
        genai.configure(api_key=self.api_key)

        # Görüntü anlayan ve üreten model
        self.vision_model = genai.GenerativeModel("gemini-2.5-flash")

    # ------------------------------------------------------------------
    # Adım 1: Arka Plan Silme
    # ------------------------------------------------------------------

    def remove_background(self, image_bytes: bytes) -> Image.Image:
        """
        rembg kullanarak arka planı siler ve şeffaf PNG döndürür.
        Ürünün hiçbir pikselinde oynama yapılmaz.
        """
        logger.info("🎨 rembg: Arka plan silme başlatılıyor...")
        transparent_bytes = rembg_remove(image_bytes)
        img = Image.open(io.BytesIO(transparent_bytes)).convert("RGBA")
        logger.info("✅ rembg: Arka plan başarıyla silindi.")
        return img

    # ------------------------------------------------------------------
    # Adım 2: Gemini ile Stüdyo Ortamı Ekleme
    # ------------------------------------------------------------------

    def generate_studio_image(self, transparent_img: Image.Image) -> Optional[Image.Image]:
        """
        Şeffaf PNG'yi Gemini'ye göndererek profesyonel stüdyo ortamında
        birleşik bir görsel oluşturur.
        """
        logger.info("🤖 Gemini Studio: Görsel oluşturma başlatılıyor...")

        # Boyutu sınırla
        transparent_img = _resize_if_needed(transparent_img.copy())

        # Beyaz arka plan üzerine kompozit (Gemini şeffaf PNG'yi daha iyi yorumlar)
        composite = Image.new("RGBA", transparent_img.size, (255, 255, 255, 255))
        composite.paste(transparent_img, mask=transparent_img.split()[3])
        composite_rgb = composite.convert("RGB")

        # PIL → Gemini'ye doğrudan gönder (bytes olarak)
        buf = io.BytesIO()
        composite_rgb.save(buf, format="JPEG", quality=JPEG_QUALITY)
        image_bytes = buf.getvalue()

        try:
            # Gemini görüntü + metin prompt
            response = self.vision_model.generate_content(
                [
                    STUDIO_PROMPT,
                    {
                        "mime_type": "image/jpeg",
                        "data": base64.b64encode(image_bytes).decode("utf-8"),
                    },
                ]
            )

            # Yanıtta resim varsa (Gemini image generation)
            if response.candidates:
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        if hasattr(part, "inline_data") and part.inline_data:
                            mime = part.inline_data.mime_type
                            if "image" in mime:
                                logger.info("✅ Gemini: Stüdyo görseli başarıyla oluşturuldu (inline_data).")
                                img_data = base64.b64decode(part.inline_data.data)
                                return Image.open(io.BytesIO(img_data))

            # Gemini görsel üretemedi → fallback: kompozit+renk düzeltmesi ile döndür
            logger.warning("⚠️ Gemini görsel üretmedi, fallback kompozit kullanılıyor.")
            return self._apply_studio_fallback(transparent_img)

        except Exception as e:
            logger.error(f"❌ Gemini Studio hatası: {str(e)}")
            logger.info("↩️  Fallback stüdyo kompoziti uygulanıyor...")
            return self._apply_studio_fallback(transparent_img)

    # ------------------------------------------------------------------
    # Fallback: Gemini yanıt vermezse yerel stüdyo kompoziti
    # ------------------------------------------------------------------

    def _apply_studio_fallback(self, product_rgba: Image.Image) -> Image.Image:
        """
        Gemini image generation başarısız olursa:
        - Gradient ahşap/bej arka plan
        - Soft gölge
        - Ürün üst katmanda
        """
        logger.info("🎨 Fallback stüdyo kompoziti oluşturuluyor...")
        w, h = product_rgba.size

        # Bej-krem gradyan arka plan (stüdyo zemini)
        bg = Image.new("RGB", (w, h), (245, 240, 232))

        # Hafif yatay zemin çizgileri (ahşap doku simülasyonu)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(bg)
        for y in range(0, h, max(4, h // 30)):
            alpha = 10 + (y / h) * 20
            draw.line([(0, y), (w, y)], fill=(200, 185, 165), width=1)

        # Yumuşak radial arka plan gradyanı (stüdyo ışığı)
        from PIL import ImageFilter
        spotlight = Image.new("L", (w, h), 0)
        draw_spot = ImageDraw.Draw(spotlight)
        draw_spot.ellipse(
            [(w // 4, h // 6), (3 * w // 4, 5 * h // 6)],
            fill=255,
        )
        spotlight = spotlight.filter(ImageFilter.GaussianBlur(radius=w // 3))
        spotlight_rgb = Image.merge(
            "RGB", [spotlight] * 3
        ).point(lambda x: int(x * 0.06))  # Hafif ışık vurgusu

        bg = Image.blend(bg.convert("L").convert("RGB"), bg, alpha=1.0)

        # Ürün gölgesi (tabana yerleştir)
        shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        alpha_channel = product_rgba.split()[3]
        shadow_mask = alpha_channel.filter(ImageFilter.GaussianBlur(radius=max(6, w // 50)))
        shadow_layer.paste((30, 25, 20, 120), mask=shadow_mask)
        # Gölgeyi biraz aşağı offset et
        offset_y = max(4, h // 40)
        shadow_shifted = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        shadow_shifted.paste(shadow_layer, (0, offset_y))

        # Katmanları birleştir
        result = bg.convert("RGBA")
        result = Image.alpha_composite(result, shadow_shifted)
        result = Image.alpha_composite(result, product_rgba)
        logger.info("✅ Fallback stüdyo kompoziti tamamlandı.")
        return result.convert("RGB")

    # ------------------------------------------------------------------
    # Ana Pipeline
    # ------------------------------------------------------------------

    async def process_studio_ai(self, image_bytes: bytes) -> bytes:
        """
        Tam Studio AI pipeline:
          image_bytes → arka plan sil → Gemini stüdyo → JPEG bytes

        Returns:
            bytes: Profesyonel stüdyo görselinin JPEG bytes'ı
        """
        # 1. Arka plan sil
        transparent_img = self.remove_background(image_bytes)

        # 2. Stüdyo ortamı ekle
        studio_img = self.generate_studio_image(transparent_img)

        if studio_img is None:
            raise RuntimeError("Stüdyo görseli oluşturulamadı.")

        # 3. JPEG olarak serialize et
        out_buf = io.BytesIO()
        studio_img.convert("RGB").save(out_buf, format="JPEG", quality=JPEG_QUALITY)
        return out_buf.getvalue()
