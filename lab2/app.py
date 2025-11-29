from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
from PIL import Image
import io
import base64
import cv2
from typing import Optional, Literal
import os

app = FastAPI(title="Image Processing Lab 2")

# CORS для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ThresholdParams(BaseModel):
    """Параметры пороговой обработки"""
    method: Literal["otsu", "adaptive_mean", "adaptive_gaussian", "niblack"]
    block_size: int = Field(11, ge=3, description="Размер блока (должен быть нечетным)")
    c_constant: float = Field(2.0, description="Константа для адаптивного порога")
    k_niblack: float = Field(-0.2, ge=-1, le=1, description="Коэффициент для метода Niblack")


class ContrastParams(BaseModel):
    """Параметры контрастирования"""
    alpha: float = Field(1.0, ge=0.1, le=3.0, description="Коэффициент контраста")
    beta: float = Field(0, ge=-100, le=100, description="Смещение яркости")


class ArithmeticParams(BaseModel):
    """Параметры поэлементных операций"""
    operation: Literal["add", "subtract", "multiply", "divide"]
    value: float = Field(50, description="Значение для операции")


class HistogramParams(BaseModel):
    """Параметры эквализации гистограммы"""
    method: Literal["rgb", "hsv_v", "hls_l"]


def image_to_base64(image: np.ndarray) -> str:
    """Конвертация numpy массива в base64 строку"""
    # Конвертируем BGR в RGB для корректного отображения
    if len(image.shape) == 3:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        image_rgb = image
    
    pil_img = Image.fromarray(image_rgb)
    buff = io.BytesIO()
    pil_img.save(buff, format="PNG")
    img_str = base64.b64encode(buff.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def load_image_from_upload(file_bytes: bytes) -> np.ndarray:
    """Загрузка изображения из загруженного файла"""
    image = Image.open(io.BytesIO(file_bytes))
    # Конвертируем в RGB если необходимо
    if image.mode != 'RGB':
        image = image.convert('RGB')
    # Конвертируем в numpy и BGR для OpenCV
    img_array = np.array(image)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    return img_bgr


def calculate_histogram(image: np.ndarray) -> dict:
    """Вычисление гистограммы для всех каналов"""
    if len(image.shape) == 2:
        # Grayscale
        hist = cv2.calcHist([image], [0], None, [256], [0, 256])
        return {
            "gray": hist.flatten().tolist()
        }
    else:
        # Color image (BGR)
        hist_b = cv2.calcHist([image], [0], None, [256], [0, 256])
        hist_g = cv2.calcHist([image], [1], None, [256], [0, 256])
        hist_r = cv2.calcHist([image], [2], None, [256], [0, 256])
        
        return {
            "blue": hist_b.flatten().tolist(),
            "green": hist_g.flatten().tolist(),
            "red": hist_r.flatten().tolist()
        }


# ============= ПОРОГОВАЯ ОБРАБОТКА =============

def threshold_otsu(image: np.ndarray) -> np.ndarray:
    """
    Метод Оцу (Otsu) - автоматическое определение порога
    
    Алгоритм минимизирует внутриклассовую дисперсию (within-class variance)
    или максимизирует межклассовую дисперсию (between-class variance).
    Оптимален для изображений с бимодальной гистограммой.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)


def threshold_adaptive_mean(image: np.ndarray, block_size: int = 11, c: float = 2) -> np.ndarray:
    """
    Адаптивная пороговая обработка (среднее значение)
    
    Порог для каждого пикселя вычисляется как среднее значение 
    в окрестности размера block_size минус константа C.
    
    T(x,y) = mean(block) - C
    
    Подходит для изображений с неравномерным освещением.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Убедимся, что block_size нечетный
    if block_size % 2 == 0:
        block_size += 1
    
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
        cv2.THRESH_BINARY, block_size, c
    )
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)


def threshold_adaptive_gaussian(image: np.ndarray, block_size: int = 11, c: float = 2) -> np.ndarray:
    """
    Адаптивная пороговая обработка (взвешенное среднее по Гауссу)
    
    Порог вычисляется как взвешенная сумма значений в окрестности,
    где веса определяются гауссовым распределением.
    
    T(x,y) = gaussian_weighted_mean(block) - C
    
    Более устойчив к шуму по сравнению со средним арифметическим.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if block_size % 2 == 0:
        block_size += 1
    
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, block_size, c
    )
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)


def threshold_niblack(image: np.ndarray, block_size: int = 15, k: float = -0.2) -> np.ndarray:
    """
    Метод Niblack - локальная пороговая обработка
    
    Формула: T(x,y) = m(x,y) + k * s(x,y)
    где:
    - m(x,y) - локальное среднее в окне
    - s(x,y) - локальное стандартное отклонение
    - k - коэффициент (обычно от -0.2 до -0.5)
    
    Эффективен для текстов и документов с неравномерным фоном.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64)
    
    if block_size % 2 == 0:
        block_size += 1
    
    # Вычисляем локальное среднее
    mean = cv2.blur(gray, (block_size, block_size))
    
    # Вычисляем локальное стандартное отклонение
    mean_sq = cv2.blur(gray ** 2, (block_size, block_size))
    std = np.sqrt(mean_sq - mean ** 2)
    
    # Применяем формулу Niblack
    threshold = mean + k * std
    
    # Бинаризация
    binary = (gray > threshold).astype(np.uint8) * 255
    
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


# ============= КОНТРАСТИРОВАНИЕ И ПОЭЛЕМЕНТНЫЕ ОПЕРАЦИИ =============

def linear_contrast(image: np.ndarray, alpha: float = 1.0, beta: float = 0) -> np.ndarray:
    """
    Линейное контрастирование
    
    Формула: new_pixel = alpha * old_pixel + beta
    где:
    - alpha (gain) - коэффициент контраста (1.0 = без изменений)
      alpha > 1: увеличение контраста
      alpha < 1: уменьшение контраста
    - beta (bias) - смещение яркости
      beta > 0: увеличение яркости
      beta < 0: уменьшение яркости
    
    Результат ограничивается диапазоном [0, 255]
    """
    # Преобразуем в float для точных вычислений
    img_float = image.astype(np.float64)
    
    # Применяем линейное преобразование
    adjusted = alpha * img_float + beta
    
    # Ограничиваем диапазон [0, 255]
    adjusted = np.clip(adjusted, 0, 255)
    
    # Конвертируем обратно в uint8
    return adjusted.astype(np.uint8)


def arithmetic_operation(image: np.ndarray, operation: str, value: float) -> np.ndarray:
    """
    Поэлементные арифметические операции над изображением
    
    Операции применяются к каждому пикселю независимо:
    - add: pixel + value (увеличение яркости)
    - subtract: pixel - value (уменьшение яркости)
    - multiply: pixel * value (масштабирование)
    - divide: pixel / value (уменьшение интенсивности)
    
    Результаты автоматически обрезаются до диапазона [0, 255]
    """
    img_float = image.astype(np.float64)
    
    if operation == "add":
        result = cv2.add(img_float, value)
    elif operation == "subtract":
        result = cv2.subtract(img_float, value)
    elif operation == "multiply":
        result = img_float * (value / 100.0)  # Нормализуем для удобства
    elif operation == "divide":
        if value == 0:
            value = 1
        result = img_float / (value / 100.0)
    else:
        result = img_float
    
    # Обрезаем значения до диапазона [0, 255]
    result = np.clip(result, 0, 255)
    return result.astype(np.uint8)


# ============= ЭКВАЛИЗАЦИЯ ГИСТОГРАММЫ =============

def histogram_equalization_rgb(image: np.ndarray) -> np.ndarray:
    """
    Эквализация гистограммы в пространстве RGB
    
    Применяет эквализацию независимо к каждому каналу R, G, B.
    
    Процесс:
    1. Вычисляется гистограмма для каждого канала
    2. Строится кумулятивная функция распределения (CDF)
    3. Нормализуется CDF к диапазону [0, 255]
    4. Каждое значение пикселя заменяется на соответствующее значение из CDF
    
    Недостаток: может изменить цветовой баланс изображения
    """
    # Разделяем на каналы BGR
    b, g, r = cv2.split(image)
    
    # Эквализация каждого канала
    b_eq = cv2.equalizeHist(b)
    g_eq = cv2.equalizeHist(g)
    r_eq = cv2.equalizeHist(r)
    
    # Объединяем обратно
    equalized = cv2.merge([b_eq, g_eq, r_eq])
    return equalized


def histogram_equalization_hsv_v(image: np.ndarray) -> np.ndarray:
    """
    Эквализация только канала V (Value) в пространстве HSV
    
    HSV = Hue (тон), Saturation (насыщенность), Value (яркость)
    
    Преимущества:
    - Сохраняет цветовую информацию (H и S не изменяются)
    - Изменяет только яркость изображения
    - Не искажает цвета, в отличие от RGB эквализации
    
    Применение: улучшение яркости при сохранении цветов
    """
    # Конвертируем BGR -> HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    
    # Эквализация только канала V (яркость)
    v_eq = cv2.equalizeHist(v)
    
    # Объединяем обратно
    hsv_eq = cv2.merge([h, s, v_eq])
    
    # Конвертируем обратно в BGR
    result = cv2.cvtColor(hsv_eq, cv2.COLOR_HSV2BGR)
    return result


def histogram_equalization_hls_l(image: np.ndarray) -> np.ndarray:
    """
    Эквализация только канала L (Lightness) в пространстве HLS
    
    HLS = Hue (тон), Lightness (светлота), Saturation (насыщенность)
    
    Отличие от HSV:
    - L (Lightness) - перцептивная яркость (как человек воспринимает)
    - V (Value) - математическая яркость (max(R,G,B))
    
    HLS более соответствует человеческому восприятию яркости.
    """
    # Конвертируем BGR -> HLS
    hls = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
    h, l, s = cv2.split(hls)
    
    # Эквализация только канала L (светлота)
    l_eq = cv2.equalizeHist(l)
    
    # Объединяем обратно
    hls_eq = cv2.merge([h, l_eq, s])
    
    # Конвертируем обратно в BGR
    result = cv2.cvtColor(hls_eq, cv2.COLOR_HLS2BGR)
    return result


# ============= API ENDPOINTS =============

@app.get("/")
async def read_root():
    """Главная страница приложения"""
    return FileResponse("static/index.html")


@app.post("/api/threshold")
async def apply_threshold(
    file: UploadFile = File(...),
    method: str = "otsu",
    block_size: int = 11,
    c_constant: float = 2.0,
    k_niblack: float = -0.2
):
    """
    Применение пороговой обработки к изображению
    
    Методы:
    - otsu: Метод Оцу (автоматический порог)
    - adaptive_mean: Адаптивный порог (среднее)
    - adaptive_gaussian: Адаптивный порог (Гаусс)
    - niblack: Метод Niblack (локальный порог)
    """
    try:
        # Загружаем изображение
        contents = await file.read()
        image = load_image_from_upload(contents)
        
        # Применяем выбранный метод
        if method == "otsu":
            result = threshold_otsu(image)
        elif method == "adaptive_mean":
            result = threshold_adaptive_mean(image, block_size, c_constant)
        elif method == "adaptive_gaussian":
            result = threshold_adaptive_gaussian(image, block_size, c_constant)
        elif method == "niblack":
            result = threshold_niblack(image, block_size, k_niblack)
        else:
            raise HTTPException(status_code=400, detail="Unknown threshold method")
        
        # Вычисляем гистограммы
        hist_original = calculate_histogram(image)
        hist_result = calculate_histogram(result)
        
        return JSONResponse({
            "original": image_to_base64(image),
            "result": image_to_base64(result),
            "histogram_original": hist_original,
            "histogram_result": hist_result,
            "method": method
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/contrast")
async def apply_contrast(
    file: UploadFile = File(...),
    alpha: float = 1.0,
    beta: float = 0
):
    """
    Применение линейного контрастирования
    
    Параметры:
    - alpha: коэффициент контраста (0.1 - 3.0)
    - beta: смещение яркости (-100 - 100)
    """
    try:
        contents = await file.read()
        image = load_image_from_upload(contents)
        
        result = linear_contrast(image, alpha, beta)
        
        hist_original = calculate_histogram(image)
        hist_result = calculate_histogram(result)
        
        return JSONResponse({
            "original": image_to_base64(image),
            "result": image_to_base64(result),
            "histogram_original": hist_original,
            "histogram_result": hist_result,
            "alpha": alpha,
            "beta": beta
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/arithmetic")
async def apply_arithmetic(
    file: UploadFile = File(...),
    operation: str = "add",
    value: float = 50
):
    """
    Применение поэлементных операций
    
    Операции:
    - add: сложение
    - subtract: вычитание
    - multiply: умножение
    - divide: деление
    """
    try:
        contents = await file.read()
        image = load_image_from_upload(contents)
        
        result = arithmetic_operation(image, operation, value)
        
        hist_original = calculate_histogram(image)
        hist_result = calculate_histogram(result)
        
        return JSONResponse({
            "original": image_to_base64(image),
            "result": image_to_base64(result),
            "histogram_original": hist_original,
            "histogram_result": hist_result,
            "operation": operation,
            "value": value
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/histogram-equalization")
async def apply_histogram_equalization(
    file: UploadFile = File(...),
    method: str = "rgb"
):
    """
    Эквализация гистограммы
    
    Методы:
    - rgb: эквализация всех каналов RGB
    - hsv_v: эквализация только яркости V в HSV
    - hls_l: эквализация только светлоты L в HLS
    """
    try:
        contents = await file.read()
        image = load_image_from_upload(contents)
        
        if method == "rgb":
            result = histogram_equalization_rgb(image)
        elif method == "hsv_v":
            result = histogram_equalization_hsv_v(image)
        elif method == "hls_l":
            result = histogram_equalization_hls_l(image)
        else:
            raise HTTPException(status_code=400, detail="Unknown equalization method")
        
        hist_original = calculate_histogram(image)
        hist_result = calculate_histogram(result)
        
        return JSONResponse({
            "original": image_to_base64(image),
            "result": image_to_base64(result),
            "histogram_original": hist_original,
            "histogram_result": hist_result,
            "method": method
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
