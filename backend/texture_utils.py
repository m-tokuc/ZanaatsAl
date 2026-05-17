"""
Prosedürel Doku Üretim Modülü — ZanaatsAl Studio AI (Profesyonel Sürüm)
========================================================================
numpy + PIL kullanarak gerçekçi, perspektifli ve stüdyo kalitesinde arka planlar üretir.
- 3D kütük/log yüzeyi (Doğa teması için)
- 3D mermer tezgah ve beveled perspektif kenarı
- 3D beton plaka ve beveled beton kenarı
- 3D ahşap masa panelleri
- İki katmanlı fiziksel gölge (Contact + Ambient) ve ürün kenar feathering
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops

# ──────────────────────────────────────────────────────────────────────────────
# Noise Primitives
# ──────────────────────────────────────────────────────────────────────────────

def smooth_noise(h: int, w: int, scale: int = 64) -> np.ndarray:
    sh, sw = max(2, h // scale), max(2, w // scale)
    small = np.random.rand(sh, sw).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8), "L")
    img = img.resize((w, h), Image.BILINEAR)
    img = img.filter(ImageFilter.GaussianBlur(radius=max(1, scale // 3)))
    return np.array(img, dtype=np.float32) / 255.0


def fractal_noise(h: int, w: int, octaves: int = 4, persistence: float = 0.5) -> np.ndarray:
    result = np.zeros((h, w), dtype=np.float32)
    amp, total, scale = 1.0, 0.0, 64
    for _ in range(octaves):
        result += smooth_noise(h, w, max(2, scale)) * amp
        total += amp
        amp *= persistence
        scale = max(2, scale // 2)
    return result / total


def vertical_gradient(h: int, w: int, top: float = 0.0, bottom: float = 1.0) -> np.ndarray:
    grad = np.linspace(top, bottom, h, dtype=np.float32)
    return np.tile(grad[:, None], (1, w))


def radial_highlight(h: int, w: int, cx: float, cy: float,
                     radius: float, strength: float = 0.15) -> np.ndarray:
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    dist = np.sqrt((X - cx * w) ** 2 + (Y - cy * h) ** 2)
    highlight = np.clip(1.0 - dist / (radius * max(w, h)), 0, 1)
    return highlight * strength


def apply_vignette(img_np: np.ndarray, strength: float = 0.3) -> np.ndarray:
    h, w = img_np.shape[:2]
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    max_dist = np.sqrt(cx ** 2 + cy ** 2)
    vignette = 1.0 - (dist / max_dist) * strength
    vignette = np.clip(vignette, 0, 1)
    if img_np.ndim == 3:
        vignette = vignette[:, :, None]
    return img_np * vignette


def _np_to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ──────────────────────────────────────────────────────────────────────────────
# Gelişmiş Arka Plan Üreteçleri (Görsel Derinlik ve Perspektifli)
# ──────────────────────────────────────────────────────────────────────────────

def generate_bg_studio_white(w: int, h: int, horizon_y: int) -> Image.Image:
    """Yumuşak arka duvar ve temiz zemin geçişli e-ticaret stüdyosu."""
    img = np.ones((h, w, 3), dtype=np.float32) * 246
    # Duvar ve zemin geçiş gradienti
    grad = vertical_gradient(h, w, 0.90, 1.0)
    img *= grad[:, :, None]
    
    # Merkez stüdyo softbox ışığı
    img += radial_highlight(h, w, 0.5, 0.45, 0.65, 9.0)[:, :, None]
    
    # Zemin-Duvar geçiş bandı (Horizon gölgesi)
    horizon_band = np.zeros((h, w), dtype=np.float32)
    band_h = max(10, h // 25)
    for y in range(horizon_y - band_h, horizon_y + band_h):
        if 0 <= y < h:
            t = 1.0 - abs(y - horizon_y) / band_h
            horizon_band[y, :] = t * 14
    img -= horizon_band[:, :, None]
    
    img = apply_vignette(img, 0.05)
    return _np_to_pil(img)


def generate_bg_rustic_wood(w: int, h: int, horizon_y: int) -> Image.Image:
    """Gerçekçi ahşap paneller ve perspektif çizgileri olan meşe masa yüzeyi."""
    # Arka Plan Duvarı (Koyu sıcak bej)
    bg_wall = np.zeros((h, w, 3), dtype=np.float32)
    wall_color = np.array([55, 42, 32], dtype=np.float32)
    for y in range(horizon_y):
        t = y / max(1, horizon_y)
        bg_wall[y, :, :] = wall_color * (0.65 + t * 0.35)
    
    # Masa Yüzeyi Dokusu
    table = np.zeros((h - horizon_y, w, 3), dtype=np.float32)
    wood_base = np.array([160, 115, 75], dtype=np.float32)
    wood_dark = np.array([80, 50, 30], dtype=np.float32)
    
    # Paneller halinde ahşap
    th = h - horizon_y
    panel_w = w // 4
    distortion = fractal_noise(th, w, octaves=3, persistence=0.55)
    
    for y in range(th):
        # Perspektifli grain efekti
        grain_scale = 4.0 + (y / max(1, th)) * 8.0
        grain = smooth_noise(1, w, scale=int(grain_scale))[0]
        # Panel birleşim çizgileri
        for x in range(w):
            panel_idx = x // panel_w
            line_factor = 1.0
            # Panel sınırlarına yakın hafif gölge çizgileri
            dist_to_border = min(x % panel_w, panel_w - (x % panel_w))
            if dist_to_border < 4:
                line_factor = 0.75 + (dist_to_border / 4.0) * 0.25
                
            noise_val = grain[x] * 0.5 + distortion[y, x] * 0.5
            color = wood_dark + noise_val * (wood_base - wood_dark)
            table[y, x, :] = color * line_factor
            
    # Masa yüzeyini yerleştir
    img = bg_wall
    img[horizon_y:, :, :] = table
    
    # Sıcak spot ışığı (Masa üstünde süzülen altın ışık)
    img += radial_highlight(h, w, 0.55, 0.4, 0.55, 24)[:, :, None] * np.array([1.0, 0.82, 0.48], dtype=np.float32)
    img = apply_vignette(img, 0.18)
    return _np_to_pil(img)


def generate_bg_minimal_marble(w: int, h: int, horizon_y: int) -> Image.Image:
    """3D beveled bej mermer tezgah, üst yüzey mermer damarlı, ön yüzey gölgeli."""
    # Arka Plan Duvarı (Minimal soft krem)
    img = np.zeros((h, w, 3), dtype=np.float32)
    wall_color = np.array([238, 235, 230], dtype=np.float32)
    for y in range(horizon_y):
        t = y / max(1, horizon_y)
        img[y, :, :] = wall_color * (0.92 + t * 0.08)
        
    # Mermer Tezgah Üst Yüzeyi (Horizon'dan aşağıya doğru)
    counter_h = h - horizon_y
    counter = np.ones((counter_h, w, 3), dtype=np.float32) * 242
    counter[:, :, 1] = 239
    counter[:, :, 2] = 234
    
    # Carrara Damarları (Sinüzoidal + gürültülü yollar)
    x_coords = np.linspace(0, 5 * np.pi, w)
    y_coords = np.linspace(0, 5 * np.pi, counter_h)
    X, Y = np.meshgrid(x_coords, y_coords)
    distortion = fractal_noise(counter_h, w, octaves=4, persistence=0.6)
    
    # 2 set damar sistemi
    veins1 = np.sin(X * 0.7 + Y * 1.3 + distortion * 6)
    veins1 = 1.0 - np.power(np.abs(veins1), 0.18)
    veins1 = np.clip(veins1 * 1.4 - 0.4, 0, 1)
    
    veins2 = np.sin(X * 2.2 + Y * 0.8 + distortion * 9)
    veins2 = 1.0 - np.power(np.abs(veins2), 0.22)
    veins2 = np.clip(veins2 * 1.8 - 0.8, 0, 1)
    
    veins = veins1 * 0.65 + veins2 * 0.35
    vein_color = np.array([168, 164, 172], dtype=np.float32)
    
    for c in range(3):
        counter[:, :, c] -= veins * (counter[:, :, c] - vein_color[c]) * 0.32
        
    img[horizon_y:, :, :] = counter
    
    # 3D Bevel/Kenar Efekti (Tezgahın en altındaki beveled pahlı bitiş kenarı)
    bevel_y = h - max(12, h // 25)
    if bevel_y > horizon_y:
        # Ön dikme yüzü daha koyu gölgeli
        for c in range(3):
            img[bevel_y:, :, c] *= 0.75
            
    # Mermer cilası parlaması
    img += radial_highlight(h, w, 0.45, 0.5, 0.6, 12)[:, :, None]
    img = apply_vignette(img, 0.08)
    return _np_to_pil(img)


def generate_bg_modern_concrete(w: int, h: int, horizon_y: int) -> Image.Image:
    """3D perspektif beveled beton plaka, pürüzlü dokulu."""
    img = np.ones((h, w, 3), dtype=np.float32) * 65
    
    # Duvar gradienti
    for y in range(horizon_y):
        t = y / max(1, horizon_y)
        img[y, :, :] *= (0.55 + t * 0.45)
        
    # Beton dokusu
    coarse = fractal_noise(h, w, 4, 0.58)
    fine = smooth_noise(h, w, scale=3)
    patches = smooth_noise(h, w, scale=96)
    texture = coarse * 0.45 + fine * 0.25 + patches * 0.3
    img += (texture[:, :, None] - 0.5) * 36
    
    # 3D Kenar (Bitiş pahı)
    bevel_y = h - max(14, h // 20)
    for y in range(horizon_y, h):
        if y >= bevel_y:
            img[y, :, :] *= 0.68  # Ön dik yüz gölgesi
            
    # Spot ışığı
    img += radial_highlight(h, w, 0.7, 0.3, 0.55, 18)[:, :, None]
    img = apply_vignette(img, 0.24)
    return _np_to_pil(img)


def generate_bg_nature_leaves(w: int, h: int, horizon_y: int) -> Image.Image:
    """
    Doğa Teması:
    - Arka planda gökyüzü (mavi-turkuaz gradient) ve orman bokehi
    - Ön tarafta ürünün basacağı 3D gerçekçi ahşap KÜTÜK (log slice) kesiti.
    """
    # 1. Gökyüzü ve orman yeşili bokeh arka planı
    img = np.zeros((h, w, 3), dtype=np.float32)
    sky_top = np.array([135, 185, 220], dtype=np.float32)   # Yumuşak gökyüzü mavisi
    forest_bot = np.array([45, 95, 40], dtype=np.float32)   # Orman yeşili
    for y in range(h):
        t = y / max(1, h - 1)
        img[y, :, :] = sky_top + (forest_bot - sky_top) * t
        
    # Yaprak bokehi
    rng = np.random.RandomState(88)
    bokeh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bokeh)
    for _ in range(50):
        cx = rng.randint(0, w)
        cy = rng.randint(0, int(h * 0.75))
        r = rng.randint(max(15, w // 25), max(30, w // 7))
        green = rng.randint(90, 210)
        red = rng.randint(30, 90)
        alpha = rng.randint(20, 60)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=(red, green, rng.randint(30, 80), alpha))
    bokeh = bokeh.filter(ImageFilter.GaussianBlur(radius=max(14, w // 20)))
    bokeh_np = np.array(bokeh, dtype=np.float32)
    alpha_mask = bokeh_np[:, :, 3:4] / 255.0
    img = img * (1 - alpha_mask) + bokeh_np[:, :, :3] * alpha_mask
    
    # PIL formatına dönüştürüp kütük (log) çiziyoruz
    bg_pil = _np_to_pil(img)
    draw_pil = ImageDraw.Draw(bg_pil)
    
    # 2. Ürünün basacağı 3D Kütük (Log Slice) Yüzeyi
    # Geniş bir elips çiziyoruz
    log_cx = w // 2
    log_cy = int(horizon_y + (h - horizon_y) * 0.3)
    log_rx = int(w * 0.44)
    log_ry = int((h - horizon_y) * 0.45)
    
    # Kütük halkaları (Rings)
    ring_colors = [
        (130, 95, 60),  # Dış kabuk (bark)
        (145, 110, 75),
        (185, 150, 110), # Yaş halkası açık renk
        (165, 130, 90),
        (190, 155, 115),
        (170, 135, 95),
        (195, 160, 120), # Merkez öz odun
    ]
    
    # Dıştan içe halkaları çizip blur uygulayarak iç içe halka dokusu veriyoruz
    for i, col in enumerate(ring_colors):
        factor = 1.0 - (i / len(ring_colors)) * 0.85
        cur_rx = int(log_rx * factor)
        cur_ry = int(log_ry * factor)
        
        # Her halkaya hafif bir gürültülü dalgalanma ekliyoruz ki dümdüz elips olmasın
        draw_pil.ellipse([
            log_cx - cur_rx, log_cy - cur_ry,
            log_cx + cur_rx, log_cy + cur_ry
        ], fill=col)
        
    # Kütüğü genel olarak çok az yumuşatarak bütünleştiriyoruz
    bg_np = np.array(bg_pil, dtype=np.float32)
    
    # Kütük üstüne radyal ahşap çatlakları ve radial noise ekleme (numpy ile)
    # Kütüğün elips maskesini alalım
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    elips_val = ((X - log_cx) / log_rx) ** 2 + ((Y - log_cy) / log_ry) ** 2
    log_mask = (elips_val <= 1.0).astype(np.float32)
    
    # Ahşap çatlak kanalları (radial veins)
    fractal = fractal_noise(h, w, 4, PERSISTENCE:=0.6)
    noise_rings = np.sin(np.sqrt((X - log_cx) ** 2 + (Y - log_cy) ** 2) * 0.15 + fractal * 3)
    noise_rings = np.clip(1.0 - np.abs(noise_rings), 0, 1)
    
    # Kütük dokusuna gürültüyü entegre et
    for c in range(3):
        bg_np[:, :, c] -= log_mask * noise_rings * 15 * (1.0 - elips_val * 0.3)
        
    # Golden Sunlight (Sağ üstten ormanın içine süzülen altın ışınlar)
    sun = radial_highlight(h, w, 0.78, 0.15, 0.5, 38)
    bg_np[:, :, 0] += sun * 1.0
    bg_np[:, :, 1] += sun * 0.78
    bg_np[:, :, 2] += sun * 0.28
    
    bg_np = apply_vignette(bg_np, 0.12)
    return _np_to_pil(bg_np)


def generate_bg_premium_black(w: int, h: int, horizon_y: int) -> Image.Image:
    """Mat lüks siyah yüzey, parlak neon soft spot ışıklı."""
    img = np.ones((h, w, 3), dtype=np.float32) * 11
    # Micro noise
    texture = fractal_noise(h, w, 3, 0.52)
    img += (texture[:, :, None] - 0.5) * 5
    
    # Sağ üst spotlight parlaması
    spot = radial_highlight(h, w, 0.65, 0.28, 0.45, 48)
    img += spot[:, :, None] * np.array([1.0, 0.96, 1.04], dtype=np.float32)
    
    # Horizon altı lüks parlak zemin (glossy yansıma)
    for y in range(horizon_y, h):
        t = (y - horizon_y) / max(1, h - horizon_y)
        img[y, :, :] += 7.0 * (1.0 - t)
        
    img = apply_vignette(img, 0.32)
    return _np_to_pil(img)


# ──────────────────────────────────────────────────────────────────────────────
# Background dispatcher
# ──────────────────────────────────────────────────────────────────────────────

BG_GENERATORS = {
    "studio_white": generate_bg_studio_white,
    "rustic_wood": generate_bg_rustic_wood,
    "minimal_marble": generate_bg_minimal_marble,
    "modern_concrete": generate_bg_modern_concrete,
    "nature_leaves": generate_bg_nature_leaves,
    "premium_black": generate_bg_premium_black,
}

def generate_background(bg_type: str, w: int, h: int, horizon_y: int) -> Image.Image:
    gen = BG_GENERATORS.get(bg_type, generate_bg_studio_white)
    return gen(w, h, horizon_y)


# ──────────────────────────────────────────────────────────────────────────────
# Gelişmiş Ürün Preprocessing, Ölçekleme ve Kusursuz Yerleşim (Floating Engelleme)
# ──────────────────────────────────────────────────────────────────────────────

def preprocess_product(
    product_rgba: Image.Image, target_w: int, target_h: int, horizon_y: int, bg_type: str
) -> tuple[Image.Image, tuple]:
    """
    Ürünü boş kenarlarından kırpar, ideal boyuta ölçekler,
    ve alt kenarını tam zemin/kütük çizgisine hizalayarak 'havada durma' etkisini YOK EDER.
    """
    alpha = product_rgba.split()[3]
    bbox = alpha.getbbox()
    if not bbox:
        return product_rgba, (0, 0, target_w, target_h)
        
    # Boş alanları kırp
    cropped = product_rgba.crop(bbox)
    cw, ch = cropped.size
    
    # Şablona göre ideal ölçeklendirme
    if bg_type == "nature_leaves":
        # Kütük üzerine tam oturması için biraz daha küçük (%45-50 yükseklik)
        max_scale_h = target_h * 0.48
        max_scale_w = target_w * 0.50
    else:
        max_scale_h = target_h * 0.56
        max_scale_w = target_w * 0.60
        
    scale = min(max_scale_w / cw, max_scale_h / ch)
    scaled_w = max(20, int(cw * scale))
    scaled_h = max(20, int(ch * scale))
    
    scaled = cropped.resize((scaled_w, scaled_h), Image.LANCZOS)
    
    # Yerleşim: Alt kenarı tam horizon_y veya kütük üstüne oturt
    px = (target_w - scaled_w) // 2
    
    if bg_type == "nature_leaves":
        # Kütüğün üst yüzeyine oturması için horizon_y'nin biraz altına (kütük merkezine) yerleştir
        py = int(horizon_y + (target_h - horizon_y) * 0.25 - scaled_h)
    else:
        py = horizon_y - scaled_h
        
    # Yeni kanvas üzerine yapıştır
    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    canvas.paste(scaled, (px, py))
    
    new_bbox = (px, py, px + scaled_w, py + scaled_h)
    return canvas, new_bbox


# ──────────────────────────────────────────────────────────────────────────────
# Kusursuz Gölgelendirme (Contact + Ambient Shadows)
# ──────────────────────────────────────────────────────────────────────────────

def create_contact_shadow(
    alpha: Image.Image, bbox: tuple, w: int, h: int,
    color: tuple = (10, 8, 5), opacity: int = 190
) -> Image.Image:
    """Ürünün tam tabanına basan keskin, çok ince kontakt gölgesi."""
    if not bbox:
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))
    left, top, right, bottom = bbox
    pw = right - left
    pcx = (left + right) // 2
    
    # İnce yayvan elips
    shadow_h = max(2, h // 110)
    shadow_w = int(pw * 0.88)
    
    layer = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(layer)
    draw.ellipse([
        pcx - shadow_w // 2, bottom - shadow_h,
        pcx + shadow_w // 2, bottom + shadow_h
    ], fill=opacity)
    
    # Çok az blur (gerçekçi keskinlik için)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=max(1, w // 250)))
    
    result = Image.new("RGBA", (w, h), (*color, 255))
    return Image.merge("RGBA", [*result.split()[:3], layer])


def create_ambient_shadow(
    alpha: Image.Image, w: int, h: int,
    color: tuple = (15, 12, 10), opacity: int = 65,
    blur_factor: int = 16
) -> Image.Image:
    """Alt ve arka plana yumuşakça dağılan büyük çevre gölgesi."""
    # Ürün silüetini dikeyde %55 sıkıştır
    squeezed_h = max(1, int(alpha.size[1] * 0.55))
    squeezed = alpha.resize((w, squeezed_h), Image.LANCZOS)
    
    shadow_mask = Image.new("L", (w, h), 0)
    # Alt taban seviyesine ve hafif arkaya yerleştir
    bbox = alpha.getbbox()
    if bbox:
        bottom = bbox[3]
        offset_y = bottom - squeezed_h + max(2, h // 90)
    else:
        offset_y = h - squeezed_h
        
    shadow_mask.paste(squeezed, (0, offset_y))
    
    # Geniş Gaussian blur
    blur_r = max(6, w // blur_factor)
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(radius=blur_r))
    
    # Opaklık ölçekleme
    shadow_mask = shadow_mask.point(lambda x: min(int(x * opacity / 255.0), opacity))
    
    result = Image.new("RGBA", (w, h), (*color, 255))
    return Image.merge("RGBA", [*result.split()[:3], shadow_mask])


# ──────────────────────────────────────────────────────────────────────────────
# Işık ve Renk Entegrasyonu (Image Blending & Feathering)
# ──────────────────────────────────────────────────────────────────────────────

def feather_edges(product_rgba: Image.Image, radius: float = 1.2) -> Image.Image:
    """Ürün kenarlarındaki sert pikselleri yumuşatarak arka planla birleştirir."""
    r, g, b, a = product_rgba.split()
    eroded = a.filter(ImageFilter.MinFilter(3)) # 1px içeri daralt
    blurred = eroded.filter(ImageFilter.GaussianBlur(radius=radius))
    
    # Dışarı taşmaması için orijinal maske ile çarp
    feathered = ImageChops.darker(a, blurred)
    return Image.merge("RGBA", [r, g, b, feathered])


def apply_environment_tint(
    product_rgba: Image.Image, tint_color: tuple, strength: float = 0.04
) -> Image.Image:
    """Ürüne seçilen temanın ortam rengini hafifçe yedirerek ışık uyumu sağlar."""
    r, g, b, a = product_rgba.split()
    rgb = Image.merge("RGB", [r, g, b])
    tint = Image.new("RGB", product_rgba.size, tint_color)
    blended = Image.blend(rgb, tint, strength)
    return Image.merge("RGBA", [*blended.split(), a])
