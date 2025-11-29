const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');

// Настройки канваса
const CANVAS_SIZE = 600;
const GRID_SIZE = 30;
const CELL_SIZE = CANVAS_SIZE / GRID_SIZE;

canvas.width = CANVAS_SIZE;
canvas.height = CANVAS_SIZE;

// Переменные состояния
let currentMode = 'line';

// Инициализация
function init() {
    drawGrid();
    setupEventListeners();
}

// Рисование сетки с осями и подписями
function drawGrid() {
    ctx.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
    
    // Фон
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
    
    const center = GRID_SIZE / 2;
    
    // Рисуем сетку
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 0.5;
    
    for (let i = 0; i <= GRID_SIZE; i++) {
        const pos = i * CELL_SIZE;
        
        // Вертикальные линии
        ctx.beginPath();
        ctx.moveTo(pos, 0);
        ctx.lineTo(pos, CANVAS_SIZE);
        ctx.stroke();
        
        // Горизонтальные линии
        ctx.beginPath();
        ctx.moveTo(0, pos);
        ctx.lineTo(CANVAS_SIZE, pos);
        ctx.stroke();
    }
    
    // Рисуем оси координат
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 2;
    
    // Ось Y (вертикальная)
    ctx.beginPath();
    ctx.moveTo(center * CELL_SIZE, 0);
    ctx.lineTo(center * CELL_SIZE, CANVAS_SIZE);
    ctx.stroke();
    
    // Ось X (горизонтальная)
    ctx.beginPath();
    ctx.moveTo(0, center * CELL_SIZE);
    ctx.lineTo(CANVAS_SIZE, center * CELL_SIZE);
    ctx.stroke();
    
    // Подписи осей
    ctx.fillStyle = '#333333';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    // Подписи на оси X
    for (let i = -center; i <= center; i++) {
        if (i === 0) continue;
        const x = (center + i) * CELL_SIZE;
        const y = center * CELL_SIZE + 15;
        ctx.fillText(i.toString(), x, y);
    }
    
    // Подписи на оси Y
    ctx.textAlign = 'right';
    for (let i = -center; i <= center; i++) {
        if (i === 0) continue;
        const x = center * CELL_SIZE - 5;
        const y = (center - i) * CELL_SIZE;
        ctx.fillText(i.toString(), x, y);
    }
    
    // Подпись начала координат
    ctx.textAlign = 'right';
    ctx.fillText('0', center * CELL_SIZE - 5, center * CELL_SIZE + 15);
    
    // Стрелки на осях
    drawArrow(center * CELL_SIZE, 5, center * CELL_SIZE, 0);
    drawArrow(CANVAS_SIZE - 5, center * CELL_SIZE, CANVAS_SIZE, center * CELL_SIZE);
    
    // Подписи осей
    ctx.font = 'bold 14px Arial';
    ctx.fillText('Y', center * CELL_SIZE - 10, 15);
    ctx.textAlign = 'left';
    ctx.fillText('X', CANVAS_SIZE - 15, center * CELL_SIZE + 20);
}

// Рисование стрелки
function drawArrow(fromX, fromY, toX, toY) {
    const headlen = 8;
    const angle = Math.atan2(toY - fromY, toX - fromX);
    
    ctx.beginPath();
    ctx.moveTo(toX, toY);
    ctx.lineTo(
        toX - headlen * Math.cos(angle - Math.PI / 6),
        toY - headlen * Math.sin(angle - Math.PI / 6)
    );
    ctx.moveTo(toX, toY);
    ctx.lineTo(
        toX - headlen * Math.cos(angle + Math.PI / 6),
        toY - headlen * Math.sin(angle + Math.PI / 6)
    );
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 2;
    ctx.stroke();
}

// Преобразование координат из логических в канвас
function toCanvasCoords(x, y) {
    const center = GRID_SIZE / 2;
    return {
        x: (center + x) * CELL_SIZE,
        y: (center - y) * CELL_SIZE
    };
}

// Рисование пикселя
function drawPixel(x, y, intensity = 1.0) {
    const coords = toCanvasCoords(x, y);
    
    if (intensity < 1.0) {
        // Алгоритм Ву с прозрачностью
        const alpha = intensity;
        ctx.fillStyle = `rgba(102, 126, 234, ${alpha})`;
    } else {
        ctx.fillStyle = '#667eea';
    }
    
    ctx.fillRect(
        coords.x - CELL_SIZE / 2 + 1,
        coords.y - CELL_SIZE / 2 + 1,
        CELL_SIZE - 2,
        CELL_SIZE - 2
    );
}

// Обработчики событий
function setupEventListeners() {
    // Выбор режима
    document.querySelectorAll('input[name="mode"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            currentMode = e.target.value;
            document.getElementById('line-controls').style.display = 
                currentMode === 'line' ? 'block' : 'none';
            document.getElementById('circle-controls').style.display = 
                currentMode === 'circle' ? 'block' : 'none';
        });
    });
    
    // Кнопка рисования
    document.getElementById('drawBtn').addEventListener('click', draw);
    
    // Кнопка очистки
    document.getElementById('clearBtn').addEventListener('click', () => {
        drawGrid();
        document.getElementById('time').textContent = '-';
        document.getElementById('count').textContent = '-';
    });
    
    // Подсказка с координатами
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const center = GRID_SIZE / 2;
        const logicalX = Math.floor(x / CELL_SIZE - center);
        const logicalY = Math.floor(center - y / CELL_SIZE);
        
        tooltip.textContent = `(${logicalX}, ${logicalY})`;
        tooltip.style.display = 'block';
        tooltip.style.left = (e.clientX + 10) + 'px';
        tooltip.style.top = (e.clientY + 10) + 'px';
    });
    
    canvas.addEventListener('mouseleave', () => {
        tooltip.style.display = 'none';
    });
}

// Основная функция рисования
async function draw() {
    drawGrid();
    
    const algorithm = document.getElementById('algorithm').value;
    
    try {
        if (currentMode === 'line') {
            const x1 = parseInt(document.getElementById('x1').value);
            const y1 = parseInt(document.getElementById('y1').value);
            const x2 = parseInt(document.getElementById('x2').value);
            const y2 = parseInt(document.getElementById('y2').value);
            
            const response = await fetch('/draw', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ algorithm, x1, y1, x2, y2 }),
            });
            
            const data = await response.json();
            
            // Рисуем пиксели
            data.pixels.forEach(pixel => {
                drawPixel(pixel.x, pixel.y, pixel.intensity || 1.0);
            });
            
            // Обновляем статистику
            document.getElementById('time').textContent = data.time.toFixed(2);
            document.getElementById('count').textContent = data.count;
            
        } else if (currentMode === 'circle') {
            const xc = parseInt(document.getElementById('xc').value);
            const yc = parseInt(document.getElementById('yc').value);
            const r = parseInt(document.getElementById('radius').value);
            
            const response = await fetch('/draw_circle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ xc, yc, r }),
            });
            
            const data = await response.json();
            
            // Рисуем пиксели
            data.pixels.forEach(pixel => {
                drawPixel(pixel.x, pixel.y);
            });
            
            // Обновляем статистику
            document.getElementById('time').textContent = data.time.toFixed(2);
            document.getElementById('count').textContent = data.count;
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Произошла ошибка при рисовании');
    }
}

// Запуск при загрузке
init();
