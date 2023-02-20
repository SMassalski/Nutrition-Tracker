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
