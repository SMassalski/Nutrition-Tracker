import "jquery";
import 'bootstrap';
import {
    fetchLastMonthCalorie,
    fetchLastMonthIntake,
    fetchLastMonthWeight,
    MacrosPieChart
} from './chart_util.js';
import autoConvertHeight from './util.js'

// HTMX
window.htmx = require('htmx.org');
require('htmx.org/dist/ext/response-targets.js');

// Masonry
var Masonry = require('masonry-layout');
var jQueryBridget = require('jquery-bridget')
jQueryBridget( 'masonry', Masonry, $ );

window.setUpGrid = function setUpGrid() {
    $('.grid').masonry({
        columnWidth: ".grid-item",
        itemSelector: ".grid-item",
    });
}

window.autoConvertHeight = autoConvertHeight;

window.MacrosPieChart = MacrosPieChart;
window.fetchLastMonthCalorie = fetchLastMonthCalorie;
window.fetchLastMonthIntake = fetchLastMonthIntake;
window.fetchLastMonthWeight = fetchLastMonthWeight;
