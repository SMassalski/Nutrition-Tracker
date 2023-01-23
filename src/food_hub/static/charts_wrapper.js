const palette = getComputedStyle(document.documentElement)
    .getPropertyValue("--chart_palette") || ["#33658A", "#86BBD8", "#2B8C69", "#F6AE2D", "#F26419"];

/*
const rangedChart = function(elementId, data, lower, upper) {
    const chart = new Chart (document.getElementById(elementId), {
        type: 'bar',
        data: {

        }
    });
};
*/
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
