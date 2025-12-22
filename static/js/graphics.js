anychart.onDocumentReady(function () {

    // create data
    var data = [
      ["January", 10000],
      ["February", 12000],
      ["March", 18000],
      ["April", 11000],
      ["May", 9000]
    ];

    // create a chart
    var chart = anychart.line();

    // create a line series and set the data
    var series = chart.line(data);

    // set the chart title
    chart.title("Ваши очки по дням");

    // set the titles of the axes
    var xAxis = chart.xAxis();
    xAxis.title("Дата");
    var yAxis = chart.yAxis();
    yAxis.title("Очки");

    // set the container id
    chart.container("scoreChart");

    // initiate drawing the chart
    chart.draw();
});