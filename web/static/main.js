document.addEventListener("DOMContentLoaded", () => {
  const path = window.location.pathname;

  if (path === "/") {
    initDashboard();
  } else if (path === "/search") {
    initSearch();
  }
});

// =================================================================
// 数据看板逻辑
// =================================================================

let groupChart = null;
let dailyChart = null;

function initDashboard() {
  const ctxGroup = document.getElementById("group-chart")?.getContext("2d");
  const ctxDaily = document.getElementById("daily-chart")?.getContext("2d");

  if (!ctxGroup || !ctxDaily) return;

  groupChart = new Chart(ctxGroup, {
    type: "bar",
    options: {
      indexAxis: "y",
      responsive: true,
      plugins: { legend: { display: false } },
    },
  });

  dailyChart = new Chart(ctxDaily, {
    type: "line",
    options: { responsive: true, plugins: { legend: { display: false } } },
  });

  fetchAndUpdateDashboard();
  setInterval(fetchAndUpdateDashboard, 5000); // 每5秒轮询
}

async function fetchAndUpdateDashboard() {
  try {
    const response = await fetch("/api/stats");
    if (!response.ok) throw new Error("Network response was not ok");
    const stats = await response.json();
    updateDashboardUI(stats);
  } catch (error) {
    console.error("Failed to fetch dashboard stats:", error);
  }
}

function updateDashboardUI(stats) {
  // 更新数字卡片
  document.getElementById("today-count").textContent =
    stats.today_message_count;
  document.getElementById("top-talker").textContent =
    stats.seven_day_top_talker?.sender_name || "N/A";

  // 更新群组消息排行榜 (横向柱状图)
  groupChart.data = {
    labels: stats.seven_day_group_stats.map((d) => d.chat_title),
    datasets: [
      {
        label: "消息数",
        data: stats.seven_day_group_stats.map((d) => d.count),
        backgroundColor: "rgba(54, 162, 235, 0.6)",
      },
    ],
  };
  groupChart.update();

  // 更新每日消息总量趋势 (折线图)
  dailyChart.data = {
    labels: stats.seven_day_total_stats.map((d) => d.date),
    datasets: [
      {
        label: "消息数",
        data: stats.seven_day_total_stats.map((d) => d.count),
        borderColor: "rgba(255, 99, 132, 1)",
        tension: 0.1,
      },
    ],
  };
  dailyChart.update();
}

// =================================================================
// 搜索页面逻辑
// =================================================================

function initSearch() {
  const searchInput = document.getElementById("search-input");
  const resultsContainer = document.getElementById("results-container");

  let debounceTimer;
  searchInput.addEventListener("input", (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      performSearch(e.target.value, resultsContainer);
    }, 300); // 延迟300ms执行搜索，防止频繁请求
  });
}

async function performSearch(query, container) {
  if (query.length < 2) {
    container.innerHTML = "";
    return;
  }

  try {
    const response = await fetch(
      `/api/search?query=${encodeURIComponent(query)}`
    );
    if (!response.ok) throw new Error("Network response was not ok");
    const results = await response.json();
    displaySearchResults(results, container);
  } catch (error) {
    console.error("Failed to perform search:", error);
    container.innerHTML = "<p>搜索失败，请查看控制台日志。</p>";
  }
}

function displaySearchResults(results, container) {
  if (results.length === 0) {
    container.innerHTML = "<p>没有找到匹配的结果。</p>";
    return;
  }

  container.innerHTML = results
    .map(
      (msg) => `
        <article>
            <p>${msg.text}</p>
            <p class="result-meta">
                <strong>${msg.chat_title}</strong> - <em>${
        msg.sender_name
      }</em> at ${new Date(msg.date).toLocaleString()}
            </p>
        </article>
    `
    )
    .join("");
}
