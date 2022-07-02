if (!window.dash_clientside) {
    window.dash_clientside = {};
}
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
        if(!msg){return "No data";}
        const data = JSON.parse(msg.data);
        const sentences = `${data.sentences} sentences`
        const paragraphs = `${data.paragraphs} sentences`
        return [data.text, data.class_name, sentences, paragraphs];
    },

    update_analysis_data: function(msg) {
        if(!msg){
            return {
                data: [{y: [], type: "scatter"}]
            };
        }
        const data = JSON.parse(msg.data);
        return {
            data: [{y: data.data, type: data.id}],
            layout: {
                title: data.id
            }
        };
    }
}
