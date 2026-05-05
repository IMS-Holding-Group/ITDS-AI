(function () {
    function qs(sel, root) {
        return (root || document).querySelector(sel);
    }

    function initLoginForm() {
        const form = qs("#login-form");
        if (!form) return;
        const err = qs("#login-error");
        const btn = qs("#login-btn");
        const pw = qs("#password");
        const urlEl = qs("#login-post-url");
        const postUrl = urlEl ? urlEl.value : "/login";
        const toggle = qs("#toggle-pw");
        if (toggle && pw) {
            toggle.addEventListener("click", () => {
                pw.type = pw.type === "password" ? "text" : "password";
            });
        }
        form.addEventListener("submit", async (ev) => {
            ev.preventDefault();
            err.classList.remove("show");
            btn.classList.add("loading");
            btn.disabled = true;
            try {
                const res = await fetch(postUrl, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        email: qs("#email").value.trim(),
                        password: pw.value,
                    }),
                });
                const data = await res.json();
                if (data.success && data.redirect) {
                    window.location.href = data.redirect;
                } else {
                    err.textContent = data.message || "فشل تسجيل الدخول";
                    err.classList.add("show");
                }
            } catch (e) {
                err.textContent = "حدث خطأ في الاتصال";
                err.classList.add("show");
            } finally {
                btn.classList.remove("loading");
                btn.disabled = false;
            }
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        const burger = qs(".burger-btn");
        const links = qs(".nav-links");
        if (burger && links) {
            burger.addEventListener("click", () => {
                links.classList.toggle("open");
            });
        }
        initLoginForm();
    });
})();
