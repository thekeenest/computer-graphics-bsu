// Глобальные переменные
let currentImage = null;
let currentTab = 'threshold';
let originalHistogramChart = null;
let resultHistogramChart = null;

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    setupDragAndDrop();
});

// Настройка обработчиков событий
function setupEventListeners() {
    // Загрузка файла
    document.getElementById('imageInput').addEventListener('change', handleImageUpload);
    
    // Переключение вкладок
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => switchTab(button.dataset.tab));
    });
    
    // Пороговая обработка
    document.getElementById('thresholdMethod').addEventListener('change', updateThresholdControls);
    document.getElementById('blockSize').addEventListener('input', (e) => {
        document.getElementById('blockSizeValue').textContent = e.target.value;
    });
    document.getElementById('cConstant').addEventListener('input', (e) => {
        document.getElementById('cConstantValue').textContent = e.target.value;
    });
    document.getElementById('kNiblack').addEventListener('input', (e) => {
        document.getElementById('kNiblackValue').textContent = e.target.value;
    });
    document.getElementById('applyThreshold').addEventListener('click', applyThreshold);
    
    // Контрастирование
    document.getElementById('alpha').addEventListener('input', (e) => {
        document.getElementById('alphaValue').textContent = parseFloat(e.target.value).toFixed(1);
    });
    document.getElementById('beta').addEventListener('input', (e) => {
        document.getElementById('betaValue').textContent = e.target.value;
    });
    document.getElementById('applyContrast').addEventListener('click', applyContrast);
    
    // Поэлементные операции
    document.getElementById('operationValue').addEventListener('input', (e) => {
        document.getElementById('operationValueDisplay').textContent = e.target.value;
    });
    document.getElementById('applyArithmetic').addEventListener('click', applyArithmetic);
    
    // Эквализация гистограммы
    document.getElementById('histMethod').addEventListener('change', updateHistogramDescription);
    document.getElementById('applyHistogram').addEventListener('click', applyHistogramEqualization);
    
    // Действия с результатом
    document.getElementById('downloadResult').addEventListener('click', downloadResult);
    document.getElementById('resetImage').addEventListener('click', resetImage);
}

// Drag and Drop
function setupDragAndDrop() {
    const uploadBox = document.querySelector('.upload-box');
    
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.style.borderColor = '#764ba2';
        uploadBox.style.background = '#f8f9ff';
    });
    
    uploadBox.addEventListener('dragleave', () => {
        uploadBox.style.borderColor = '#667eea';
        uploadBox.style.background = '';
    });
    
    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.style.borderColor = '#667eea';
        uploadBox.style.background = '';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            document.getElementById('imageInput').files = files;
            handleImageUpload({ target: { files: files } });
        }
    });
}

// Обработка загрузки изображения
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        alert('Пожалуйста, выберите изображение!');
        return;
    }
    
    currentImage = file;
    document.getElementById('fileName').textContent = `Загружено: ${file.name}`;
    
    // Включаем кнопки применения
    enableApplyButtons();
}

// Переключение вкладок
function switchTab(tabName) {
    currentTab = tabName;
    
    // Обновляем кнопки
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Обновляем контент
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
}

// Обновление контролов для пороговой обработки
function updateThresholdControls() {
    const method = document.getElementById('thresholdMethod').value;
    const blockSizeGroup = document.getElementById('blockSizeGroup');
    const cConstantGroup = document.getElementById('cConstantGroup');
    const kNiblackGroup = document.getElementById('kNiblackGroup');
    
    if (method === 'otsu') {
        blockSizeGroup.style.display = 'none';
        cConstantGroup.style.display = 'none';
        kNiblackGroup.style.display = 'none';
    } else if (method === 'niblack') {
        blockSizeGroup.style.display = 'block';
        cConstantGroup.style.display = 'none';
        kNiblackGroup.style.display = 'block';
    } else {
        blockSizeGroup.style.display = 'block';
        cConstantGroup.style.display = 'block';
        kNiblackGroup.style.display = 'none';
    }
}

// Обновление описания метода эквализации
function updateHistogramDescription() {
    const method = document.getElementById('histMethod').value;
    const description = document.getElementById('methodDescription');
    
    const descriptions = {
        'rgb': 'Эквализация каждого канала RGB независимо. Может изменить цветовой баланс.',
        'hsv_v': 'Эквализация только яркости V в пространстве HSV. Сохраняет цвета.',
        'hls_l': 'Эквализация только светлоты L в пространстве HLS. Перцептивно корректная яркость.'
    };
    
    description.textContent = descriptions[method];
}

// Применение пороговой обработки
async function applyThreshold() {
    if (!currentImage) {
        alert('Сначала загрузите изображение!');
        return;
    }
    
    const method = document.getElementById('thresholdMethod').value;
    const blockSize = parseInt(document.getElementById('blockSize').value);
    const cConstant = parseFloat(document.getElementById('cConstant').value);
    const kNiblack = parseFloat(document.getElementById('kNiblack').value);
    
    const formData = new FormData();
    formData.append('file', currentImage);
    formData.append('method', method);
    formData.append('block_size', blockSize);
    formData.append('c_constant', cConstant);
    formData.append('k_niblack', kNiblack);
    
    showLoader();
    
    try {
        const response = await fetch('/api/threshold', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Ошибка обработки');
        
        const data = await response.json();
        displayResults(data, 'threshold');
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при обработке изображения: ' + error.message);
    } finally {
        hideLoader();
    }
}

// Применение контрастирования
async function applyContrast() {
    if (!currentImage) {
        alert('Сначала загрузите изображение!');
        return;
    }
    
    const alpha = parseFloat(document.getElementById('alpha').value);
    const beta = parseFloat(document.getElementById('beta').value);
    
    const formData = new FormData();
    formData.append('file', currentImage);
    formData.append('alpha', alpha);
    formData.append('beta', beta);
    
    showLoader();
    
    try {
        const response = await fetch('/api/contrast', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Ошибка обработки');
        
        const data = await response.json();
        displayResults(data, 'contrast');
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при обработке изображения: ' + error.message);
    } finally {
        hideLoader();
    }
}

// Применение арифметических операций
async function applyArithmetic() {
    if (!currentImage) {
        alert('Сначала загрузите изображение!');
        return;
    }
    
    const operation = document.getElementById('operation').value;
    const value = parseFloat(document.getElementById('operationValue').value);
    
    const formData = new FormData();
    formData.append('file', currentImage);
    formData.append('operation', operation);
    formData.append('value', value);
    
    showLoader();
    
    try {
        const response = await fetch('/api/arithmetic', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Ошибка обработки');
        
        const data = await response.json();
        displayResults(data, 'arithmetic');
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при обработке изображения: ' + error.message);
    } finally {
        hideLoader();
    }
}

// Применение эквализации гистограммы
async function applyHistogramEqualization() {
    if (!currentImage) {
        alert('Сначала загрузите изображение!');
        return;
    }
    
    const method = document.getElementById('histMethod').value;
    
    const formData = new FormData();
    formData.append('file', currentImage);
    formData.append('method', method);
    
    showLoader();
    
    try {
        const response = await fetch('/api/histogram-equalization', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Ошибка обработки');
        
        const data = await response.json();
        displayResults(data, 'histogram');
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при обработке изображения: ' + error.message);
    } finally {
        hideLoader();
    }
}

// Отображение результатов
function displayResults(data, type) {
    // Показываем секцию результатов
    document.getElementById('resultsSection').style.display = 'block';
    
    // Устанавливаем изображения
    document.getElementById('originalImage').src = data.original;
    document.getElementById('resultImage').src = data.result;
    
    // Обновляем гистограммы
    updateHistograms(data.histogram_original, data.histogram_result);
    
    // Обновляем информационную панель
    updateInfoPanel(data, type);
    
    // Прокручиваем к результатам
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

// Обновление гистограмм
function updateHistograms(originalHist, resultHist) {
    // Уничтожаем старые графики
    if (originalHistogramChart) originalHistogramChart.destroy();
    if (resultHistogramChart) resultHistogramChart.destroy();
    
    // Создаем новые графики
    originalHistogramChart = createHistogramChart('originalHistogram', originalHist, 'Гистограмма исходного изображения');
    resultHistogramChart = createHistogramChart('resultHistogram', resultHist, 'Гистограмма результата');
}

// Создание графика гистограммы
function createHistogramChart(canvasId, histData, title) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    const datasets = [];
    
    if (histData.gray) {
        datasets.push({
            label: 'Яркость',
            data: histData.gray,
            borderColor: '#666',
            backgroundColor: 'rgba(102, 102, 102, 0.3)',
            borderWidth: 1,
            fill: true
        });
    } else {
        if (histData.red) {
            datasets.push({
                label: 'Красный',
                data: histData.red,
                borderColor: '#ff0000',
                backgroundColor: 'rgba(255, 0, 0, 0.2)',
                borderWidth: 1,
                fill: true
            });
        }
        if (histData.green) {
            datasets.push({
                label: 'Зеленый',
                data: histData.green,
                borderColor: '#00ff00',
                backgroundColor: 'rgba(0, 255, 0, 0.2)',
                borderWidth: 1,
                fill: true
            });
        }
        if (histData.blue) {
            datasets.push({
                label: 'Синий',
                data: histData.blue,
                borderColor: '#0000ff',
                backgroundColor: 'rgba(0, 0, 255, 0.2)',
                borderWidth: 1,
                fill: true
            });
        }
    }
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: 256}, (_, i) => i),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: title
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Обновление информационной панели
function updateInfoPanel(data, type) {
    const panel = document.getElementById('infoPanel');
    let html = '<h4>Информация об обработке</h4>';
    
    if (type === 'threshold') {
        const methodNames = {
            'otsu': 'Метод Оцу (Otsu)',
            'adaptive_mean': 'Адаптивный порог (среднее)',
            'adaptive_gaussian': 'Адаптивный порог (Гаусс)',
            'niblack': 'Метод Niblack'
        };
        html += `<p><strong>Метод:</strong> ${methodNames[data.method]}</p>`;
    } else if (type === 'contrast') {
        html += `<p><strong>Коэффициент контраста (α):</strong> ${data.alpha}</p>`;
        html += `<p><strong>Смещение яркости (β):</strong> ${data.beta}</p>`;
        html += `<p><strong>Формула:</strong> новый_пиксель = ${data.alpha} × старый_пиксель + ${data.beta}</p>`;
    } else if (type === 'arithmetic') {
        const operationNames = {
            'add': 'Сложение',
            'subtract': 'Вычитание',
            'multiply': 'Умножение',
            'divide': 'Деление'
        };
        html += `<p><strong>Операция:</strong> ${operationNames[data.operation]}</p>`;
        html += `<p><strong>Значение:</strong> ${data.value}</p>`;
    } else if (type === 'histogram') {
        const methodNames = {
            'rgb': 'RGB (все каналы)',
            'hsv_v': 'HSV (яркость V)',
            'hls_l': 'HLS (светлота L)'
        };
        html += `<p><strong>Метод:</strong> ${methodNames[data.method]}</p>`;
    }
    
    panel.innerHTML = html;
}

// Скачивание результата
function downloadResult() {
    const resultImage = document.getElementById('resultImage');
    const link = document.createElement('a');
    link.href = resultImage.src;
    link.download = `result_${Date.now()}.png`;
    link.click();
}

// Сброс и загрузка нового изображения
function resetImage() {
    currentImage = null;
    document.getElementById('imageInput').value = '';
    document.getElementById('fileName').textContent = '';
    document.getElementById('resultsSection').style.display = 'none';
    disableApplyButtons();
    
    // Прокручиваем наверх
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Показать индикатор загрузки
function showLoader() {
    document.getElementById('loader').style.display = 'block';
    disableApplyButtons();
}

// Скрыть индикатор загрузки
function hideLoader() {
    document.getElementById('loader').style.display = 'none';
    enableApplyButtons();
}

// Включить кнопки применения
function enableApplyButtons() {
    document.querySelectorAll('.apply-button').forEach(btn => {
        btn.disabled = false;
    });
}

// Выключить кнопки применения
function disableApplyButtons() {
    document.querySelectorAll('.apply-button').forEach(btn => {
        btn.disabled = true;
    });
}

// Инициализация
updateThresholdControls();
updateHistogramDescription();
disableApplyButtons();
