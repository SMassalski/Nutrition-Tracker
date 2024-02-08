import 'htmx.org';
import "jquery";
import 'bootstrap';
import 'admin-lte';
import Chart from 'chart.js/auto'; // TODO: needs to be optimized
import annotationPlugin from 'chartjs-plugin-annotation';

Chart.register(annotationPlugin);
window.Chart = Chart;
window.htmx = require('htmx.org');
require('htmx.org/dist/ext/response-targets.js');

window.autoConvertHeight = function autoConvertHeight(cm_selector, ft_selector, in_selector) {
    // Automatically convert the height value in centimeters to feet and inches and vice versa.
    // Set the appropriate fields value to the converted value.

    let cm_field = $(cm_selector);
    let ft_field = $(ft_selector);
    let in_field = $(in_selector);

    // Convert on load
    ft_field.val(Math.floor(cm_field.val() / 30.48));
    in_field.val(Math.round((cm_field.val() / 30.48 - ft_field.val()) * 12));


    cm_field.change(function() {
        ft_field.val(Math.floor($(this).val() / 30.48));
        in_field.val(Math.round(($(this).val() / 30.48 - ft_field.val()) * 12));
    });
    ft_field.change(function() {
        cm_field.val(Math.round((parseInt(ft_field.val()) + parseInt(in_field.val()) / 12) * 30.48));
    });
    in_field.change(function() {
        cm_field.val(Math.round((parseInt(ft_field.val()) + parseInt(in_field.val()) / 12) * 30.48));
    });
}
