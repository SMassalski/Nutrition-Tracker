/*
Utility functions.
*/

/**
 * Automatically convert the height value in centimeters to ft. and in.
 * and vice versa.
 * Set the appropriate fields value to the converted value.
 * @param {string} cm_selector - The selector of the field holding the
 * value in centimeters.
 * @param {string} ft_selector - The selector of the field holding the
 * value in feet.
 * @param {string} in_selector - The selector of the field holding the
 * value in inches.
 */
export const autoConvertHeight = function autoConvertHeight(cm_selector, ft_selector, in_selector) {
    //

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
