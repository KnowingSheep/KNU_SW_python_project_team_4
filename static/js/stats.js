let hourChart, weekChart, regionChart, trendChart;

function renderCharts(data) {
    const hourCtx = document.getElementById("hourChart").getContext("2d");
    const weekCtx = document.getElementById("weekChart").getContext("2d");
    const regionCtx = document.getElementById("regionChart").getContext("2d");
    const trendCtx = document.getElementById("trendChart").getContext("2d");

    // 기존 차트 제거
    if (hourChart) hourChart.destroy();
    if (weekChart) weekChart.destroy();
    if (regionChart) regionChart.destroy();
    if (trendChart) trendChart.destroy();

    hourChart = new Chart(hourCtx, {
        type: "bar",
        data: {
            labels: data.hour.labels,
            datasets: [{
                label: "사고 수",
                data: data.hour.values,
                backgroundColor: "#3b82f6"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });

    weekChart = new Chart(weekCtx, {
        type: "doughnut",  // ✅ bar → doughnut
        data: {
            labels: data.week.labels,
            datasets: [{
                label: "사고 수",
                data: data.week.values,
                backgroundColor: [
                    "#f87171", "#fb923c", "#facc15", "#4ade80", "#60a5fa", "#a78bfa", "#f472b6"
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom", // ✅ 하단에 범례 배치
                    labels: {
                        boxWidth: 14,
                        padding: 12
                    }
                }
            }
        }
    });

    regionChart = new Chart(regionCtx, {
        type: "bar",
        data: {
            labels: data.region.labels,
            datasets: [{
                label: "사고 수",
                data: data.region.values,
                backgroundColor: "#10b981"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });

    trendChart = new Chart(trendCtx, {
        type: "line",
        data: {
            labels: data.trend.labels,
            datasets: [{
                label: "사고 수",
                data: data.trend.values,
                borderColor: "#6366f1",
                backgroundColor: "rgba(99, 102, 241, 0.1)",
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });
}

async function loadStatsByYear(year) {
    const res = await fetch(`/api/stats?start=${year}-01-01&end=${year}-12-31`);
    const data = await res.json();
    document.getElementById("totalAccidents").textContent = data.total.toLocaleString();
    document.getElementById("fatalAccidents").textContent = data.fatal.toLocaleString();
    document.getElementById("avgSeverity").textContent = data.avg_severity;
    renderCharts(data); // ⬅️ 차트 렌더링 추가됨
}

async function loadYearOptions() {
    const res = await fetch("/api/years");
    const years = await res.json();
    const selector = document.getElementById("yearSelector");
    selector.innerHTML = years.map(y => `<option value="${y}">${y}</option>`).join('');
    selector.value = years[years.length - 1];
    loadStatsByYear(selector.value);
    selector.addEventListener("change", () => {
        loadStatsByYear(selector.value);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("home-button").addEventListener("click", () => {
        window.location.href = "/";
    });
    loadYearOptions();
});