from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import colorsys
import math

app = FastAPI(title="Color Models Converter")


class CMYKColor(BaseModel):
    """Модель CMYK цвета"""
    c: float  # Cyan (0-100)
    m: float  # Magenta (0-100)
    y: float  # Yellow (0-100)
    k: float  # Key/Black (0-100)


class RGBColor(BaseModel):
    """Модель RGB цвета"""
    r: int  # Red (0-255)
    g: int  # Green (0-255)
    b: int  # Blue (0-255)


class HLSColor(BaseModel):
    """Модель HLS цвета"""
    h: float  # Hue (0-360)
    l: float  # Lightness (0-100)
    s: float  # Saturation (0-100)


def cmyk_to_rgb(c: float, m: float, y: float, k: float) -> tuple[int, int, int]:
    """
    Преобразование CMYK в RGB
    
    CMYK - субтрактивная модель (для печати)
    RGB - аддитивная модель (для экранов)
    
    Формулы:
    R = 255 × (1 - C) × (1 - K)
    G = 255 × (1 - M) × (1 - K)
    B = 255 × (1 - Y) × (1 - K)
    """
    # Преобразуем проценты в диапазон 0-1
    c = c / 100.0
    m = m / 100.0
    y = y / 100.0
    k = k / 100.0
    
    # Применяем формулу преобразования
    r = int(255 * (1 - c) * (1 - k))
    g = int(255 * (1 - m) * (1 - k))
    b = int(255 * (1 - y) * (1 - k))
    
    # Ограничиваем значения диапазоном 0-255
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    
    return r, g, b


def rgb_to_cmyk(r: int, g: int, b: int) -> tuple[float, float, float, float]:
    """
    Преобразование RGB в CMYK
    
    Формулы:
    K = 1 - max(R, G, B) / 255
    C = (1 - R/255 - K) / (1 - K)
    M = (1 - G/255 - K) / (1 - K)
    Y = (1 - B/255 - K) / (1 - K)
    """
    # Нормализуем RGB в диапазон 0-1
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0
    
    # Вычисляем K (черный компонент)
    k = 1 - max(r_norm, g_norm, b_norm)
    
    # Особый случай: если цвет чисто черный
    if k == 1.0:
        return 0.0, 0.0, 0.0, 100.0
    
    # Вычисляем C, M, Y
    c = (1 - r_norm - k) / (1 - k)
    m = (1 - g_norm - k) / (1 - k)
    y = (1 - b_norm - k) / (1 - k)
    
    # Переводим в проценты
    return c * 100, m * 100, y * 100, k * 100


def rgb_to_hls(r: int, g: int, b: int) -> tuple[float, float, float]:
    """
    Преобразование RGB в HLS
    
    HLS (Hue, Lightness, Saturation) - цилиндрическая модель
    Использует встроенную функцию Python colorsys
    
    H - тон (цвет на цветовом круге, 0-360°)
    L - светлота (0-100%)
    S - насыщенность (0-100%)
    """
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0
    
    h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)
    
    h = h * 360  # Hue в градусы (0-360)
    l = l * 100  # Lightness в проценты (0-100)
    s = s * 100  # Saturation в проценты (0-100)
    
    return h, l, s


def hls_to_rgb(h: float, l: float, s: float) -> tuple[int, int, int]:
    """
    Преобразование HLS в RGB
    
    Использует встроенную функцию Python colorsys
    """
    h_norm = h / 360.0  # Hue в диапазон 0-1
    l_norm = l / 100.0  # Lightness в диапазон 0-1
    s_norm = s / 100.0  # Saturation в диапазон 0-1
    
    r, g, b = colorsys.hls_to_rgb(h_norm, l_norm, s_norm)
    
    # Преобразуем обратно в 0-255
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    
    return r, g, b


@app.get("/")
async def read_root():
    """Главная страница приложения"""
    return FileResponse("static/index.html")


@app.post("/convert/cmyk_to_all")
async def convert_cmyk_to_all(color: CMYKColor):
    """
    Преобразование CMYK во все остальные модели
    """
    # CMYK -> RGB
    r, g, b = cmyk_to_rgb(color.c, color.m, color.y, color.k)
    
    # RGB -> HLS
    h, l, s = rgb_to_hls(r, g, b)
    
    return {
        "cmyk": {"c": color.c, "m": color.m, "y": color.y, "k": color.k},
        "rgb": {"r": r, "g": g, "b": b},
        "hls": {"h": round(h, 2), "l": round(l, 2), "s": round(s, 2)}
    }


@app.post("/convert/rgb_to_all")
async def convert_rgb_to_all(color: RGBColor):
    """
    Преобразование RGB во все остальные модели
    """
    # RGB -> CMYK
    c, m, y, k = rgb_to_cmyk(color.r, color.g, color.b)
    
    # RGB -> HLS
    h, l, s = rgb_to_hls(color.r, color.g, color.b)
    
    return {
        "cmyk": {"c": round(c, 2), "m": round(m, 2), "y": round(y, 2), "k": round(k, 2)},
        "rgb": {"r": color.r, "g": color.g, "b": color.b},
        "hls": {"h": round(h, 2), "l": round(l, 2), "s": round(s, 2)}
    }


@app.post("/convert/hls_to_all")
async def convert_hls_to_all(color: HLSColor):
    """
    Преобразование HLS во все остальные модели
    """
    # HLS -> RGB
    r, g, b = hls_to_rgb(color.h, color.l, color.s)
    
    # RGB -> CMYK
    c, m, y, k = rgb_to_cmyk(r, g, b)
    
    return {
        "cmyk": {"c": round(c, 2), "m": round(m, 2), "y": round(y, 2), "k": round(k, 2)},
        "rgb": {"r": r, "g": g, "b": b},
        "hls": {"h": color.h, "l": color.l, "s": color.s}
    }


# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
