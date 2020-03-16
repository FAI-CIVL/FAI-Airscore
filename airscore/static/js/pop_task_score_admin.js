function populate_task_scores(taskid, filename){


    $('#task_result').dataTable({
        ajax: '/users/_get_task_score_from_file/' + taskid + '/' + filename,
        paging: false,
        destroy: true,
        searching: true,
        info: false,
        columns: [
            {data: 'rank', name:'#'},
            {data: 'name', name:'Pilot'},
            {data: 'SSS', name:'SS'},
            {data: 'ESS', name:'ES'},
            {data: 'time', name:'Time'},
            {data: 'altbonus', name:'altbonus'},
            {data: 'distance', name:'Kms'},
            {data: 'speedP', name:'Spd'},
            {data: 'leadP', name:'leading'},
            {data: 'arrivalP', name:'Arv'},
            {data: 'distanceP', name:'Dst'},
            {data: 'penalty', name:'Pen'},
            {data: 'score', name:'Tot'}
           ],
        "language": {
        "emptyTable":     "Error: result file not found"
    }
    });

}

