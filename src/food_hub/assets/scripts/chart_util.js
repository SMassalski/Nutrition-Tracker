/**
 * Charts.js wrappers for easy themed charts.
 */
 import {
    Chart,
    LineController,
    LineElement,
    PointElement,
    PieController,
    ArcElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Title,
    Legend,
    BarController,
    BarElement
 } from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';

Chart.register(
    BarController,
    BarElement,
    LineController,
    LineElement,
    PointElement,
    PieController,
    ArcElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Title,
    Legend,
    annotationPlugin
);


const style = getComputedStyle(document.documentElement)
const palette = style.getPropertyValue("--chart_palette").split(", ") || ["#33658A", "#86BBD8", "#2B8C69", "#F6AE2D", "#F26419"];
const [primary, info, success, warning, danger, ...rest] = palette;
const chartPrimary = style.getPropertyValue("--chart_primary") || palette[1] || "#86BBD8";
const annotation_color = style.getPropertyValue("--chart_annotation") || palette[palette.length - 1] || "#F26419";
const colorMap = {
      "Lipid": warning,
      "Protein": primary,
      "Carbohydrate": info,
      "Alcohol": success
}

/**
 * Draw a pie chart in a canvas element colored based on the label.
 * @param {string} elementId - The id of the canvas.
 * @param {Object} data - Mapping in the format of {<label>: <value>}.
 */
const MacrosPieChart = function(elementId, data) {

    let labels = Object.keys(data)
    let colors = [];
    for (let i=0; i < labels.length; i++) {
        colors[i] = colorMap[labels[i]];
    }

    const ctx = document.getElementById(elementId);

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [
                {
                    data: Object.values(data),
                    backgroundColor: colors
                }
            ]
        },
        options: {
            responsive: true,
        }
    });
}

/**
 * Generate a line annotation options object.
 * @param {Number} value - The y value of the annotation.
 * @param {string} label - The label prefix.
 * The final label will be '<label>: <value>'.
 * @param {string} color - The color of the line and label
 * @param {boolean} dashed - If true the annotation line will be dashed
 * @param {string|Number} labelPosition - Either "start", "center",
 * "end" or a percent position
 * @returns {Object} - The generated options.
 */
const makeAnnotation = function(value, label, color, dashed=false, labelPosition="center") {

    // Set line dash
    let lineDash = [];
    if (dashed) {
        lineDash= [5, 5];
    }

    return {
        type: 'line',
        yMin: value,
        yMax: value,
        borderColor: color,
        borderWidth: 1,
        borderDash: lineDash,
        label: {
            content: label + ": " + value.toFixed(1),
            display: true,
            backgroundColor: color,
            color: "white",
            position: labelPosition
        },
    }
}

/**
 * Generate the 'average' annotation options object.
 * @param {Number} value - The value of the average.
 * @returns {Object} - The generated options.
 */
const makeAvgAnnotation = function(value) {
    return makeAnnotation(value, "Avg", primary, true, "start");
}


/**
 * Draw a line chart in the canvas element with optional annotations for
 * the min, max, and avg values.
 * @param {string} elementId - The id of the canvas.
 * @param {Number} target_min - The value for the min annotation
 * @param {Number} target_max- The value for the max annotation
 * @param {Number} avg - The value for the avg annotation
 * @param {Object} data - Mapping in the format of {<label>: <value>}.
 */
const monthIntakeChart = function({elementId, data, target_min, target_max, avg, title}) {

    const ctx = document.getElementById(elementId);
    const values = Object.values(data);
    let yMax = Math.max(...values, target_min||0, target_max||0) * 1.1;
    yMax = Math.round(yMax * 10) / 10;

    const options = {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true,
                max: yMax
            }
        },
        plugins: {
            legend: false,
            title: {
                display: !!(title),
                text: title
            }
        }

    }

    // Annotations
    let annotations = {}

    if (target_min !== null ) {
        annotations.min_target = makeAnnotation(target_min, "Min", annotation_color);
    }
    if (target_max !== null ) {
        annotations.max_target = makeAnnotation(target_max, "Max", annotation_color);
    }
    if (avg !== null ) {
        annotations.average = makeAvgAnnotation(avg);
    }
    if( Object.keys(annotations).length != 0 ) {
        options.plugins.annotation = {
            annotations: annotations
        }
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: Object.keys(data),
            datasets: [
                {
                    data: values,
                    backgroundColor: chartPrimary
                }
            ]
        },
        options: options
    });
}

/**
 * Fetch data from url and draw a monthIntakeChart in a canvas element.
 * @param {string} url - The url from where the data can be retrieved.
 * @param {string} chartId - The id of the canvas element.
 */
const fetchLastMonthIntake = function (url, chartId) {
    $.get(url, function(data) {
        let amount_min = null;
        let amount_max = null;
        for (let i=0; i < data.recommendations.length; i++) {

            // Recommendation selection
            if (data.recommendations[i].dri_type == "AMDR") {
                amount_min = data.recommendations[i].amount_min;
                amount_max = data.recommendations[i].amount_max;
                break;
            }
            amount_min = data.recommendations[i].amount_min;
            amount_max = data.recommendations[i].amount_max;
        };

        monthIntakeChart({
            elementId: chartId,
            data: data.intakes,
            target_min: amount_min,
            target_max: amount_max,
            avg: data.avg,
            title: data.name
        });
    });
}

/**
 * Fetch data from url and draw a line chart in a canvas element.
 *
 * Redraw if chart already exists.
 * @param {string} url - The url from where the data can be retrieved.
 * @param {string} chartId - The id of the canvas element.
 */
const fetchLastMonthWeight = function (url, chartId) {
    const chart = Chart.getChart(chartId)
    $.get(url, function(data) {
        if (chart) {  // Update chart if exists
            chart.data.datasets[0].data = Object.values(data);
            chart.data.labels = Object.keys(data);
            chart.update();
            return;
        }
        const ctx = document.getElementById(chartId);
        const values = Object.values(data);

        const yMax = Math.max(...values) + 5
        const yMin = Math.min(...values) - 5

        const options = {
            responsive: true,
            scales: {
                y: {
                    min: yMin,
                    max: yMax,
                }
            },
            plugins: {
                legend: false,
                title: {
                    display: true,
                    text: "Weight (kg)"
                }
            }

        }

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: Object.keys(data),
                datasets: [
                    {
                        data: values,
                        backgroundColor: chartPrimary
                    }
                ]
            },
            options: options
        });
    });
}

/**
 * Fetch data from url and draw a calorie chart in a canvas element.
 *
 * The chart is a stacked bar chart with an average annotation.
 * @param {string} url - The url from where the data can be retrieved.
 * @param {string} chartId - The id of the canvas element.
 */
const fetchLastMonthCalorie = function (url, chartId) {
    $.get(url, function(data) {
        const ctx = document.getElementById(chartId);
        const avg = data.avg;
        let datasets = [];

        let totalCalories = new Array(data.caloric_intake.dates.length);
        totalCalories.fill(0);

        Object.keys(data.caloric_intake.values).forEach(element => {
            let values = data.caloric_intake.values[element];
            datasets.push({
                label: element,
                data: values,
                backgroundColor: colorMap[element]
            });
            totalCalories = totalCalories.map((element, idx) => element + values[idx]);
        });

        const yMax = Math.max(...totalCalories) * 1.1;

        const options = {
            responsive: true,
            scales: {
                y: {
                    stacked: true,
                    max: yMax
                },
                x: {
                    stacked: true
                }
            },
            plugins: {
                legend: true,
                title: {
                    display: true,
                    text: "Caloric Intake"
                }
            },

            annotations: {
                average: makeAvgAnnotation(avg)
            }
        }

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.caloric_intake.dates,
                datasets: datasets
            },
            options: options
        });
    });
}

export {MacrosPieChart, fetchLastMonthCalorie, fetchLastMonthIntake, fetchLastMonthWeight};
