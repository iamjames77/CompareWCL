document.addEventListener('DOMContentLoaded', function () {
    // Hidden div에서 데이터를 가져옵니다
    const MyGraphData = JSON.parse(document.getElementById('MyGraphData').innerText);
    const OtherGraphData = JSON.parse(document.getElementById('OtherGraphData').innerText);
    const DataType = document.getElementById('dType').innerText;
    var TimeLength = document.getElementById('TimeLength').innerText;

    const dType = (DataType === 'Healing') ? 'Hps' : 'Dps';
    

    // 밀리초를 분과 초로 변환하는 함수
    function millisecondsToMinutesAndSeconds(ms) {
        const totalSeconds = ms / 1000;
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = (totalSeconds % 60).toFixed(0);
        if(seconds < 10){
            return `${minutes}:0${seconds}`;
        }
        return `${minutes}:${seconds}`;
    }

    // 큰 숫자를 축약형으로 변환하는 함수
    function formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        } else {
            return num.toString();
        }
    }

    function generateTickPositions(maxTime, interval) {
        const positions = [];
        for (let time = 0; time <= maxTime; time += interval) {
            positions.push(time);
        }
        return positions;
    }
    
    const tickInterval = 1000;
    const tickPositions = generateTickPositions(TimeLength, tickInterval);

    const chartWidth = (TimeLength / 1000) * 100; // 전체 초 * 100픽셀

    // Highcharts 차트를 생성합니다
    const chart = Highcharts.chart('container', {
        chart: {
            type: 'area',
            width: chartWidth
        },
        title: {
            text: dType + ' graph'
        },
        xAxis: {
            type: 'linear',
            title: {
                text: 'Time'
            },
            min: 0,
            max: TimeLength,
            tickPositions: tickPositions, // 30초 단위로 레이블을 표시합니다.
            labels: {
                formatter: function () {
                    return millisecondsToMinutesAndSeconds(this.value);
                }
            }
        },
        yAxis: {
            title: {
                text: dType
            },
            labels: {
                formatter: function () {
                    return formatNumber(this.value);
                }
            }
        },
        tooltip: {
            formatter: function () {
                const elapsedTime = this.x;
                const timeStr = millisecondsToMinutesAndSeconds(elapsedTime);
                return `<b>Time: ${timeStr}</b><br/>${this.series.name}: ${formatNumber(this.y)}`;
            }
        },
        series: [{
            name: 'My'+dType,
            data: MyGraphData.data.map((value, index) => [index * MyGraphData.pointInterval, value])
        }, {
            name: 'Other'+dType,
            data: OtherGraphData.data.map((value, index) => [index * OtherGraphData.pointInterval, value])
        }]
    });
    document.getElementById('container').style.width = chartWidth + 'px';
    var intervalPX = chart.plotWidth / TimeLength * 1000;
    console.log(intervalPX);
    const MyCastEvent = JSON.parse(document.getElementById('MyCastEvent').innerText);
    const OtherCastEvent = JSON.parse(document.getElementById('OtherCastEvent').innerText);
    const MyBuffEvent = JSON.parse(document.getElementById('MyBuffEvent').innerText);
    const OtherBuffEvent = JSON.parse(document.getElementById('OtherBuffEvent').innerText);
    const spellDict = JSON.parse(document.getElementById('spellDict').innerText);
    const MyStartTime = document.getElementById('MyStartTime').innerText;
    const OtherStartTime = document.getElementById('OtherStartTime').innerText;
    
    document.getElementById('MyCastTitle').style.width = chart.plotLeft + 'px';
    document.getElementById('MyCastGraph').style.flexGrow = 1;
    document.getElementById('OtherCastTitle').style.width = chart.plotLeft + 'px';
    document.getElementById('OtherCastGraph').style.flexGrow = 1;
    
    addIcons('MyCastGraph', MyCastEvent, MyStartTime, spellDict, intervalPX);
    addIcons('OtherCastGraph', OtherCastEvent, OtherStartTime, spellDict, intervalPX);
});

function addIcons(containerID, EventData, StartTime, spellDict, intervalPX) {
    const container = document.getElementById(containerID);
    EventData.forEach((event) => {
        const icon = document.createElement('img');
        const iconURL = 'https://wow.zamimg.com/images/wow/icons/large/';
        icon.src = iconURL + spellDict[event.abilityGameID].icon;
        icon.style.position = 'absolute';
        icon.style.left = ((event.timestamp - StartTime) / 1000) * intervalPX + 'px';
        icon.title = spellDict[event.abilityGameID].name + ' ' + (event.timestamp - StartTime) / 1000 + 's';
        icon.style.width = '20px';
        icon.style.height = '20px';
        container.appendChild(icon);
    });
}

