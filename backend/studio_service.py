"""
ZanaatsAl Studio AI Servisi
============================
İş Akışı:
  1. Gelen resimden rembg ile arka plan silinir → şeffaf PNG elde edilir
  2. Şeffaf PNG base64'e çevrilerek Gemini'nin görsel analiz modeline gönderilir
  3. Gemini, ürünü seçilen arka plan temasında profesyonel stüdyo ortamında
     yeniden render eder ve sonuç base64 PNG olarak döndürülür
"""

import io
import os
import base64
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Tuple

from PIL import Image
from rembg import remove as rembg_remove
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Arka Plan Şablonları
# ---------------------------------------------------------------------------

BACKGROUND_TEMPLATES: Dict[str, Dict] = {
    "studio_white": {
        "prompt": (
            "Clean, bright, professional studio white background with soft shadows. "
            "The product sits on a pure white seamless backdrop with even, diffused "
            "soft-box lighting from above. Subtle contact shadow beneath the product."
        ),
        "bg_color": (250, 250, 250),
        "line_color": (235, 235, 235),
        "shadow_rgba": (180, 180, 180, 80),
        "spotlight_strength": 0.03,
    },
    "rustic_wood": {
        "prompt": (
            "Planted on a rustic wooden table texture with warm background lighting. "
            "Rich honey-toned oak wood grain surface, warm golden-hour ambient light, "
            "soft bokeh in the background with earthy brown and amber tones."
        ),
        "bg_color": (140, 100, 60),
        "line_color": (120, 80, 45),
        "shadow_rgba": (40, 25, 10, 130),
        "spotlight_strength": 0.08,
    },
    "minimal_marble": {
        "prompt": (
            "Placed on a polished luxurious white marble countertop. "
            "Elegant Carrara marble surface with subtle grey veining, "
            "bright natural window light from the side, soft reflections on the marble."
        ),
        "bg_color": (240, 238, 235),
        "line_color": (200, 195, 190),
        "shadow_rgba": (100, 95, 90, 90),
        "spotlight_strength": 0.05,
    },
    "modern_concrete": {
        "prompt": (
            "Industrial dark grey concrete floor with soft studio rim light. "
            "Raw, polished concrete surface with subtle texture, "
            "dramatic side-lighting creating a moody, modern atmosphere. "
            "Dark charcoal gradient background."
        ),
        "bg_color": (70, 70, 75),
        "line_color": (55, 55, 60),
        "shadow_rgba": (10, 10, 12, 150),
        "spotlight_strength": 0.10,
    },
    "nature_leaves": {
        "prompt": (
            "Soft out-of-focus green tropical foliage and natural sunlight. "
            "Lush green leaves blurred in the background (heavy bokeh), "
            "warm golden sunlight rays filtering through, "
            "the product sits on a light natural wood surface."
        ),
        "bg_color": (60, 100, 55),
        "line_color": (50, 85, 45),
        "shadow_rgba": (20, 35, 15, 110),
        "spotlight_strength": 0.07,
    },
    "premium_black": {
        "prompt": (
            "Deep matte black background with high-contrast dramatic lighting. "
            "Luxurious dark backdrop, sharp studio spot-light from the top-right, "
            "elegant rim-light outlining the product edges, "
            "subtle glossy reflection on the dark surface beneath."
        ),
        "bg_color": (15, 15, 18),
        "line_color": (25, 25, 30),
        "shadow_rgba": (0, 0, 0, 160),
        "spotlight_strength": 0.12,
    },
}

# Varsayılan şablon
DEFAULT_TEMPLATE = "studio_white"

MAX_IMAGE_SIZE = (1024, 1024)   # Gemini'ye gönderilecek max boyut
JPEG_QUALITY   = 90


# ---------------------------------------------------------------------------
# Yardımcı Fonksiyonlar
# ---------------------------------------------------------------------------

def _get_template(background_type: str) -> Dict:
    """Şablon döndürür, bilinmiyorsa varsayılana döner."""
    return BACKGROUND_TEMPLATES.get(background_type, BACKGROUND_TEMPLATES[DEFAULT_TEMPLATE])


def _build_studio_prompt(background_type: str) -> str:
    """Seçilen temaya göre Gemini prompt'u oluşturur."""
    template = _get_template(background_type)
    base = (
        "Sen bir profesyonel ürün fotoğraf editörüsün. "
        "Bu resimde arka planı tamamen kaldırılmış ve yalnızca ürün görünmekte. "
        "KRİTİK KURAL: Ürünün kendi şeklini, rengini, dokusunu veya detaylarını "
        "kesinlikle değiştirme. Sadece arka planı ve ortamı ekle. "
        "Sonuç; Etsy, Amazon veya Trendyol gibi global e-ticaret platformlarında "
        "satışa hazır, profesyonel bir ürün görseli olmalı. "
        "İstenen arka plan ortamı: "
    )
    return base + template["prompt"]


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

    def generate_studio_image(
        self,
        transparent_img: Image.Image,
        background_type: str = DEFAULT_TEMPLATE,
    ) -> Optional[Image.Image]:
        """
        Şeffaf PNG'yi Gemini'ye göndererek seçilen tema ile profesyonel
        stüdyo ortamında birleşik bir görsel oluşturur.
        """
        logger.info(f"🤖 Gemini Studio: Görsel oluşturma başlatılıyor... (tema: {background_type})")

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

        # Dinamik prompt
        prompt = _build_studio_prompt(background_type)

        try:
            # Gemini görüntü + metin prompt
            response = self.vision_model.generate_content(
                [
                    prompt,
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

            # Gemini görsel üretemedi → fallback
            logger.warning("⚠️ Gemini görsel üretmedi, fallback kompozit kullanılıyor.")
            return self._apply_studio_fallback(transparent_img, background_type)

        except Exception as e:
            logger.error(f"❌ Gemini Studio hatası: {str(e)}")
            logger.info("↩️  Fallback stüdyo kompoziti uygulanıyor...")
            return self._apply_studio_fallback(transparent_img, background_type)

    # ------------------------------------------------------------------
    # Fallback: Gemini yanıt vermezse yerel stüdyo kompoziti
    # ------------------------------------------------------------------

    def _apply_studio_fallback(
        self,
        product_rgba: Image.Image,
        background_type: str = DEFAULT_TEMPLATE,
    ) -> Image.Image:
        """
        Gemini image generation başarısız olursa:
        - Seçilen temaya uygun gradient arka plan
        - Soft gölge
        - Ürün üst katmanda
        """
        template = _get_template(background_type)
        logger.info(f"🎨 Fallback stüdyo kompoziti oluşturuluyor... (tema: {background_type})")
        w, h = product_rgba.size

        bg_color = template["bg_color"]
        line_color = template["line_color"]
        shadow_rgba = template["shadow_rgba"]
        spotlight_strength = template["spotlight_strength"]

        # Düz renkli arka plan
        bg = Image.new("RGB", (w, h), bg_color)

        # Hafif yatay zemin çizgileri (doku simülasyonu)
        from PIL import ImageDraw, ImageFilter
        draw = ImageDraw.Draw(bg)
        step = max(4, h // 30)
        for y in range(0, h, step):
            draw.line([(0, y), (w, y)], fill=line_color, width=1)

        # Yumuşak radial arka plan gradyanı (stüdyo ışığı)
        spotlight = Image.new("L", (w, h), 0)
        draw_spot = ImageDraw.Draw(spotlight)
        draw_spot.ellipse(
            [(w // 4, h // 6), (3 * w // 4, 5 * h // 6)],
            fill=255,
        )
        spotlight = spotlight.filter(ImageFilter.GaussianBlur(radius=max(1, w // 3)))

        # Işık vurgusunu arka plana ekle
        spot_layer = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        spot_alpha = spotlight.point(lambda x: int(x * spotlight_strength))
        spot_layer.putalpha(spot_alpha)
        bg_rgba = bg.convert("RGBA")
        bg_rgba = Image.alpha_composite(bg_rgba, spot_layer)

        # Ürün gölgesi (tabana yerleştir)
        shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        alpha_channel = product_rgba.split()[3]
        shadow_mask = alpha_channel.filter(
            ImageFilter.GaussianBlur(radius=max(6, w // 50))
        )
        shadow_layer.paste(shadow_rgba, mask=shadow_mask)

        # Gölgeyi biraz aşağı offset et
        offset_y = max(4, h // 40)
        shadow_shifted = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        shadow_shifted.paste(shadow_layer, (0, offset_y))

        # Katmanları birleştir
        result = Image.alpha_composite(bg_rgba, shadow_shifted)
        result = Image.alpha_composite(result, product_rgba)
        logger.info("✅ Fallback stüdyo kompoziti tamamlandı.")
        return result.convert("RGB")

    # ------------------------------------------------------------------
    # Ana Pipeline
    # ------------------------------------------------------------------

    async def process_studio_ai(
        self,
        image_bytes: bytes,
        background_type: str = DEFAULT_TEMPLATE,
    ) -> bytes:
        """
        Tam Studio AI pipeline:
          image_bytes → arka plan sil → Gemini stüdyo → JPEG bytes

        Args:
            image_bytes: Orijinal ürün görseli (bytes)
            background_type: Seçilen arka plan şablon ID'si

        Returns:
            bytes: Profesyonel stüdyo görselinin JPEG bytes'ı
        """
        # 1. Arka plan sil
        transparent_img = self.remove_background(image_bytes)

        # 2. Stüdyo ortamı ekle (seçilen temaya göre)
        studio_img = self.generate_studio_image(transparent_img, background_type)

        if studio_img is None:
            raise RuntimeError("Stüdyo görseli oluşturulamadı.")

        # 3. JPEG olarak serialize et
        out_buf = io.BytesIO()
        studio_img.convert("RGB").save(out_buf, format="JPEG", quality=JPEG_QUALITY)
        return out_buf.getvalue()
