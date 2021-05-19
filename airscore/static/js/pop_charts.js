$(document).ready(function() {
  var charts = {
    h_v: !( penalty.v_outer_limit === penalty.h_outer_limit && penalty.v_boundary === penalty.h_boundary &&
            penalty.v_boundary_penalty === penalty.h_boundary_penalty && penalty.v_inner_limit === penalty.h_inner_limit &&
            penalty.v_inner_penalty === penalty.h_inner_penalty),
    func: penalty['function'],
    double_step: !(penalty.h_boundary_penalty === penalty.h_inner_penalty),
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

  create_charts(charts);
});

function get_chart_data(charts, side) {
  let notif_dist = penalty.notification_distance;

  //get penalty parameters
  let def = {
    outer_limit: penalty[side+'_outer_limit'],
    border: penalty[side+'_boundary'],
    border_penalty: penalty[side+'_boundary_penalty'],
    inner_limit: penalty[side+'_inner_limit'],
    inner_penalty: penalty[side+'_max_penalty']
  }

  //populate description list
  let table = $('#'+side+'-chart-list');
  let thead = table.find('thead');
  thead.append($("<tr></tr>").html('<th></th><th>Distance from restriction border</th><th>Penalty</th>'));
  table.append($('<tbody></tbody'));
  let tbody = table.find('tbody');
  if ( notif_dist > def.outer_limit ) {
    tbody.append('<tr><td>Notification distance:</td><td>'+notif_dist+' m.</td><td>Warning only</td></tr>')
  }
  tbody.append('<tr><td>Outer Limit:</td><td>'+def.outer_limit+' m.</td><td>0</td></tr>');
  if ( charts.func === 'linear' && charts.double_step ) {
    tbody.append('<tr><td>Change of gradient distance:</td><td>'+def.border+' m.</td><td>'+def.border_penalty*100+'%</td></tr>')
  }
  tbody.append('<tr><td>Inner Limit:</td><td>'+def.inner_limit+' m.</td><td>'+def.inner_penalty*100+'%</td></tr>')

  //create distance-penalty array for chart
  let mylabels = [def.inner_limit];
  let mydata = [def.inner_penalty*100];

  let x = Math.round(def.inner_limit / 10) * 10;
  do {
    if ( charts.double_step && def.border < x && !mylabels.includes(def.border) ) {
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
      mydata.push( x < def.outer_limit ? calc_pen(charts, x, def) : 0 );
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

function draw_chart(charts, side, x_title) {

//  [charts.h, charts.v].forEach( el => {
  let chart_data = get_chart_data(charts, side);

  let dataset = create_dataset('Penalty (% of pilot score)', chart_data.data, "192,75,75", true);
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
  let ctx = charts[side].canvas;

  // create the chart using the chart canvas
  charts[side].object = new Chart(ctx, {
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
            text: x_title
          }
        }
      }
    }
  });
}

function calc_pen(charts, x, def) {
  if ( charts.func == 'linear' ) {
    if ( charts.double_step ) {
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
  else if ( charts.func == 'non-linear' ) {
    let total = def.outer_limit - def.inner_limit;
    let pen_m = def.inner_penalty / total;
    return Math.round(Math.pow((def.outer_limit - x) / total, Math.log2(10)) * 100 * 10) / 10;
  }
}

function create_charts(charts) {
  $('#v-chart-div').hide();
  let x_title = 'Distance in meters from airspace border (negative inside)';
  if ( charts.h_v ) {
    $('#v-chart-div').show();
    x_title = 'Horizontal distance in meters from airspace border (negative inside)';
    draw_chart(charts, 'v', 'Vertical distance in meters from airspace border (negative inside)');
  }
  draw_chart(charts, 'h', x_title);
}