if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.minty_colors = ['#78c2ad', '#f3969a', '#6cc3d5', '#ffce67', '#ff7851']
window.drake = dragula();
window.dash_clientside.clientside = {
    make_draggable: function() {
        let args = Array.from(arguments)[0];
        var els = [];
        window.drake.destroy();
        setTimeout(function() {
            for (i = 0; i < args.length; i++){
                els[i] = document.getElementById(JSON.stringify(args[i]));
            }
            window.drake = dragula(els);
        }, 1)
        return window.dash_clientside.no_update
    },

    sort_students: function(value, data, options, students) {
        let orders = Array(students).fill(window.dash_clientside.no_update)
        if (!value | value === 'none') {
            return [orders, window.dash_clientside.no_update]
        }
        const option = options.filter(obj => {return obj.value === value});
        for (let i = 0; i < data.length; i++) {
            orders[i] = `order-${4 - data[i].indicators[value]['value']}`;
        }
        return [orders, option[0].label]
    },

    populate_student_data: function(msg, old_data, students) {
        if (!msg) {
            return old_data;
        }
        let updates = Array(students).fill(window.dash_clientside.no_update);
        const data = JSON.parse(msg.data);
        for (const up of data) {
            let index = up.id;
            updates[index] = {...old_data[index], ...up};
            updates[index] = _.merge(old_data[index], up);
        }
        return updates;
    },

    open_offcanvas: function(clicks, is_open) {
        if(clicks) {
            return !is_open
        }
        return is_open
    },

    // TODO there is probably a better way to handle the following functions
    toggle_indicators_checklist: function(values) {
        if (values.includes('indicators')) {
            return true;
        }
        return false;
    },

    toggle_metrics_checklist: function(values) {
        if (values.includes('metrics')) {
            return true;
        }
        return false;
    },

    toggle_text_checklist: function(values) {
        if (values.includes('text')) {
            return true;
        }
        return false;
    },

    show_hide_data: function(values, metrics, indicators, students) {
        const l = values.concat(metrics).concat(indicators);
        return Array(students).fill(l)
    },

    send_websocket: function (reports, student) {
        if (typeof student === "undefined") {
            return window.dash_clientside.no_update;
        }
        const msg = {"reports":reports, "student":student};
        return JSON.stringify(msg);
    },

    update_report_graph: function(msg) {
        // TODO figure out a better way to update the data
        // since we need to update the traces as well, I'm not sure
        // its feasible to simple extend the data, might
        // have to update the data of the figure
        // eventually we'll have a lot of analysis so we having a trace
        // for each one is probably not the best practice
        if (!msg) {
            return window.dash_clientside.no_update;
        }
        const data = JSON.parse(msg.data);
        return [data, [0, 1, 2, 3], 4];
    }
}
