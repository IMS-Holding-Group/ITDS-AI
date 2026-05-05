(function () {
    function escapeHtml(s) {
        const d = document.createElement("div");
        d.textContent = s;
        return d.innerHTML;
    }

    async function initEmployeeDashboard() {
        const root = document.getElementById("employee-summary-root");
        if (!root) return;
        const res = await fetch("/api/employee/summary");
        const j = await res.json();
        if (!j.success || !j.data) return;
        const d = j.data;
        const greet = document.getElementById("emp-greet");
        if (greet && d.emp_name) greet.textContent = "مرحباً، " + d.emp_name;
        document.getElementById("emp-stat-active").textContent = d.active_tasks ?? "—";
        document.getElementById("emp-stat-week").textContent = d.week_completed ?? "—";
        document.getElementById("emp-stat-perf").textContent =
            d.performance_score != null ? Number(d.performance_score).toFixed(1) : "—";
        document.getElementById("emp-stat-burn").textContent =
            d.burnout_risk != null ? Number(d.burnout_risk).toFixed(2) : "—";

        const urg = document.getElementById("emp-urgent");
        if (urg && d.urgent) {
            urg.innerHTML = "";
            if (!d.urgent.length) {
                urg.innerHTML = '<p class="text-muted">لا مهام عاجلة ضمن المعايير الحالية</p>';
            } else {
                d.urgent.forEach((t) => {
                    const div = document.createElement("div");
                    div.className = "card fade-in";
                    div.innerHTML =
                        "<h3>" +
                        escapeHtml(t.title) +
                        '</h3><p class="task-meta"><span class="priority-' +
                        (t.priority || "") +
                        '">' +
                        escapeHtml(t.priority || "") +
                        "</span> · " +
                        escapeHtml(t.status || "") +
                        "</p>";
                    urg.appendChild(div);
                });
            }
        }

        const act = document.getElementById("emp-activity");
        if (act && d.activity) {
            act.innerHTML = "";
            d.activity.forEach((a) => {
                const li = document.createElement("li");
                li.textContent = (a.title || "") + " — " + (a.status || "");
                act.appendChild(li);
            });
        }
    }

    function initMyTasksTabs() {
        const tabs = document.querySelectorAll("#my-tasks-tabs .tab-btn");
        const cards = document.querySelectorAll(".task-card-item");
        if (!tabs.length || !cards.length) return;
        tabs.forEach((tab) => {
            tab.addEventListener("click", () => {
                tabs.forEach((t) => t.classList.remove("active"));
                tab.classList.add("active");
                const f = tab.dataset.filter;
                cards.forEach((c) => {
                    const st = c.dataset.status || "";
                    let show = f === "all";
                    if (f === "active") show = ["assigned", "in_progress", "analyzing"].includes(st);
                    if (f === "review") show = st === "in_review";
                    if (f === "done") show = st === "completed";
                    c.style.display = show ? "" : "none";
                });
            });
        });
    }

    function initPerformanceChart() {
        const el = document.getElementById("perf-data-json");
        const canvas = document.getElementById("perf-line-chart");
        if (!el || !canvas || !window.ITDSCharts) return;
        try {
            const pts = JSON.parse(el.textContent || "[]");
            const labels = pts.map((p) => p.label || "");
            const values = pts.map((p) => p.score || 0);
            window.ITDSCharts.drawLineChart(canvas, labels, values);
        } catch (e) {
            console.error(e);
        }
    }

    function bindEmployeeTaskActions() {
        document.querySelectorAll("[data-action-start]").forEach((btn) => {
            btn.addEventListener("click", async () => {
                const id = btn.dataset.taskId;
                const res = await fetch("/employee/tasks/" + id + "/start", { method: "POST" });
                const j = await res.json();
                if (j.success) window.location.reload();
                else alert(j.message || "تعذر البدء");
            });
        });
        document.querySelectorAll("[data-action-finish]").forEach((btn) => {
            btn.addEventListener("click", async () => {
                const id = btn.dataset.taskId;
                const res = await fetch("/employee/tasks/" + id + "/finish", { method: "POST" });
                const j = await res.json();
                if (j.success) window.location.reload();
                else alert(j.message || "تعذر الإرسال");
            });
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        initEmployeeDashboard();
        initMyTasksTabs();
        initPerformanceChart();
        bindEmployeeTaskActions();
    });
})();
