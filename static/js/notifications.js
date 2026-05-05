(function () {
    const panel = document.getElementById("notif-panel");
    const bell = document.getElementById("notif-bell");
    const badge = document.getElementById("notif-badge");

    async function loadNotifications() {
        try {
            const res = await fetch("/api/notifications");
            const j = await res.json();
            if (!j.success || !j.data) return;
            const unread = j.data.unread_count || 0;
            if (badge) {
                badge.textContent = unread > 99 ? "99+" : String(unread);
                if (unread > 0) {
                    badge.classList.remove("is-empty");
                } else {
                    badge.classList.add("is-empty");
                }
            }
            if (!panel) return;
            panel.innerHTML = "";
            const items = j.data.items || [];
            if (!items.length) {
                const empty = document.createElement("div");
                empty.className = "notif-item text-muted";
                empty.textContent = "لا توجد إشعارات";
                panel.appendChild(empty);
                return;
            }
            items.forEach((n) => {
                const div = document.createElement("div");
                div.className = "notif-item" + (n.is_read ? "" : " unread");
                div.textContent = n.message;
                div.dataset.id = n.id;
                div.addEventListener("click", async () => {
                    await fetch("/api/notifications/read/" + n.id, { method: "POST" });
                    div.classList.remove("unread");
                    loadNotifications();
                });
                panel.appendChild(div);
            });
        } catch (e) {
            console.error(e);
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        if (bell && panel) {
            bell.addEventListener("click", (ev) => {
                ev.stopPropagation();
                panel.classList.toggle("open");
                loadNotifications();
            });
            document.addEventListener("click", () => panel.classList.remove("open"));
            panel.addEventListener("click", (ev) => ev.stopPropagation());
        }
        loadNotifications();
        setInterval(loadNotifications, 60000);
    });
})();
