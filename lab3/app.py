from flask import Flask, render_template, request, jsonify
import math
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def step_by_step_line(x1, y1, x2, y2):
    """Пошаговый алгоритм растеризации линии"""
    pixels = []
    
    if abs(x2 - x1) > abs(y2 - y1):
        # Итерация по x
        if x1 > x2:
            x1, x2, y1, y2 = x2, x1, y2, y1
        
        steps = abs(x2 - x1)
        if steps == 0:
            return [(x1, y1)]
        
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps
        
        x, y = x1, y1
        for _ in range(steps + 1):
            pixels.append((round(x), round(y)))
            x += dx
            y += dy
    else:
        # Итерация по y
        if y1 > y2:
            x1, x2, y1, y2 = x2, x1, y2, y1
        
        steps = abs(y2 - y1)
        if steps == 0:
            return [(x1, y1)]
        
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps
        
        x, y = x1, y1
        for _ in range(steps + 1):
            pixels.append((round(x), round(y)))
            x += dx
            y += dy
    
    return pixels

def dda_line(x1, y1, x2, y2):
    """Алгоритм ЦДА (Цифровой Дифференциальный Анализатор)"""
    pixels = []
    
    dx = x2 - x1
    dy = y2 - y1
    
    steps = max(abs(dx), abs(dy))
    
    if steps == 0:
        return [(x1, y1)]
    
    x_increment = dx / steps
    y_increment = dy / steps
    
    x, y = x1, y1
    
    for _ in range(steps + 1):
        pixels.append((round(x), round(y)))
        x += x_increment
        y += y_increment
    
    return pixels

def bresenham_line(x1, y1, x2, y2):
    """Алгоритм Брезенхема для линий"""
    pixels = []
    
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    
    err = dx - dy
    
    x, y = x1, y1
    
    while True:
        pixels.append((x, y))
        
        if x == x2 and y == y2:
            break
        
        e2 = 2 * err
        
        if e2 > -dy:
            err -= dy
            x += sx
        
        if e2 < dx:
            err += dx
            y += sy
    
    return pixels

def bresenham_circle(xc, yc, r):
    """Алгоритм Брезенхема для окружности"""
    pixels = []
    
    x = 0
    y = r
    d = 3 - 2 * r
    
    def add_circle_points(xc, yc, x, y):
        points = [
            (xc + x, yc + y),
            (xc - x, yc + y),
            (xc + x, yc - y),
            (xc - x, yc - y),
            (xc + y, yc + x),
            (xc - y, yc + x),
            (xc + y, yc - x),
            (xc - y, yc - x)
        ]
        return points
    
    pixels.extend(add_circle_points(xc, yc, x, y))
    
    while y >= x:
        x += 1
        
        if d > 0:
            y -= 1
            d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6
        
        pixels.extend(add_circle_points(xc, yc, x, y))
    
    return pixels

def wu_line(x1, y1, x2, y2):
    """Алгоритм Ву для сглаженных линий"""
    pixels = []
    
    def fpart(x):
        return x - math.floor(x)
    
    def rfpart(x):
        return 1 - fpart(x)
    
    steep = abs(y2 - y1) > abs(x2 - x1)
    
    if steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
    
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0:
        gradient = 1.0
    else:
        gradient = dy / dx
    
    # Обработка первой конечной точки
    xend = round(x1)
    yend = y1 + gradient * (xend - x1)
    xgap = rfpart(x1 + 0.5)
    xpxl1 = xend
    ypxl1 = math.floor(yend)
    
    if steep:
        pixels.append((ypxl1, xpxl1, rfpart(yend) * xgap))
        pixels.append((ypxl1 + 1, xpxl1, fpart(yend) * xgap))
    else:
        pixels.append((xpxl1, ypxl1, rfpart(yend) * xgap))
        pixels.append((xpxl1, ypxl1 + 1, fpart(yend) * xgap))
    
    intery = yend + gradient
    
    # Обработка второй конечной точки
    xend = round(x2)
    yend = y2 + gradient * (xend - x2)
    xgap = fpart(x2 + 0.5)
    xpxl2 = xend
    ypxl2 = math.floor(yend)
    
    if steep:
        pixels.append((ypxl2, xpxl2, rfpart(yend) * xgap))
        pixels.append((ypxl2 + 1, xpxl2, fpart(yend) * xgap))
    else:
        pixels.append((xpxl2, ypxl2, rfpart(yend) * xgap))
        pixels.append((xpxl2, ypxl2 + 1, fpart(yend) * xgap))
    
    # Основной цикл
    if steep:
        for x in range(xpxl1 + 1, xpxl2):
            pixels.append((math.floor(intery), x, rfpart(intery)))
            pixels.append((math.floor(intery) + 1, x, fpart(intery)))
            intery += gradient
    else:
        for x in range(xpxl1 + 1, xpxl2):
            pixels.append((x, math.floor(intery), rfpart(intery)))
            pixels.append((x, math.floor(intery) + 1, fpart(intery)))
            intery += gradient
    
    return pixels

def castle_pitway_line(x1, y1, x2, y2):
    """Алгоритм Кастла-Питвея (обобщение Брезенхема)"""
    pixels = []
    
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    
    while True:
        pixels.append((x1, y1))
        
        if x1 == x2 and y1 == y2:
            break
        
        e2 = 2 * err
        
        if e2 > -dy:
            err -= dy
            x1 += sx
        
        if e2 < dx:
            err += dx
            y1 += sy
    
    return pixels

@app.route('/draw', methods=['POST'])
def draw():
    data = request.json
    algorithm = data.get('algorithm')
    x1 = int(data.get('x1'))
    y1 = int(data.get('y1'))
    x2 = int(data.get('x2'))
    y2 = int(data.get('y2'))
    
    start_time = time.perf_counter()
    
    if algorithm == 'step_by_step':
        pixels = step_by_step_line(x1, y1, x2, y2)
    elif algorithm == 'dda':
        pixels = dda_line(x1, y1, x2, y2)
    elif algorithm == 'bresenham':
        pixels = bresenham_line(x1, y1, x2, y2)
    elif algorithm == 'wu':
        pixels = wu_line(x1, y1, x2, y2)
    elif algorithm == 'castle_pitway':
        pixels = castle_pitway_line(x1, y1, x2, y2)
    else:
        return jsonify({'error': 'Unknown algorithm'}), 400
    
    end_time = time.perf_counter()
    execution_time = (end_time - start_time) * 1000000  # в микросекундах
    
    # Преобразуем пиксели в нужный формат
    result_pixels = []
    for pixel in pixels:
        if len(pixel) == 3:  # Алгоритм Ву с интенсивностью
            result_pixels.append({'x': pixel[0], 'y': pixel[1], 'intensity': pixel[2]})
        else:
            result_pixels.append({'x': pixel[0], 'y': pixel[1]})
    
    return jsonify({
        'pixels': result_pixels,
        'time': round(execution_time, 2),
        'count': len(pixels)
    })

@app.route('/draw_circle', methods=['POST'])
def draw_circle():
    data = request.json
    xc = int(data.get('xc'))
    yc = int(data.get('yc'))
    r = int(data.get('r'))
    
    start_time = time.perf_counter()
    pixels = bresenham_circle(xc, yc, r)
    end_time = time.perf_counter()
    
    execution_time = (end_time - start_time) * 1000000  # в микросекундах
    
    result_pixels = [{'x': pixel[0], 'y': pixel[1]} for pixel in pixels]
    
    return jsonify({
        'pixels': result_pixels,
        'time': round(execution_time, 2),
        'count': len(pixels)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
