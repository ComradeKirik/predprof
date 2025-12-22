anychart.onDocumentReady(function () {
    // Получаем контейнер графика
    var chartContainer = document.getElementById('scoreChart');

    // Получаем данные из data-атрибута
    var chartDataJson = chartContainer.getAttribute('data-chart-data');

    // Парсим JSON
    var data;
    try {
        data = JSON.parse(chartDataJson);
    } catch (e) {
        alert('Error parsing chart data:', e);
        data = [];
    }

    // Если данных нет, показываем заглушку
    if (!data || data.length === 0) {
        data = [["Нет данных за последние 30 дней", 0]];
    }

    // Создаем график
    var chart = anychart.line();
    var series = chart.line(data);

    // Настройки графика
    chart.title("Ваши очки по дням");

    var xAxis = chart.xAxis();
    xAxis.title("Дата");

    var yAxis = chart.yAxis();
    yAxis.title("Очки");

    // Форматируем даты на оси X
    chart.xAxis().labels().format('{%value}{dateTimeFormat:dd.MM}');

    // Дополнительные настройки для лучшего отображения
    chart.tooltip().format("Дата: {%x}\nОчки: {%value}");

    // Включаем легенду
    chart.legend().enabled(false);

    // Устанавливаем контейнер и рисуем график
    chart.container("scoreChart");
    chart.draw();
});