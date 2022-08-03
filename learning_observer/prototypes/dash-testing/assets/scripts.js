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

    update_student_card: function(data) {
        if(!data) {
            return ['', '', '', '', '', '', '', '', ''];
        }
        // TODO incorporate the no_update exception,
        // so components that did not change, don't update
        // should lead to better performance, so we don't
        // initiate callbacks down the chain if we don't need to
        return [
            `${data.sentences} sentences`,
            `${data.paragraphs} paragraphs`,
            `${data.time_on_task} minutes on task`,
            `${data.unique_words} unique words`,
            data.text,
            data.transition_words,
            data.use_of_synonyms,
            data.sv_agreement,
            data.formal_language,
        ];
    },

    update_student_outline: function(order_by, data) {
        if (!data) {
            return ['gray-400', '']
        }
        const options = ['secondary', 'warning', 'primary'];
        const value = data[order_by];
        if (!value) {
            return ['gray-400', '']
        }
        return [options[value-1], `order-${4-value}`];
    },

    sort_students: function(value, options, students) {
        if (!value) {
            return [Array(students).fill(window.dash_clientside.no_update), window.dash_clientside.no_update]
        }
        const option = options.filter(obj => {return obj.value === value});
        return [Array(students).fill(value), option[0].label]
    },

    populate_student_data: function(msg, old_data, students) {
        if (!msg) {
            return []
        }
        let updates = Array(students).fill(window.dash_clientside.no_update);
        const data = JSON.parse(msg.data);
        for (const up of data) {
            let index = up.id
            updates[index] = {...old_data[index], ...up};
        }
        return updates;
    },

    update_student_progress_bars: function(value) {
        const options = ['secondary', 'warning', 'primary'];
        return options[value-1];
    },

    open_offcanvas: function(clicks, is_open) {
        if(clicks) {
            return !is_open
        }
        return is_open
    },

    toggle_progress_checklist: function(values) {
        if (values.includes('progress')) {
            return true;
        }
        return false;
    },

    hide_show_attributes: function(values, progress, students) {
        let sentence_badge = 'd-none';
        let paragraph_badge = 'd-none';
        let time_on_task_badge = 'd-none';
        let unique_words_badge = 'd-none';
        let text_area = 'd-none';
        let progress_div = 'd-none';
        let transition_words = 'd-none';
        let use_of_synonyms = 'd-none';
        let sv_agreement = 'd-none';
        let formal_language = 'd-none';
        if (values.includes('sentences')) {
            sentence_badge = 'mb-1';
        }
        if (values.includes('paragraphs')) {
            paragraph_badge = 'mb-1';
        }
        if (values.includes('time_on_task')) {
            time_on_task_badge = 'mb-1';
        }
        if (values.includes('unique_words')) {
            unique_words_badge = 'mb-1';
        }
        if (values.includes('text')) {
            text_area = '';
        }
        if (values.includes('progress')) {
            // TODO there is probably a better way to do this
            // in more algorithmic way
            // requires a deeper discussion on what is shown
            progress_div = ''
            if (progress.includes('transition_words')) {
                transition_words = ''
            }
            if (progress.includes('use_of_synonyms')) {
                use_of_synonyms = ''
            }
            if (progress.includes('sv_agreement')) {
                sv_agreement = ''
            }
            if (progress.includes('formal_language')) {
                formal_language = ''
            }
        }
        return [
            Array(students).fill(sentence_badge),
            Array(students).fill(paragraph_badge),
            Array(students).fill(time_on_task_badge),
            Array(students).fill(unique_words_badge),
            Array(students).fill(text_area),
            Array(students).fill(progress_div),
            Array(students).fill(transition_words),
            Array(students).fill(use_of_synonyms),
            Array(students).fill(sv_agreement),
            Array(students).fill(formal_language),
        ]
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
