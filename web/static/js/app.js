document.addEventListener("DOMContentLoaded", () => {
  const { createApp, ref, onMounted, reactive } = Vue;

  createApp({
    setup() {
      const loading = ref(true);
      const searchQuery = ref("");
      const searchResults = ref([]);
      const chartInstances = reactive({});
      const TIMEZONE_OFFSET = 8 * 60 * 60 * 1000; // 8 hours for Beijing Time

      // ECharts option templates
      const baseChartOptions = {
        backgroundColor: "transparent",
        tooltip: {
          trigger: "item",
          formatter: "{b}<br/>{a}: {c}",
          textStyle: {
            color: "#fff",
          },
          backgroundColor: "rgba(0,0,0,0.7)",
          borderColor: "#333",
        },
        grid: {
          left: "3%",
          right: "4%",
          bottom: "3%",
          containLabel: true,
        },
        xAxis: {
          type: "value",
          axisLine: { lineStyle: { color: "#888" } },
          splitLine: { lineStyle: { color: "#444" } },
        },
        yAxis: {
          type: "category",
          axisLine: { lineStyle: { color: "#888" } },
          axisLabel: {
            color: "#ddd",
            formatter: function (value) {
              return value.length > 15 ? value.substring(0, 15) + "..." : value;
            },
          },
        },
        textStyle: {
          color: "#ddd",
        },
      };

      // Format date considering Beijing Time
      const formatDate = (dateString) => {
        const date = new Date(new Date(dateString).getTime() + TIMEZONE_OFFSET);
        return date.toISOString().split("T")[0];
      };

      const fetchData = async () => {
        try {
          const response = await fetch("/api/dashboard-data");
          const data = await response.json();

          updateTopChats7Days(data.top_chats_7_days);
          updateTotalMessages7Days(data.total_messages_7_days);
          updateTopUsers7Days(data.top_users_7_days);
          updateTopChatsToday(data.top_chats_today);
        } catch (error) {
          console.error("Failed to fetch dashboard data:", error);
        } finally {
          // Hide loading spinner on first load
          if (loading.value) {
            const loadingEl = document.getElementById("loading");
            const appEl = document.getElementById("app");
            if (loadingEl && appEl) {
              loadingEl.style.opacity = "0";
              setTimeout(() => {
                loadingEl.style.display = "none";
                appEl.style.opacity = "1";
              }, 500);
            }
            loading.value = false;
          }
        }
      };

      const initCharts = () => {
        chartInstances.topChats7Days = echarts.init(
          document.getElementById("top-chats-7-days")
        );
        chartInstances.totalMessages7Days = echarts.init(
          document.getElementById("total-messages-7-days")
        );
        chartInstances.topUsers7Days = echarts.init(
          document.getElementById("top-users-7-days")
        );
        chartInstances.topChatsToday = echarts.init(
          document.getElementById("top-chats-today")
        );
      };

      const updateTopChats7Days = (data) => {
        const chartData = data
          .map((item) => ({
            value: item.message_count,
            name: item.chat_title,
          }))
          .reverse();

        chartInstances.topChats7Days.setOption({
          ...baseChartOptions,
          title: { text: "七天群消息排行榜", textStyle: { color: "#eee" } },
          yAxis: {
            ...baseChartOptions.yAxis,
            data: chartData.map((d) => d.name),
          },
          series: [
            {
              name: "消息数量",
              type: "bar",
              data: chartData.map((d) => d.value),
              itemStyle: { color: "#3b82f6" },
            },
          ],
        });
      };

      const updateTotalMessages7Days = (data) => {
        const chartData = data.map((item) => ({
          day: formatDate(item.day),
          count: item.message_count,
        }));

        chartInstances.totalMessages7Days.setOption({
          ...baseChartOptions,
          title: { text: "七日总消息数量", textStyle: { color: "#eee" } },
          xAxis: { type: "category", data: chartData.map((d) => d.day) },
          yAxis: { type: "value" },
          series: [
            {
              name: "总消息数",
              type: "line",
              smooth: true,
              data: chartData.map((d) => d.count),
              itemStyle: { color: "#8b5cf6" },
              areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  {
                    offset: 0,
                    color: "rgba(139, 92, 246, 0.5)",
                  },
                  {
                    offset: 1,
                    color: "rgba(139, 92, 246, 0)",
                  },
                ]),
              },
            },
          ],
        });
      };

      const updateTopUsers7Days = (data) => {
        const chartData = data
          .map((item) => ({
            value: item.message_count,
            name: item.sender_name,
          }))
          .reverse();

        chartInstances.topUsers7Days.setOption({
          ...baseChartOptions,
          title: { text: "七日用户消息排行", textStyle: { color: "#eee" } },
          yAxis: {
            ...baseChartOptions.yAxis,
            data: chartData.map((d) => d.name),
          },
          series: [
            {
              name: "消息数量",
              type: "bar",
              data: chartData.map((d) => d.value),
              itemStyle: { color: "#10b981" },
            },
          ],
        });
      };

      const updateTopChatsToday = (data) => {
        const chartData = data
          .map((item) => ({
            value: item.message_count,
            name: item.chat_title,
          }))
          .reverse();

        chartInstances.topChatsToday.setOption({
          ...baseChartOptions,
          title: { text: "今日群消息排行", textStyle: { color: "#eee" } },
          yAxis: {
            ...baseChartOptions.yAxis,
            data: chartData.map((d) => d.name),
          },
          series: [
            {
              name: "消息数量",
              type: "bar",
              data: chartData.map((d) => d.value),
              itemStyle: { color: "#ef4444" },
            },
          ],
        });
      };

      // Debounce function for search
      let searchTimeout;
      const searchMessages = () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(async () => {
          if (searchQuery.value.length > 1) {
            const response = await fetch(
              `/api/search?q=${encodeURIComponent(searchQuery.value)}`
            );
            searchResults.value = await response.json();
          } else {
            searchResults.value = [];
          }
        }, 300); // 300ms delay
      };

      onMounted(() => {
        initCharts();
        fetchData(); // Initial fetch
        setInterval(fetchData, 5000); // Poll every 5 seconds

        window.addEventListener("resize", () => {
          Object.values(chartInstances).forEach((chart) => chart.resize());
        });
      });

      return {
        searchQuery,
        searchResults,
        searchMessages,
        formatDate,
      };
    },
  }).mount("#app");
});
