/**
 * Chart wrappers for easy themed charts.
 */
// TODO: Length independent color palette
const style = getComputedStyle(document.documentElement)
const palette = style.getPropertyValue("--chart_palette").split(", ") || ["#33658A", "#86BBD8", "#2B8C69", "#F6AE2D", "#F26419"];
const primary = style.getPropertyValue("--chart_primary") || palette[0] || "#86BBD8";
const annotation_color = style.getPropertyValue("--chart_annotation") || palette[palette.length - 1] || "#F26419";

/**
 * Draw a chart.js pie chart in a canvas element
 * @param {string} elementId - The id of the canvas.
 * @param {Object} data - Mapping in the format of {<label>: <value>}.
 */
const pieChart = function(elementId, data) {

    const ctx = document.getElementById(elementId);

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(data),
            datasets: [
                {
                    data: Object.values(data),
                    backgroundColor: palette
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
    // Max of the array of values and targets + 10
    const yMax = Math.max(values.reduce((a, b) => Math.max(a, b), -Infinity), target_min || 0, target_max || 0) + 10

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
    annotations = {}

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
            borderColor: primary,
            borderWidth: 1,
            borderDash: [5, 5],
            label: {
                content: "Avg: " + avg.toFixed(1),
                display: true,
                backgroundColor: 'rgba(0, 0, 0, 0)',
                color: primary,
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
        amount_min = null;
        amount_max = null;
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
