"""
ZanaatsAl Studio AI Servisi — Profesyonel Kalite Sürümü
=========================================================
Pipeline:
  1. rembg ile arka plan silinir → şeffaf PNG
  2. Gemini'ye inpainting tarzı prompt gönderilir
  3. Başarısız olursa profesyonel PIL kompozit:
     - Ürün kenarları kırpılır, ideal ölçekte 3D zemine/kütüğe yerleştirilir
     - Gerçekçi prosedürel 3D arka planlar (numpy noise textures)
     - Çift katmanlı gölge (contact + ambient)
     - Kenar yumuşatma (feathering)
     - Ortam renk uyumu (environment tinting)
"""

import io
import os
import base64
import logging
from typing import Optional, Dict

# pyrefly: ignore [missing-import]
from PIL import Image, ImageFilter
from rembg import remove as rembg_remove
from dotenv import load_dotenv
import google.generativeai as genai

from texture_utils import (
    generate_background,
    preprocess_product,
    create_contact_shadow,
    create_ambient_shadow,
    feather_edges,
    apply_environment_tint,
)

load_dotenv()
logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE = (1024, 1024)
JPEG_QUALITY = 95
DEFAULT_TEMPLATE = "studio_white"

# ---------------------------------------------------------------------------
# Şablon Tanımları (Gemini Prompt & Fallback Blending Ayarları)
# ---------------------------------------------------------------------------
BACKGROUND_TEMPLATES: Dict[str, Dict] = {
    "studio_white": {
        "prompt": (
            "Clean, bright, professional e-commerce studio. Pure white seamless "
            "backdrop and surface. Even diffused soft-box lighting from above. "
            "Natural contact shadow beneath the product. "
            "The product was photographed in this setting."
        ),
        "tint_color": (255, 252, 245),
        "tint_strength": 0.025,
        "shadow_color": (100, 100, 105),
        "contact_opacity": 160,
        "ambient_opacity": 45,
        "ambient_blur": 18,
    },
    "rustic_wood": {
        "prompt": (
            "Product naturally sitting on a rustic honey-toned oak wood table. "
            "Rich wood grain texture visible. Warm golden-hour ambient light "
            "from the left side. Soft bokeh background with earthy brown tones. "
            "Realistic contact shadow on the wood surface."
        ),
        "tint_color": (220, 185, 130),
        "tint_strength": 0.045,
        "shadow_color": (40, 25, 10),
        "contact_opacity": 190,
        "ambient_opacity": 65,
        "ambient_blur": 16,
    },
    "minimal_marble": {
        "prompt": (
            "Product placed on a polished Carrara marble countertop. "
            "Elegant white marble with subtle grey veining. Bright natural "
            "window light from the right side. Soft reflections on the "
            "polished marble surface. Minimal, luxurious atmosphere."
        ),
        "tint_color": (245, 242, 238),
        "tint_strength": 0.03,
        "shadow_color": (95, 90, 88),
        "contact_opacity": 155,
        "ambient_opacity": 50,
        "ambient_blur": 18,
    },
    "modern_concrete": {
        "prompt": (
            "Product on a raw polished concrete surface. Dark charcoal grey "
            "concrete with visible aggregate texture. Dramatic studio rim "
            "light from the top-right creating moody atmosphere. "
            "Industrial, modern editorial photography style."
        ),
        "tint_color": (140, 145, 155),
        "tint_strength": 0.035,
        "shadow_color": (8, 8, 10),
        "contact_opacity": 200,
        "ambient_opacity": 70,
        "ambient_blur": 15,
    },
    "nature_leaves": {
        "prompt": (
            "Product placed on a rustic tree log slice in a lush forest. "
            "Lush out-of-focus tropical foliage and soft bokeh in the background. "
            "Warm golden sun rays filtering through forest leaves. "
            "Natural, organic, eco-friendly professional product photography."
        ),
        "tint_color": (175, 210, 145),
        "tint_strength": 0.045,
        "shadow_color": (20, 32, 12),
        "contact_opacity": 175,
        "ambient_opacity": 60,
        "ambient_blur": 16,
    },
    "premium_black": {
        "prompt": (
            "Product on a glossy deep black surface. Matte black backdrop "
            "with dramatic high-contrast spot-light from the top-right. "
            "Elegant rim-light outlining the product edges. Subtle glossy "
            "reflection on the dark surface beneath. Luxury editorial style."
        ),
        "tint_color": (200, 210, 230),
        "tint_strength": 0.03,
        "shadow_color": (0, 0, 0),
        "contact_opacity": 220,
        "ambient_opacity": 80,
        "ambient_blur": 14,
    },
}


def _get_template(bg_type: str) -> Dict:
    return BACKGROUND_TEMPLATES.get(bg_type, BACKGROUND_TEMPLATES[DEFAULT_TEMPLATE])


def _build_inpainting_prompt(bg_type: str) -> str:
    t = _get_template(bg_type)
    return (
        "You are a world-class product photography compositor. "
        "TASK: The input image shows a product isolated on a white background. "
        "REPLACE ONLY the background. Keep the product PIXEL-PERFECT UNCHANGED. "
        "Think of this as INPAINTING — the product is the protected mask. "
        "Build the environment AROUND it with physically accurate shadows, "
        "reflections, and lighting that match the product's perspective. "
        f"ENVIRONMENT: {t['prompt']} "
        "CRITICAL: Do NOT modify the product's shape, color, texture, "
        "stitching, or any detail. The result must look like a real studio "
        "photograph, indistinguishable from an actual photo shoot. "
        "Apply photorealistic lighting adjustments to seamlessly blend the product into the new background. "
        "Generate soft, realistic contact shadows that ground the object perfectly on the surface. "
        "Ensure there is no gap between the object and its generated shadow to eliminate the floating effect."
    )


def _resize_if_needed(img: Image.Image) -> Image.Image:
    img.thumbnail(MAX_IMAGE_SIZE, Image.LANCZOS)
    return img


# ---------------------------------------------------------------------------
# Ana Sınıf
# ---------------------------------------------------------------------------
class StudioAIService:

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY bulunamadı! .env dosyasını kontrol edin.")
        genai.configure(api_key=self.api_key)
        self.vision_model = genai.GenerativeModel("gemini-2.5-flash")

    # ── Adım 1: Arka Plan Silme ─────────────────────────────────────────
    def remove_background(self, image_bytes: bytes) -> Image.Image:
        logger.info("🎨 rembg: Arka plan silme başlatılıyor...")
        transparent_bytes = rembg_remove(image_bytes)
        img = Image.open(io.BytesIO(transparent_bytes)).convert("RGBA")
        logger.info("✅ rembg: Arka plan başarıyla silindi.")
        return img

    # ── Adım 2: Gemini Inpainting ──────────────────────────────────────
    def generate_studio_image(
        self, transparent_img: Image.Image, bg_type: str = DEFAULT_TEMPLATE
    ) -> Optional[Image.Image]:
        logger.info(f"🤖 Gemini Studio: Inpainting başlatılıyor (tema: {bg_type})")
        transparent_img = _resize_if_needed(transparent_img.copy())

        # Beyaz zemin üzerine composite → Gemini'ye gönder
        comp = Image.new("RGBA", transparent_img.size, (255, 255, 255, 255))
        comp.paste(transparent_img, mask=transparent_img.split()[3])
        comp_rgb = comp.convert("RGB")

        buf = io.BytesIO()
        comp_rgb.save(buf, format="JPEG", quality=JPEG_QUALITY)
        img_bytes = buf.getvalue()

        prompt = _build_inpainting_prompt(bg_type)

        import concurrent.futures

        def _call_gemini():
            return self.vision_model.generate_content([
                prompt,
                {"mime_type": "image/jpeg",
                 "data": base64.b64encode(img_bytes).decode("utf-8")},
            ])

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_call_gemini)
                try:
                    response = future.result(timeout=30)  # 30s timeout — ağ sorunlarına karşı
                except concurrent.futures.TimeoutError:
                    logger.warning("⚠️ Gemini 30s timeout → profesyonel fallback")
                    return self._professional_composite(transparent_img, bg_type)

            if response.candidates:
                for cand in response.candidates:
                    for part in cand.content.parts:
                        if hasattr(part, "inline_data") and part.inline_data:
                            if "image" in part.inline_data.mime_type:
                                logger.info("✅ Gemini: Inpainting başarılı.")
                                data = base64.b64decode(part.inline_data.data)
                                return Image.open(io.BytesIO(data))

            logger.warning("⚠️ Gemini görsel üretmedi → profesyonel fallback")
            return self._professional_composite(transparent_img, bg_type)

        except Exception as e:
            logger.error(f"❌ Gemini hatası: {e}")
            return self._professional_composite(transparent_img, bg_type)

    # ── Profesyonel Fallback Composite ──────────────────────────────────
    def _professional_composite(
        self, product_rgba: Image.Image, bg_type: str = DEFAULT_TEMPLATE
    ) -> Image.Image:
        """
        Profesyonel seviye PIL kompozit:
        1. Ürün boş kenarlarından kırpılır ve ideal boyutta 3D zemine/kütüğe yerleştirilir.
        2. Gerçekçi 3D arka plan (doğada kütük, mermerde 3D beveled tezgah) üretilir.
        3. Contact shadow (alt temasta keskin, ince koyuluk) oluşturulur.
        4. Ambient shadow (yumuşak, dikey sıkıştırılmış çevre gölgesi) oluşturulur.
        5. Kenar yumuşatma (feathering) ile sert pikseller giderilir.
        6. Ortam renk tinti ile çanta ve ortam ışığı entegre edilir.
        """
        template = _get_template(bg_type)
        w, h = product_rgba.size

        logger.info(f"🎨 Profesyonel kompozit pipeline tetiklendi (tema: {bg_type})")

        # Horizon seviyesini belirle
        horizon_y = int(h * 0.58)

        # 1) Ürünü ideal ölçekte zemin/kütük üzerine yerleştir (Floating YOK EDİLDİ)
        logger.info("  → Ürün konumlandırma ve ölçekleme...")
        placed_product, new_bbox = preprocess_product(
            product_rgba, w, h, bg_type
        )
        
        placed_alpha = placed_product.split()[3]

        # 2) Doku ve 3D Perspektif Arka Planını oluştur
        logger.info("  → Arka plan dokusu üretiliyor...")
        background = generate_background(bg_type, w, h, horizon_y)

        # 3) Kenar feathering uygula
        logger.info("  → Kenar feathering...")
        product_ready = feather_edges(placed_product, radius=1.2)

        # 4) Ortam renk uyumu filtresi uygula
        logger.info("  → Ortam renk uyumu tinti...")
        product_ready = apply_environment_tint(
            product_ready,
            template["tint_color"],
            template["tint_strength"],
        )

        # 5) Contact shadow oluştur (Tam yeni oturtulan taban konumunda)
        logger.info("  → Contact shadow...")
        contact = create_contact_shadow(
            placed_alpha, new_bbox, w, h,
            color=template["shadow_color"],
            opacity=template["contact_opacity"],
        )

        # 6) Ambient shadow oluştur (Hafif dikey yayılmış, yumuşak)
        logger.info("  → Ambient shadow...")
        ambient = create_ambient_shadow(
            placed_alpha, w, h,
            color=template["shadow_color"],
            opacity=template["ambient_opacity"],
            blur_factor=template["ambient_blur"],
        )

        # 7) Katmanları mükemmel fiziksel sırada birleştir: bg → ambient → contact → product
        logger.info("  → Katmanlar birleştiriliyor...")
        result = background.convert("RGBA")
        result = Image.alpha_composite(result, ambient)
        result = Image.alpha_composite(result, contact)
        result = Image.alpha_composite(result, product_ready)

        logger.info("✅ Profesyonel kompozit başarıyla tamamlandı.")
        return result.convert("RGB")

    # ── Ana Pipeline ────────────────────────────────────────────────────
    async def process_studio_ai(
        self, image_bytes: bytes, background_type: str = DEFAULT_TEMPLATE
    ) -> bytes:
        transparent_img = self.remove_background(image_bytes)
        studio_img = self.generate_studio_image(transparent_img, background_type)
        if studio_img is None:
            raise RuntimeError("Stüdyo görseli oluşturulamadı.")
        out = io.BytesIO()
        studio_img.convert("RGB").save(out, format="JPEG", quality=JPEG_QUALITY)
        return out.getvalue()
