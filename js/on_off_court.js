var canv = document.createElement('canvas');
canv.id = 'on_off_court';
canv.width = 800;
canv.height = 600;
document.body.appendChild(canv);

var chartRadarDOM;
var chartRadarData;
var chartRadarOptions;

Chart.defaults.global.responsive = false;
chartRadarDOM = document.getElementById("on_off_court");
//custormized options
chartRadarOptions = 
{
    legend:{
        labels:{
            fontColor: 'rgb(250,139,28)',
            fontSize: 14
        }
    }
};

$.getJSON("statistics/on_off_court_sum.json", function(data) {
    var labels = data.map(function(e) {
        return e.balltype;
    });

    var data = data.map(function(e) {
        return e.on_off_court;
    });

    //random color generator
    color = new Array();
    for(var i = 0;i<data.length;i++){
        r = Math.floor(Math.random() * 133);
        g = Math.floor(Math.random() * 231);
        b = Math.floor(Math.random() * 177);
        color.push('rgb(' + r + ', ' + g + ', ' + b + ')');
    }
    
    var chart = new Chart(chartRadarDOM, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                backgroundColor: color,
                pointBorderColor: "rgba(0,0,0,0)",
                borderColor: 'rgb(129, 198, 228)',
                borderWidth: 3,
                data: data
            }]
        },
        options: chartRadarOptions
    });
});