// Глобальные переменные
let isUpdating = false;
let currentModel = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    initializePalette();
    setupEventListeners();
    updateAllModels('rgb'); // Инициализация с белым цветом
});

// Создание палитры готовых цветов
function initializePalette() {
    const palette = document.getElementById('colorPalette');
    const colors = [
        { name: 'Красный', rgb: [255, 0, 0] },
        { name: 'Зеленый', rgb: [0, 255, 0] },
        { name: 'Синий', rgb: [0, 0, 255] },
        { name: 'Желтый', rgb: [255, 255, 0] },
        { name: 'Голубой', rgb: [0, 255, 255] },
        { name: 'Пурпурный', rgb: [255, 0, 255] },
        { name: 'Оранжевый', rgb: [255, 165, 0] },
        { name: 'Фиолетовый', rgb: [128, 0, 128] },
        { name: 'Розовый', rgb: [255, 192, 203] },
        { name: 'Коричневый', rgb: [165, 42, 42] },
        { name: 'Серый', rgb: [128, 128, 128] },
        { name: 'Белый', rgb: [255, 255, 255] },
        { name: 'Черный', rgb: [0, 0, 0] },
        { name: 'Салатовый', rgb: [173, 255, 47] },
        { name: 'Морской', rgb: [32, 178, 170] },
        { name: 'Индиго', rgb: [75, 0, 130] }
    ];

    colors.forEach(color => {
        const colorDiv = document.createElement('div');
        colorDiv.className = 'palette-color';
        colorDiv.style.backgroundColor = `rgb(${color.rgb[0]}, ${color.rgb[1]}, ${color.rgb[2]})`;
        colorDiv.title = color.name;
        colorDiv.addEventListener('click', () => {
            setRGBValues(color.rgb[0], color.rgb[1], color.rgb[2]);
            updateAllModels('rgb');
        });
        palette.appendChild(colorDiv);
    });
}

// Настройка обработчиков событий
function setupEventListeners() {
    // CMYK слайдеры
    setupSliderPair('cmyk-c', 'cmyk-c-input', () => updateAllModels('cmyk'));
    setupSliderPair('cmyk-m', 'cmyk-m-input', () => updateAllModels('cmyk'));
    setupSliderPair('cmyk-y', 'cmyk-y-input', () => updateAllModels('cmyk'));
    setupSliderPair('cmyk-k', 'cmyk-k-input', () => updateAllModels('cmyk'));

    // RGB слайдеры
    setupSliderPair('rgb-r', 'rgb-r-input', () => updateAllModels('rgb'));
    setupSliderPair('rgb-g', 'rgb-g-input', () => updateAllModels('rgb'));
    setupSliderPair('rgb-b', 'rgb-b-input', () => updateAllModels('rgb'));

    // HLS слайдеры
    setupSliderPair('hls-h', 'hls-h-input', () => updateAllModels('hls'));
    setupSliderPair('hls-l', 'hls-l-input', () => updateAllModels('hls'));
    setupSliderPair('hls-s', 'hls-s-input', () => updateAllModels('hls'));

    // Color picker
    document.getElementById('colorPicker').addEventListener('input', (e) => {
        const hex = e.target.value;
        const rgb = hexToRgb(hex);
        setRGBValues(rgb.r, rgb.g, rgb.b);
        updateAllModels('rgb');
    });

    // Кнопка копирования HEX
    document.getElementById('copyHex').addEventListener('click', copyHexToClipboard);
}

// Связывание слайдера и числового поля
function setupSliderPair(sliderId, inputId, callback) {
    const slider = document.getElementById(sliderId);
    const input = document.getElementById(inputId);

    slider.addEventListener('input', (e) => {
        if (!isUpdating) {
            input.value = e.target.value;
            callback();
        }
    });

    input.addEventListener('input', (e) => {
        if (!isUpdating) {
            let value = parseFloat(e.target.value);
            const min = parseFloat(input.min);
            const max = parseFloat(input.max);
            
            if (value < min) value = min;
            if (value > max) value = max;
            
            slider.value = value;
            input.value = value;
            callback();
        }
    });
}

// Обновление всех моделей
async function updateAllModels(sourceModel) {
    if (isUpdating) return;
    
    isUpdating = true;
    currentModel = sourceModel;

    try {
        let response;

        if (sourceModel === 'cmyk') {
            const c = parseFloat(document.getElementById('cmyk-c').value);
            const m = parseFloat(document.getElementById('cmyk-m').value);
            const y = parseFloat(document.getElementById('cmyk-y').value);
            const k = parseFloat(document.getElementById('cmyk-k').value);

            response = await fetch('/convert/cmyk_to_all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ c, m, y, k })
            });
        } else if (sourceModel === 'rgb') {
            const r = parseInt(document.getElementById('rgb-r').value);
            const g = parseInt(document.getElementById('rgb-g').value);
            const b = parseInt(document.getElementById('rgb-b').value);

            response = await fetch('/convert/rgb_to_all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ r, g, b })
            });
        } else if (sourceModel === 'hls') {
            const h = parseFloat(document.getElementById('hls-h').value);
            const l = parseFloat(document.getElementById('hls-l').value);
            const s = parseFloat(document.getElementById('hls-s').value);

            response = await fetch('/convert/hls_to_all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ h, l, s })
            });
        }

        const data = await response.json();
        updateUI(data, sourceModel);
    } catch (error) {
        console.error('Ошибка при конвертации:', error);
    } finally {
        isUpdating = false;
    }
}

// Обновление интерфейса
function updateUI(data, sourceModel) {
    // Обновляем CMYK (если источник не CMYK)
    if (sourceModel !== 'cmyk') {
        setSliderValue('cmyk-c', data.cmyk.c);
        setSliderValue('cmyk-m', data.cmyk.m);
        setSliderValue('cmyk-y', data.cmyk.y);
        setSliderValue('cmyk-k', data.cmyk.k);
    }

    // Обновляем RGB (если источник не RGB)
    if (sourceModel !== 'rgb') {
        setSliderValue('rgb-r', data.rgb.r);
        setSliderValue('rgb-g', data.rgb.g);
        setSliderValue('rgb-b', data.rgb.b);
    }

    // Обновляем HLS (если источник не HLS)
    if (sourceModel !== 'hls') {
        setSliderValue('hls-h', data.hls.h);
        setSliderValue('hls-l', data.hls.l);
        setSliderValue('hls-s', data.hls.s);
    }

    // Обновляем предварительный просмотр и HEX
    updateColorPreview(data.rgb.r, data.rgb.g, data.rgb.b);
}

// Установка значения слайдера и поля ввода
function setSliderValue(baseId, value) {
    const slider = document.getElementById(baseId);
    const input = document.getElementById(baseId + '-input');
    
    slider.value = value;
    input.value = value;
}

// Установка значений RGB
function setRGBValues(r, g, b) {
    setSliderValue('rgb-r', r);
    setSliderValue('rgb-g', g);
    setSliderValue('rgb-b', b);
}

// Обновление предварительного просмотра цвета
function updateColorPreview(r, g, b) {
    const preview = document.getElementById('colorPreview');
    const hexValue = document.getElementById('hexValue');
    const colorPicker = document.getElementById('colorPicker');
    
    const color = `rgb(${r}, ${g}, ${b})`;
    const hex = rgbToHex(r, g, b);
    
    preview.style.backgroundColor = color;
    hexValue.textContent = hex;
    colorPicker.value = hex;
}

// Конвертация RGB в HEX
function rgbToHex(r, g, b) {
    const toHex = (n) => {
        const hex = n.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    };
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`.toUpperCase();
}

// Конвертация HEX в RGB
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
}

// Копирование HEX в буфер обмена
function copyHexToClipboard() {
    const hexValue = document.getElementById('hexValue').textContent;
    navigator.clipboard.writeText(hexValue).then(() => {
        const button = document.getElementById('copyHex');
        const originalText = button.textContent;
        button.textContent = '✓';
        setTimeout(() => {
            button.textContent = originalText;
        }, 1000);
    }).catch(err => {
        console.error('Ошибка при копировании:', err);
        alert('Не удалось скопировать в буфер обмена');
    });
}
