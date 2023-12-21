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
