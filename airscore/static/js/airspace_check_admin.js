var dropdown = {
  h_boundary_penalty: $('#h_boundary_penalty'),
  v_boundary_penalty: $('#v_boundary_penalty'),
  h_max_penalty: $('#h_max_penalty'),
  v_max_penalty: $('#v_max_penalty'),
  func: $('#function')
};

var checkbox = {
  h_v: $('#h_v'),
  double_step: $('#double_step')
}

function show_boundary() {
  $('#h_boundary_section').hide();
  $('#v_boundary_section').hide();
  if ( checkbox.double_step.is(":checked") ) {
    $('#h_boundary_section').show();
    $('#v_boundary_section').show();
  }
}

function show_v_limit() {
  $('#v_limits').hide();
  if ( checkbox.h_v.is(":checked") ) { $('#v_limits').show(); }
}

function update_parameters(){
  if ( dropdown.func.val() == 'linear' ) {
    $('#double_step_div').show();
    $('#h_max_penalty_div').show();
    $('#v_max_penalty_div').show();
    show_boundary();
    show_v_limit();
  }
  else {
    $('#double_step_div').hide();
    $('#h_boundary_section').hide();
    $('#v_boundary_section').hide();
    $('#h_max_penalty').val('1.0');
    $('#v_max_penalty').val('1.0');
    $('#h_max_penalty_div').hide();
    $('#v_max_penalty_div').hide();
    show_v_limit();
  }
}

function get_chart_data(side) {
  let notif_dist = parseInt(parseInt($('#notification_distance').val()));
  let ol = $('#'+side+'_outer_limit');
  let b = $('#'+side+'_boundary');
  let bp = $('#'+side+'_boundary_penalty');
  let il = $('#'+side+'_inner_limit');
  let ip = $('#'+side+'_max_penalty');

  let def = {
    outer_limit: parseInt(ol.val()),
    border: parseInt(b.val()),
    border_penalty: parseFloat(bp.val()),
    inner_limit: parseInt(il.val()),
    inner_penalty: parseFloat(ip.val())
  }

  let mylabels = [def.inner_limit];
  let mydata = [def.inner_penalty*100];

  let x = Math.round(def.inner_limit / 10) * 10;
  do {
    if ( checkbox.double_step.is(":checked") && def.border < x && !mylabels.includes(def.border) ) {
      mylabels.push(def.border);
      mydata.push(def.border_penalty*100);
    }
    if ( def.outer_limit < x && !mylabels.includes(def.outer_limit) ) {
      mylabels.push(def.outer_limit);
      mydata.push(0);
    }
    if ( notif_dist > def.outer_limit && notif_dist < x && !mylabels.includes(notif_dist) ) {
      mylabels.push(notif_dist);
      mydata.push(0);
    }
    if ( !mylabels.includes(x) ) {
      mylabels.push(x);
      mydata.push( x < def.outer_limit ? calc_pen(x, def) : 0 );
    }
    x += 10;
  }
  while ( x <= Math.max(def.outer_limit, notif_dist) );

  return { data: mydata, labels: mylabels };
}

function create_dataset(label, data, rgb, fill) {
  let color = 'rgba('+rgb+',1)';
  let faded_color = 'rgba('+rgb+',0.4)';
  return {
    label: label,
    fill: (fill === false ? false : true),
    lineTension: 0.1,
    backgroundColor: faded_color,
    borderColor: color,
    borderCapStyle: 'butt',
    borderDash: [],
    borderDashOffset: 0.0,
    borderJoinStyle: 'miter',
    pointBorderColor: color,
    pointBackgroundColor: "#fff",
    pointBorderWidth: 1,
    pointHoverRadius: 5,
    pointHoverBackgroundColor: color,
    pointHoverBorderColor: "rgba(220,220,220,1)",
    pointHoverBorderWidth: 2,
    pointRadius: 1,
    pointHitRadius: 10,
    data : data,
    spanGaps: false
  }
}

function draw_charts() {
  [charts.h, charts.v].forEach( el => {
    let chart_data = get_chart_data(el.side);
  //  console.log(chart_data);

    let dataset = create_dataset('Penalty (% of pilot score)', chart_data.data, "192,75,75", true);
  //  console.log(dataset);
    let min_value = chart_data.labels[0];
    let max_value = chart_data.labels.slice(-1)[0];
    console.log(min_value, max_value);

    // define the chart data
    let chartData = {
      labels : chart_data.labels,
      datasets : [
        dataset
      ]
    };

    // get chart canvas
    let ctx = el.canvas;

    // create the chart using the chart canvas
    el.object = new Chart(ctx, {
      type: 'line',
      data: chartData,
      options: {
        legend: {
          display: true
        },
        tooltips: {
          enabled: true,
        },
        scales: {
          y: {
            max: 100,
            min: 0,
            ticks: {
              stepSize: 10
            }
          },
          x: {
            max: max_value,
            min: min_value,
            type: 'linear',
            title: {
              display: true,
              text: 'Distance in meters from airspace border (negative inside)'
            }
          }
        }
      }
    });
  });
}

function update_charts() {
  update_chart(charts.h);
  if ( checkbox.h_v.is(":checked") ) {
    update_chart(charts.v);
  }
}

function update_chart(chart) {
  remove_data(chart.object);
  let chart_data = get_chart_data(chart.side);
  chart.object.data.labels = chart_data.labels;
  chart.object.data.datasets[0].data = chart_data.data;
  chart.object.options.scales.x.min = chart_data.labels[0];
  chart.object.options.scales.x.max = chart_data.labels.slice(-1)[0];
  chart.object.update();
}

function remove_data(cobj) {
  cobj.data.labels.pop();
  cobj.data.datasets[0].data.pop();
  cobj.update();
}

function calc_pen(x, def) {
  if ( dropdown.func.val() == 'linear' ) {
    if ( checkbox.double_step.is(":checked") ) {
      let outer = def.outer_limit - def.border;
      if ( x > def.border ) {
        let pen_m = def.border_penalty / outer;
        return Math.round((def.outer_limit - x) * pen_m * 10 * 100) / 10 ;
      }
      else {
        let inner = def.border - def.inner_limit;
        let pen_m = (def.inner_penalty - def.border_penalty) / inner
        return def.border_penalty * 100 + Math.round((def.border - x) * pen_m * 10 * 100) / 10;
      }
    }
    else {
      let total = def.outer_limit - def.inner_limit;
      let pen_m = def.inner_penalty / total;
      return Math.round((def.outer_limit - x) * pen_m * 10 * 100) / 10;
    }
  }
  else if ( dropdown.func.val() == 'non-linear' ) {
    let total = def.outer_limit - def.inner_limit;
    let pen_m = def.inner_penalty / total;
    return Math.round(Math.pow((def.outer_limit - x) / total, Math.log2(10)) * 100 * 10) / 10;
  }
}

var charts = {
  h: {
    side: 'h',
    canvas: document.getElementById('h-chart').getContext("2d"),
    object: new Object()
  },
  v: {
    side: 'v',
    canvas: document.getElementById('v-chart').getContext("2d"),
    object: new Object()
  }
};
var isSubmitting = false;

$(document).ready(function() {
  $('#airspace_check_form').data('initial-state', $('#airspace_check_form').serialize());
  show_boundary();
  show_v_limit();
  update_parameters();
  draw_charts();

  // event listener to formula dropdown change
  dropdown.func.on('change', function() {
    console.log('func changed');
    update_parameters();
  });

  // vertical limits display checkbox value change
  checkbox.h_v.change(function() {
    console.log('hv changed');
    show_v_limit();
  });

  // double steps checkbox value change
  checkbox.double_step.change(function() {
    console.log('ds changed '+ checkbox.double_step.is(":checked"));
    show_boundary();
    update_charts();
  });

  // inform when saving changings is needed
  $('#airspace_check_form :input').change(function(){
    if (!isSubmitting && $('#airspace_check_form').serialize() != $('#airspace_check_form').data('initial-state')) {
      $('#airspace_check_save_button').removeClass( "btn-outline-secondary" ).addClass( "btn-warning" );
      $('#save_button_warning_text').addClass('bg-warning').html('Parameters are changed and need to be saved');
    }
    else {
      $('#airspace_check_save_button').removeClass( "btn-warning" ).addClass( "btn-outline-secondary" );
      $('#save_button_warning_text').removeClass('bg-warning').html('');
    }
    update_charts();
  });

  $('#airspace_check_form').submit( function() {
    isSubmitting = true
  });

  $(window).on('beforeunload', function() {
    if (!isSubmitting && $('#airspace_check_form').serialize() != $('#airspace_check_form').data('initial-state')) {
      return 'You have unsaved changes which will not be saved.'
    }
  });

});