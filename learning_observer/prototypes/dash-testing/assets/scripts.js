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

    update_student_card: function(msg) {
        if(!msg) {
            return ['', '', '', '', '', {}];
        }
        const data = JSON.parse(msg.data);
        const sentences = `${data.sentences} sentences`
        const paragraphs = `${data.paragraphs} paragraphs`
        const words = `${data.unique_words} unique words`
        const graph ={
            data: [{
                values: data.data,
                type: 'pie',
                marker: {
                    colors: window.minty_colors,
                    line: {
                        color: '#000000',
                        width: 1
                    }
                }
            }],
            layout: {
                showlegend: false,
                height: 300,
                margin: {
                    t: 5,
                    b: 5
                }
            }
        }
        return [data.text, data.class_name, sentences, paragraphs, words, graph];
    },

    update_analysis_data: function(msg) {
        if(!msg){
            return {
                data: [{y: [], type: "scatter"}]
            };
        }
        const data = JSON.parse(msg.data);
        return {
            data: [{
                y: data.data,
                type: data.id,
                marker: {
                    color: window.minty_colors[0]
                }
            }],
            layout: {
                title: data.id,
            }
        };
    },

    open_offcanvas: function(clicks, is_open) {
        if(clicks) {
            return !is_open
        }
        return is_open
    },

    hide_show_attributes: function(values) {
        const students = 10;
        let summary_class = 'd-none';
        let sentences_class = 'd-none';
        let paragraph_class = 'd-none';
        let unique_class = 'd-none';
        let chart_class = 'd-none';
        if (values.includes('summary')) {
            summary_class = '';
        }
        if (values.includes('sentences')) {
            sentences_class = '';
        }
        if (values.includes('paragraphs')) {
            paragraph_class = '';
        }
        if (values.includes('unique_words')) {
            unique_class = '';
        }
        if (values.includes('chart')) {
            chart_class = '';
        }
        console.log(sentences_class)
        return [
            Array(students).fill(summary_class),
            Array(students).fill(sentences_class),
            Array(students).fill(paragraph_class),
            Array(students).fill(unique_class),
            Array(students).fill(chart_class)
        ]
    }
}
