(function () {
    const STATUS_AR = {
        new: "جديدة",
        analyzing: "قيد التحليل",
        assigned: "مخصصة",
        in_progress: "قيد التنفيذ",
        in_review: "قيد المراجعة",
        completed: "مكتملة",
        on_hold: "معلقة",
    };

    function statusClass(s) {
        return "status-" + String(s || "").replace(/,/g, "_");
    }

    async function fetchJson(url, opts) {
        const res = await fetch(url, opts);
        return res.json();
    }

    async function initAdminDashboard() {
        const root = document.getElementById("admin-stats-root");
        if (!root) return;

        const stats = await fetchJson("/api/tasks/stats");
        if (stats.success && stats.data) {
            const d = stats.data;
            document.getElementById("stat-total").textContent = d.total_tasks ?? "—";
            document.getElementById("stat-active").textContent = d.active_tasks ?? "—";
            document.getElementById("stat-available").textContent = d.available_employees ?? "—";
            document.getElementById("stat-week").textContent =
                (d.completion_week_pct != null ? d.completion_week_pct + "%" : "—") + "";
        }

        const recent = await fetchJson("/api/dashboard/recent-tasks");
        const tbody = document.querySelector("#recent-tasks-body");
        if (tbody && recent.success && recent.data.tasks) {
            tbody.innerHTML = "";
            recent.data.tasks.forEach((t) => {
                const tr = document.createElement("tr");
                tr.innerHTML =
                    '<td>' +
                    escapeHtml(t.title) +
                    '</td><td><span class="badge ' +
                    statusClass(t.status) +
                    '">' +
                    (STATUS_AR[t.status] || t.status) +
                    '</span></td><td class="priority-' +
                    (t.priority || "") +
                    '">' +
                    escapeHtml(t.priority || "") +
                    '</td><td>' +
                    escapeHtml(t.assignee_name || "—") +
                    "</td>";
                tbody.appendChild(tr);
            });
        }

        const burn = await fetchJson("/api/dashboard/burnout-alerts");
        const bc = document.getElementById("burnout-cards");
        if (bc && burn.success && burn.data.employees) {
            bc.innerHTML = "";
            burn.data.employees.forEach((e) => {
                const card = document.createElement("div");
                card.className = "card alert-danger fade-in";
                card.innerHTML =
                    '<h3>' +
                    escapeHtml(e.name) +
                    '</h3><p class="text-muted">مؤشر الخطر ' +
                    (e.burnout_risk != null ? e.burnout_risk.toFixed(2) : "") +
                    "</p>";
                bc.appendChild(card);
            });
            if (!burn.data.employees.length) {
                bc.innerHTML = '<p class="text-muted">لا توجد تنبيهات خطر عالٍ حالياً</p>';
            }
        }

        const empStats = await fetchJson("/api/employees/stats");
        const canvas = document.getElementById("team-bar-chart");
        if (canvas && empStats.success && empStats.data.employees) {
            const labels = empStats.data.employees.map((e) => e.name.split(" ")[0] || e.name);
            const values = empStats.data.employees.map((e) => Number(e.performance_score) || 0);
            window.ITDSCharts.drawBarChart(canvas, labels, values);
        }
    }

    function escapeHtml(s) {
        const d = document.createElement("div");
        d.textContent = s;
        return d.innerHTML;
    }

    function parseSkillsJson(txt) {
        try {
            const j = JSON.parse(txt || "[]");
            return Array.isArray(j) ? j : [];
        } catch (e) {
            return [];
        }
    }

    async function initTasksAdmin() {
        const root = document.getElementById("tasks-admin-root");
        if (!root) return;

        const modal = document.getElementById("task-modal");
        const openBtn = document.getElementById("open-task-modal");
        const closeBtns = document.querySelectorAll("[data-close-modal]");
        const tagWrap = document.getElementById("skills-tags");
        const tagInput = document.getElementById("skills-input");
        let tags = [];

        function renderTags() {
            tagWrap.querySelectorAll(".tag").forEach((n) => n.remove());
            tags.forEach((t) => {
                const span = document.createElement("span");
                span.className = "tag";
                span.dataset.skill = t;
                span.appendChild(document.createTextNode(t + " "));
                const rm = document.createElement("button");
                rm.type = "button";
                rm.setAttribute("aria-label", "حذف");
                rm.textContent = "\u00D7";
                rm.addEventListener("click", () => {
                    tags = tags.filter((x) => x !== t);
                    renderTags();
                });
                span.appendChild(rm);
                tagWrap.insertBefore(span, tagInput);
            });
        }

        tagInput.addEventListener("keydown", (ev) => {
            if (ev.key === "Enter" || ev.key === ",") {
                ev.preventDefault();
                const v = tagInput.value.trim();
                if (v) {
                    tags.push(v);
                    tagInput.value = "";
                    renderTags();
                }
            }
        });

        openBtn &&
            openBtn.addEventListener("click", () => {
                tags = [];
                renderTags();
                modal.classList.add("open");
                document.getElementById("task-form").reset();
                document.getElementById("ai-match-results").innerHTML = "";
            });

        closeBtns.forEach((bt) =>
            bt.addEventListener("click", () => {
                modal.classList.remove("open");
            })
        );

        document.getElementById("task-form").addEventListener("submit", async (ev) => {
            ev.preventDefault();
            const btn = document.getElementById("task-submit-btn");
            btn.classList.add("loading");
            btn.disabled = true;
            document.getElementById("ai-match-results").innerHTML = "";
            try {
                const payload = {
                    title: document.getElementById("fld-title").value.trim(),
                    description: document.getElementById("fld-desc").value.trim(),
                    priority: document.getElementById("fld-priority").value,
                    deadline: document.getElementById("fld-deadline").value,
                    estimated_hours: Number(document.getElementById("fld-hours").value) || 4,
                    required_skills: tags.slice(),
                };
                const res = await fetch("/admin/tasks/create", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                const j = await res.json();
                if (!j.success) throw new Error(j.message || "فشل الحفظ");
                const wrap = document.getElementById("ai-match-results");
                wrap.innerHTML =
                    "<p class=\"text-muted\">أفضل الموظفين وفق المحرك الداخلي (يرجى التعيين أو الاختيار يدوياً)</p>";
                j.matches.forEach((m, idx) => {
                    const d = document.createElement("div");
                    d.className = "match-card fade-in";
                    d.innerHTML =
                        "<strong>" +
                        escapeHtml(m.name) +
                        "</strong><span class=\"text-muted\">" +
                        escapeHtml(m.department) +
                        '</span><p>النتيجة: ' +
                        m.score +
                        "</p><p>" +
                        escapeHtml(m.reason) +
                        '</p><button type="button" class="btn btn-primary assign-ai" data-emp="' +
                        m.employee_id +
                        '" data-task="' +
                        j.task_id +
                        '">تعيين هذا الموظف</button>';
                    wrap.appendChild(d);
                });
                wrap.querySelectorAll(".assign-ai").forEach((b) => {
                    b.addEventListener("click", async () => {
                        const res2 = await fetch("/admin/tasks/" + b.dataset.task + "/assign", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ employee_id: Number(b.dataset.emp) }),
                        });
                        const jj = await res2.json();
                        if (jj.success) {
                            modal.classList.remove("open");
                            window.location.reload();
                        } else {
                            alert(jj.message || "تعذر التعيين");
                        }
                    });
                });
            } catch (err) {
                alert(err.message || "خطأ");
            } finally {
                btn.classList.remove("loading");
                btn.disabled = false;
            }
        });

        document.getElementById("filter-status").addEventListener("change", filterTable);
        document.getElementById("filter-priority").addEventListener("change", filterTable);
        document.getElementById("filter-employee").addEventListener("change", filterTable);
        document.getElementById("filter-date").addEventListener("change", filterTable);

        function filterTable() {
            const st = document.getElementById("filter-status").value;
            const pr = document.getElementById("filter-priority").value;
            const em = document.getElementById("filter-employee").value;
            const dt = document.getElementById("filter-date").value;
            document.querySelectorAll("#tasks-table tbody tr").forEach((tr) => {
                const okSt = !st || tr.dataset.status === st;
                const okPr = !pr || tr.dataset.priority === pr;
                const okEm = !em || tr.dataset.employee === em;
                let okDt = true;
                if (dt && tr.dataset.created) {
                    const d0 = new Date(tr.dataset.created);
                    const now = new Date();
                    const diff = (now - d0) / (86400000);
                    if (dt === "7") okDt = diff <= 7;
                    if (dt === "30") okDt = diff <= 30;
                }
                tr.style.display = okSt && okPr && okEm && okDt ? "" : "none";
            });
        }

        document.querySelectorAll(".task-status-select").forEach((sel) => {
            sel.addEventListener("change", async () => {
                const id = sel.dataset.id;
                const res = await fetch("/admin/tasks/" + id + "/status", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ status: sel.value }),
                });
                const j = await res.json();
                if (!j.success) {
                    alert(j.message || "فشل التحديث");
                    window.location.reload();
                }
            });
        });

        document.querySelectorAll(".task-assign-select").forEach((sel) => {
            sel.addEventListener("change", async () => {
                if (!sel.value) return;
                const id = sel.dataset.id;
                const res = await fetch("/admin/tasks/" + id + "/assign", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ employee_id: Number(sel.value) }),
                });
                const j = await res.json();
                if (j.success) window.location.reload();
                else alert(j.message || "تعذر التعيين");
            });
        });
    }

    async function initReports() {
        const root = document.getElementById("reports-root");
        if (!root) return;

        async function load(range) {
            const j = await fetchJson("/api/reports/summary?range=" + encodeURIComponent(range));
            if (!j.success || !j.data) return;
            const d = j.data;
            const lineC = document.getElementById("report-line-chart");
            if (lineC && d.completed_per_day) {
                const labels = d.completed_per_day.map((x) => x.date);
                const vals = d.completed_per_day.map((x) => x.count);
                window.ITDSCharts.drawLineChart(lineC, labels, vals);
            }
            const pie = document.getElementById("report-pie");
            if (pie && d.tasks_by_priority) {
                const colors = {
                    low: "#8A93AA",
                    medium: "#1B5DA8",
                    high: "#B86A00",
                    critical: "#C0392B",
                };
                const slices = Object.keys(d.tasks_by_priority).map((k) => ({
                    label: k,
                    value: d.tasks_by_priority[k],
                    color: colors[k] || "#1B3F7E",
                }));
                window.ITDSCharts.renderPieSvg(pie, slices);
            }
            const barEmp = document.getElementById("report-bar-employees");
            if (barEmp && d.employee_performance) {
                const labels = d.employee_performance.map((e) => e.name.split(" ")[0]);
                const values = d.employee_performance.map((e) => e.avg_score || 0);
                window.ITDSCharts.drawBarChart(barEmp, labels, values);
            }
            const bb = document.getElementById("burnout-bars");
            if (bb && d.burnout_report) {
                bb.innerHTML = "";
                d.burnout_report.forEach((e) => {
                    const pct = Math.min(100, (e.burnout_risk || 0) * 100);
                    let cls = "";
                    if (e.level_key === "danger") cls = " danger";
                    else if (e.level_key === "warn") cls = " warning";
                    const row = document.createElement("div");
                    row.className = "burnout-bar-row";
                    row.innerHTML =
                        '<div class="burnout-bar-head"><span>' +
                        escapeHtml(e.name) +
                        "</span><span>" +
                        (e.burnout_risk != null ? e.burnout_risk.toFixed(2) : "") +
                        '</span></div><div class="progress-track"><div class="progress-bar' +
                        cls +
                        '" style="width:' +
                        pct +
                        '%"></div></div>';
                    bb.appendChild(row);
                });
            }
        }

        const rangeSel = document.getElementById("report-range");
        rangeSel &&
            rangeSel.addEventListener("change", () => {
                load(rangeSel.value);
            });
        document.getElementById("report-print") &&
            document.getElementById("report-print").addEventListener("click", () => window.print());
        load(rangeSel ? rangeSel.value : "month");
    }

    function initEmployeesAdmin() {
        const modal = document.getElementById("emp-modal");
        const openBtn = document.getElementById("open-emp-modal");
        const urlEl = document.getElementById("emp-create-url");
        if (!modal || !openBtn || !urlEl) return;
        const closeBtn = document.querySelector("[data-close-emp]");
        openBtn.addEventListener("click", () => modal.classList.add("open"));
        closeBtn &&
            closeBtn.addEventListener("click", () => {
                modal.classList.remove("open");
            });
        document.getElementById("emp-form").addEventListener("submit", async (ev) => {
            ev.preventDefault();
            const btn = document.getElementById("emp-submit");
            btn.classList.add("loading");
            btn.disabled = true;
            const skillsRaw = document
                .getElementById("emp-skills")
                .value.split(",")
                .map((s) => s.trim())
                .filter(Boolean);
            const body = {
                name: document.getElementById("emp-name").value.trim(),
                email: document.getElementById("emp-email").value.trim(),
                department: document.getElementById("emp-dept").value.trim(),
                skills: skillsRaw,
                performance_score: Number(document.getElementById("emp-perf").value),
                speed_score: Number(document.getElementById("emp-spd").value),
            };
            try {
                const res = await fetch(urlEl.value, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(body),
                });
                const j = await res.json();
                if (j.success) window.location.reload();
                else alert(j.message || "خطأ");
            } finally {
                btn.classList.remove("loading");
                btn.disabled = false;
            }
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        initAdminDashboard();
        initTasksAdmin();
        initReports();
        initEmployeesAdmin();
    });
})();
