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
const primary = style.getPropertyValue("--chart_primary") || palette[0] || "#86BBD8";
const annotation_color = style.getPropertyValue("--chart_annotation") || palette[palette.length - 1] || "#F26419";
const colorMap = {
      "Lipid": palette[3],
      "Protein": palette[0],
      "Carbohydrate": palette[1],
      "Alcohol": palette[2]
}

/**
 * Draw a chart.js pie chart in a canvas element
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
 * Draw a chart.js line chart in a canvas element
 * @param {string} elementId - The id of the canvas.
 * @param {Object} data - Mapping in the format of {<label>: <value>}.
 */
const lineChart = function({elementId, data, target, title}) {

    const ctx = document.getElementById(elementId);
    const values = Object.values(data);
    // Max of the array of values and set target + 2
    const yMax = Math.max(values.reduce((a, b) => Math.max(a, b), -Infinity), target || 0) + 2

    const options = {
        responsive: true,

        //Scales
        scales: {
            y: {
                beginAtZero: true,

                max: yMax
            }
        },

        // Title
        plugins: {
            legend: false,
            title: {
                display: !!(title),
                text: title
            }
        }

    }

    // Target line annotation
    if( target ) {
        options.plugins.annotation = {
            annotations: {
                line1: {
                    type: 'line',
                    yMin: target,
                    yMax: target,
                    borderColor: annotation_color,
                    borderWidth: 1,
                }
            }
        }
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: Object.keys(data), //This will need to be thinned
            datasets: [
                {
                    data: values,
                    backgroundColor: primary
                }
            ]
        },
        options: options
    });
}


/**
 * Draw a chart.js line chart in a canvas element
 * @param {string} elementId - The id of the canvas.
 * @param {Object} data - Mapping in the format of {<label>: <value>}.
 */
const monthIntakeChart = function({elementId, data, target_min, target_max, avg, title}) {

    const ctx = document.getElementById(elementId);
    const values = Object.values(data);
    let yMax = Math.max(...values, target_min||0, target_max||0) * 1.1;
    yMax = Math.round(yMax * 10) / 10;

    const options = {
        responsive: true,

        //Scales
        scales: {
            y: {
                beginAtZero: true,
                max: yMax
            }
        },

        // Title
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
        annotations.min_target = {
            type: 'line',
            yMin: target_min,
            yMax: target_min,
            borderColor: annotation_color,
            borderWidth: 1,
            label: {
                content: "Min: " + target_min.toFixed(1),
                display: true,
                backgroundColor: 'rgba(0, 0, 0, 0)',
                color: annotation_color,
                yAdjust: -10,
            },
        }
    }

    if (target_max !== null ) {
        annotations.max_target = {
            type: 'line',
            yMin: target_max,
            yMax: target_max,
            borderColor: annotation_color,
            borderWidth: 1,
            label: {
                content: "Max: " + target_max.toFixed(1),
                display: true,
                backgroundColor: 'rgba(0, 0, 0, 0)',
                color: annotation_color,
                yAdjust: 700 / yMax, // Empirically determined value
            },
        }
    }

    if (avg !== null ) {
        annotations.average = {
            type: 'line',
            yMin: avg,
            yMax: avg,
            borderColor: "#33658A",
            borderWidth: 1,
            borderDash: [5, 5],
            label: {
                content: "Avg: " + avg.toFixed(1),
                display: true,
                backgroundColor: 'rgba(0, 0, 0, 0)',
                color: "#33658A",
                position: "start",
                yAdjust: -10,
            },
        }
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
                    backgroundColor: primary
                }
            ]
        },
        options: options
    });
}


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


const fetchLastMonthWeight = function (url, chartId) {
    const chart = Chart.getChart(chartId)
    $.get(url, function(data) {
        if (chart) {
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

            //Scales
            scales: {
                y: {
                    min: yMin,
                    max: yMax,
                }
            },

            // Title
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
                        backgroundColor: primary
                    }
                ]
            },
            options: options
        });
    });
}


const fetchLastMonthCalorie = function (url, chartId) {
    $.get(url, function(data) {
        const ctx = document.getElementById(chartId);
        const values = Object.values(data.caloric_intake);
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

            //Scales
            scales: {
                y: {
                    stacked: true,
                    max: yMax
                },
                x: {
                    stacked: true
                }
            },

            // Title
            plugins: {
                legend: true,
                title: {
                    display: true,
                    text: "Caloric Intake"
                }
            },

            annotations: {
                average: {
                    type: 'line',
                    yMin: avg,
                    yMax: avg,
                    borderColor: "#33658A",
                    borderWidth: 1,
                    borderDash: [5, 5],
                    label: {
                        content: "Avg: " + avg.toFixed(1),
                        display: true,
                        backgroundColor: 'rgba(0, 0, 0, 0)',
                        color: "#33658A",
                        position: "start",
                        yAdjust: -10,
                    }
                }
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
