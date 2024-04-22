import "jquery";
import 'bootstrap';
import * as charts from './chart_util.js';
import * as util from './util.js'

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

// Local
window.util = util;
window.charts = charts;
