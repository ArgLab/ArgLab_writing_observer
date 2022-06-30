if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside.clientside = {
    make_draggable: function() {
        let args = Array.from(arguments);
        var els = [];
        setTimeout(function() {

            for (i = 0; i < args.length; i++){
                els[i] = document.getElementById(args[i]);
                window.console.log(els[i]);
            }
            dragula(els)
        }, 1)
        return window.dash_clientside.no_update
    }
}
