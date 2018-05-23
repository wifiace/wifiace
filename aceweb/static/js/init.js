
// function for adding values in between the string.
String.prototype.formatUnicorn = String.prototype.formatUnicorn ||
function () {
    "use strict";
    var str = this.toString();
    if (arguments.length) {
        var t = typeof arguments[0];
        var key;
        var args = ("string" === t || "number" === t) ?
            Array.prototype.slice.call(arguments)
            : arguments[0];

        for (key in args) {
            str = str.replace(new RegExp("\\{" + key + "\\}", "gi"), args[key]);
        }
    }

    return str;
};

// template ajax
/*
$.ajax({
url: '/recon/start_deauth',
data: {},
type: 'GET',
beforeSend: function(){

},
complete: function(){

},
success: function(response) {
    console.log(response);
},
error: function(error) {
    console.log(error);
}
});
*/
