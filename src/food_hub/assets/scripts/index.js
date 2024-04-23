import "jquery";

// Bootstrap
import 'bootstrap/js/dist/alert';
import 'bootstrap/js/dist/button';
// import 'bootstrap/js/dist/carousel';
// import 'bootstrap/js/dist/collapse';
import 'bootstrap/js/dist/dropdown';
import 'bootstrap/js/dist/modal';
// import 'bootstrap/js/dist/popover';
// import 'bootstrap/js/dist/scrollspy';
import 'bootstrap/js/dist/tab';
// import 'bootstrap/js/dist/toast';
import 'bootstrap/js/dist/tooltip';

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
