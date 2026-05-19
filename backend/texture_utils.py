"""
ZanaatsAl Studio AI — Gelişmiş Kompozit ve Doku Motoru (Sürüm 3.0)
===================================================================
Tüm yapay ve kötü duran numpy noise/prosedürel çizim kodları depreke edilmiş,
yerine profesyonel ve yüksek çözünürlüklü stüdyo arka plan şablonlarını (PNG)
kullanan ve ürünü zeminlerine kusursuz yerleştiren sistem getirilmiştir.

Özellikler:
  1. Yüksek çözünürlüklü premium şablon yükleyici (`generate_background`).
  2. Floating (havada asılı kalma) önleyici ölçekleme ve 3D zemin hizalama (`preprocess_product`).
  3. Çift katmanlı fiziksel gölge motoru (İnce contact shadow + geniş ambient bloom shadow).
  4. Kenar feathering ve ortam ışığı renk entegrasyonu (apply_environment_tint).
"""

import os
import logging
from PIL import Image, ImageDraw, ImageFilter, ImageChops

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 1. Premium Şablon Yükleyici (Prosedürel gürültü tamamen silindi)
# ──────────────────────────────────────────────────────────────────────────────

def generate_background(bg_type: str, w: int, h: int, horizon_y: int = 0) -> Image.Image:
    """
    Backend/assets/studio_bases/ altındaki yüksek çözünürlüklü, perspective ve
    profesyonel ışıklandırması olan gerçek arka plan şablonunu yükler ve ölçekler.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "assets", "studio_bases", f"{bg_type}.png")
    
    logger.info(f"📂 Arka plan şablonu yükleniyor: {file_path}")
    
    if os.path.exists(file_path):
        try:
            bg = Image.open(file_path).convert("RGB")
            # Hedef ekran boyutuna LANCZOS ile yüksek kalitede ölçekle
            return bg.resize((w, h), Image.LANCZOS)
        except Exception as e:
            logger.error(f"❌ Şablon yüklenirken hata oluştu: {e}")
            
    # Dosya yoksa veya hata oluştuysa yedek profesyonel bej/gri softbox arka planı
    logger.warning("⚠️ Şablon bulunamadı, fallback düz arka plan oluşturuluyor.")
    fallback = Image.new("RGB", (w, h), (242, 241, 238))
    draw = ImageDraw.Draw(fallback)
    # Yumuşak bir dikey degrade uygula
    for y in range(h):
        t = y / max(1, h - 1)
        gray = int(245 - t * 15)
        draw.line([(0, y), (w, y)], fill=(gray, gray - 2, gray - 5))
    return fallback


# ──────────────────────────────────────────────────────────────────────────────
# 2. Ürün Ön-İşleme ve Kusursuz 3D Zemin Hizalama (No Floating)
# ──────────────────────────────────────────────────────────────────────────────

def preprocess_product(
    product_rgba: Image.Image, target_w: int, target_h: int, bg_type: str
) -> tuple[Image.Image, tuple]:
    """
    Ürünü boş kenarlarından kırpar, sahneye göre ideal oranda ölçekler,
    ve alt kenarını şablonlardaki kütük/tezgah üst yüzeylerine piksel hassasiyetinde
    hizalayıp yerleştirir. Havada durma/asılı kalma görüntüsünü tamamen YOK eder.
    """
    alpha = product_rgba.split()[3]
    
    # Transparan kirli piksellerin (rembg kalıntıları) hizalamayı bozmasını önlemek için 
    # alfa değeri 35'ten büyük olan piksellere göre akıllı bbox hesapla
    mask = alpha.point(lambda p: 255 if p > 35 else 0)
    bbox = mask.getbbox()
    if not bbox:
        bbox = alpha.getbbox()
    if not bbox:
        return product_rgba, (0, 0, target_w, target_h)
        
    # Kenar boşluklarını kırp
    cropped = product_rgba.crop(bbox)
    cw, ch = cropped.size
    
    # Şablon bazlı hizalama ve ölçek katsayıları
    # y_ratio: Ürünün alt kenarının oturacağı zemin yükseklik oranı (0.0 - 1.0)
    # x_ratio: Ürünün yatayda yerleşeceği merkez oranı (0.0 - 1.0)
    # scale_ratio: Ürünün dikeyde sahneye oranla kaplayacağı ideal yükseklik payı
    alignments = {
        "studio_white": {"y_ratio": 0.74, "scale_ratio": 0.55, "x_ratio": 0.50},
        "rustic_wood": {"y_ratio": 0.76, "scale_ratio": 0.50, "x_ratio": 0.47},     # Ahşap masanın açısına göre hafif sol-merkez
        "minimal_marble": {"y_ratio": 0.74, "scale_ratio": 0.48, "x_ratio": 0.50},   # Mermer tezgahın üst yüzeyi
        "modern_concrete": {"y_ratio": 0.72, "scale_ratio": 0.48, "x_ratio": 0.42},  # Beton bloğun tam üst düzlüğüne (sola) otursun
        "nature_leaves": {"y_ratio": 0.75, "scale_ratio": 0.42, "x_ratio": 0.50},    # Kütüğün (log slice) üst yüzeyi
        "premium_black": {"y_ratio": 0.76, "scale_ratio": 0.45, "x_ratio": 0.50},    # Premium siyah bloğun üst yüzeyi
    }
    
    align = alignments.get(bg_type, alignments["studio_white"])
    y_ratio = align["y_ratio"]
    x_ratio = align.get("x_ratio", 0.50)
    scale_ratio = align["scale_ratio"]
    
    # En-boy oranını bozmadan ölçekle
    max_h = target_h * scale_ratio
    max_w = target_w * 0.52
    scale = min(max_w / cw, max_h / ch)
    
    sw = max(20, int(cw * scale))
    sh = max(20, int(ch * scale))
    scaled = cropped.resize((sw, sh), Image.LANCZOS)
    
    # Konum hesapla (x_ratio ile dinamik yatay hizalama)
    px = int(target_w * x_ratio) - sw // 2
    py = int(target_h * y_ratio) - sh
    
    # Yeni kanvasa yapıştır
    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    canvas.paste(scaled, (px, py))
    
    new_bbox = (px, py, px + sw, py + sh)
    logger.info(f"🎯 Ürün hizalandı ({bg_type}): bbox={new_bbox}, scale={scale:.2f}, x_ratio={x_ratio}")
    return canvas, new_bbox


# ──────────────────────────────────────────────────────────────────────────────
# 3. İki Katmanlı Fiziksel Gölgelendirme (Contact + Ambient)
# ──────────────────────────────────────────────────────────────────────────────

def create_contact_shadow(
    alpha: Image.Image, bbox: tuple, w: int, h: int,
    color: tuple = (12, 10, 8), opacity: int = 195
) -> Image.Image:
    """
    Ürünün tam altına, zemine bastığı çizgiye keskin, ince ve koyu
    bir kontakt gölgesi (contact shadow) ekler.
    """
    # Transparan kirli pikselleri eleyerek tam temizlenmiş alt sınırı bul
    clean_alpha = alpha.point(lambda p: 255 if p > 35 else 0)
    clean_bbox = clean_alpha.getbbox()
    if not clean_bbox:
        clean_bbox = bbox
    if not clean_bbox:
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))
        
    left, top, right, bottom = clean_bbox
    pw = right - left
    pcx = (left + right) // 2
    
    # Çok ince, basık bir elips
    shadow_h = max(2, h // 110)
    shadow_w = int(pw * 0.88)
    
    layer = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(layer)
    draw.ellipse([
        pcx - shadow_w // 2, bottom - shadow_h,
        pcx + shadow_w // 2, bottom + shadow_h
    ], fill=opacity)
    
    # Hafif kenar yumuşatması (aşırı yapay durmasın diye küçük blur)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=max(1, w // 220)))
    
    result = Image.new("RGBA", (w, h), (*color, 255))
    return Image.merge("RGBA", [*result.split()[:3], layer])


def create_ambient_shadow(
    alpha: Image.Image, w: int, h: int,
    color: tuple = (15, 12, 10), opacity: int = 65,
    blur_factor: int = 16
) -> Image.Image:
    """
    Ürünün altına ve arkasına doğru yumuşakça süzülen,
    dikey daraltılmış ve yoğun Gaussian blur uygulanmış çevre gölgesi (ambient shadow).
    """
    # Transparan kirli pikselleri temizle
    clean_alpha = alpha.point(lambda p: 255 if p > 35 else 0)
    
    # Silüeti dikeyde %50 sıkıştır
    squeezed_h = max(1, int(clean_alpha.size[1] * 0.50))
    squeezed = clean_alpha.resize((w, squeezed_h), Image.LANCZOS)
    
    shadow_mask = Image.new("L", (w, h), 0)
    bbox = clean_alpha.getbbox()
    if bbox:
        bottom = bbox[3]
        # Ürünün hemen arkasına düşecek şekilde milimetrik hizalı kaydırma offseti
        offset_y = bottom - squeezed_h + max(1, h // 180)
    else:
        offset_y = h - squeezed_h
        
    shadow_mask.paste(squeezed, (0, offset_y))
    
    # Geniş Gaussian blur ile yayılım sağla
    blur_r = max(5, w // blur_factor)
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(radius=blur_r))
    
    # Opaklığı ayarla
    shadow_mask = shadow_mask.point(lambda x: min(int(x * opacity / 255.0), opacity))
    
    result = Image.new("RGBA", (w, h), (*color, 255))
    return Image.merge("RGBA", [*result.split()[:3], shadow_mask])


# ──────────────────────────────────────────────────────────────────────────────
# 4. Işık ve Kenar Entegrasyonu (Feathering & Color Blending)
# ──────────────────────────────────────────────────────────────────────────────

def feather_edges(product_rgba: Image.Image, radius: float = 1.2) -> Image.Image:
    """
    Arka planı silinmiş ürünün kenarlarındaki sert kesim izlerini (dekupe hatalarını)
    hafifçe içeri eriterek pürüzsüzleştirir. Ürünün alt kısmını (zemine basan tarafı)
    masanın/kütüğün bokeh/DoF (alan derinliği) seviyesiyle bütünleşecek şekilde ekstra yumuşatır.
    """
    r, g, b, a = product_rgba.split()
    
    # Genel kenar yumuşatma
    eroded = a.filter(ImageFilter.MinFilter(3))
    blurred = eroded.filter(ImageFilter.GaussianBlur(radius=radius))
    feathered = ImageChops.darker(a, blurred)
    
    # Taban geçiş yumuşatma (DoF Entegrasyonu):
    # Ürünün alt %15'lik kısmını zemine yedirmek için degrade yumuşatma maskesi uygula
    w, h = product_rgba.size
    mask = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(mask)
    
    # Alt tarafta yumuşak bir dikey degrade maske oluştur
    bbox = feathered.getbbox()
    if bbox:
        bottom = bbox[3]
        fade_start = int(bottom - h * 0.08)
        for y in range(fade_start, bottom + 1):
            if y >= h or y < 0:
                continue
            factor = (y - fade_start) / max(1, bottom - fade_start)
            # Alt kenara yaklaştıkça hafif şeffaflık erimesi (blend)
            val = int(255 - factor * 45)
            draw.line([(0, y), (w, y)], fill=val)
            
    final_alpha = ImageChops.darker(feathered, mask)
    
    # Alt kenarı ekstradan çok hafif Gaussian blur ile odağa uydur
    base_product = Image.merge("RGBA", [r, g, b, final_alpha])
    bottom_blur = base_product.filter(ImageFilter.GaussianBlur(radius=0.85))
    
    # Sadece alt kısımları bulanık olanla değiştir
    if bbox:
        bottom = bbox[3]
        fade_start = int(bottom - h * 0.06)
        gradient_mask = Image.new("L", (w, h), 0)
        g_draw = ImageDraw.Draw(gradient_mask)
        for y in range(fade_start, bottom + 1):
            if y >= h or y < 0:
                continue
            factor = (y - fade_start) / max(1, bottom - fade_start)
            val = int(factor * 255)
            g_draw.line([(0, y), (w, y)], fill=val)
        return Image.composite(bottom_blur, base_product, gradient_mask)
        
    return base_product


def apply_environment_tint(
    product_rgba: Image.Image, tint_color: tuple, strength: float = 0.04
) -> Image.Image:
    """
    Ortamın ışık rengini, parlaklığını ve kontrastını ürünün üzerine akıllıca yedirir.
    Böylece ürün stüdyo ışığıyla mükemmel şekilde kaynaşarak "gerçekten oradaymış" gibi durur.
    """
    r, g, b, a = product_rgba.split()
    rgb = Image.merge("RGB", [r, g, b])
    
    # 1) Ortam Renk Entegrasyonu (Tinting)
    tint = Image.new("RGB", product_rgba.size, tint_color)
    blended_rgb = Image.blend(rgb, tint, strength)
    
    # 2) Gelişmiş Ortam Kontrastı ve Sıcaklığı (PIL ImageEnhance ile)
    from PIL import ImageEnhance
    
    # Ahşap/Doğa gibi sıcak/loş ortamlarda kontrastı hafifçe yumuşat ve renkleri ısıt
    # (Bu sayede yapay parlaklık ve keskin stüdyo flaşı hissi ortadan kalkar)
    brightness_enhancer = ImageEnhance.Brightness(blended_rgb)
    # Çok hafif loşlaştırma (ortam ışığına entegre)
    blended_rgb = brightness_enhancer.enhance(0.97)
    
    contrast_enhancer = ImageEnhance.Contrast(blended_rgb)
    # Kontrastı %8 yumuşatarak yapay montaj görünümünü sil
    blended_rgb = contrast_enhancer.enhance(0.92)
    
    color_enhancer = ImageEnhance.Color(blended_rgb)
    # Sıcak tonları desteklemek için doygunluğu milimetrik artır
    blended_rgb = color_enhancer.enhance(1.03)
    
    return Image.merge("RGBA", [*blended_rgb.split(), a])
