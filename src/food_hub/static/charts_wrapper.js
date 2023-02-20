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
