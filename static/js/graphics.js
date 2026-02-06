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
        data = [];
        alert(e)
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

    // Адаптация под тему
    function updateChartTheme() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (isDark) {
            chart.background().fill("transparent");
            chart.title().fontColor("#e0e0e0");
            chart.xAxis().labels().fontColor("#e0e0e0");
            chart.xAxis().title().fontColor("#e0e0e0");
            chart.yAxis().labels().fontColor("#e0e0e0");
            chart.yAxis().title().fontColor("#e0e0e0");
            // Also update series color if needed
            // series.stroke("#fdbb2d"); 
        } else {
            chart.background().fill("white");
            chart.title().fontColor("#333");
            chart.xAxis().labels().fontColor("#333");
            chart.xAxis().title().fontColor("#333");
            chart.yAxis().labels().fontColor("#333");
            chart.yAxis().title().fontColor("#333");
        }
    }

    updateChartTheme();

    // Устанавливаем контейнер и рисуем график
    chart.container("scoreChart");
    chart.draw();
});