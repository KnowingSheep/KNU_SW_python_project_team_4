let charts = [];

function loadStatistics() {
  const year = document.getElementById("yearSelect").value;
  const city = document.getElementById("citySelect").value;

  let url = `/api/statistics?`;
  if (year) url += `year=${year}&`;
  if (city) url += `city=${city}&`;

  fetch(url)
    .then(res => res.json())
    .then(data => {
      charts.forEach(c => c.destroy());
      charts = [];

      charts.push(new Chart(document.getElementById("weekdayChart"), {
        type: "bar",
        data: {
          labels: data.weekdays,
          datasets: [{
            label: "요일별 사고 수",
            data: data.weekday_counts,
            backgroundColor: "skyblue"
          }]
        }
      }));

      charts.push(new Chart(document.getElementById("hourChart"), {
        type: "line",
        data: {
          labels: data.hours,
          datasets: [{
            label: "시간대별 사고 수",
            data: data.hour_counts,
            borderColor: "orange",
            fill: true
          }]
        }
      }));

      charts.push(new Chart(document.getElementById("cityChart"), {
        type: "bar",
        data: {
          labels: data.cities,
          datasets: [{
            label: "도시별 사고 수 (TOP 10)",
            data: data.city_counts,
            backgroundColor: "lightgreen"
          }]
        }
      }));
    });
}

window.onload = loadStatistics;
