(function (w) {
    function cssRatio(canvas) {
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        const ctx = canvas.getContext("2d");
        ctx.scale(dpr, dpr);
        return { ctx, w: rect.width, h: rect.height };
    }

    function drawBarChart(canvas, labels, values, opts) {
        const r = cssRatio(canvas);
        const ctx = r.ctx;
        const ww = r.w;
        const hh = r.h;
        ctx.clearRect(0, 0, ww, hh);
        const pad = (opts && opts.pad) || 36;
        const maxVal = Math.max(1, ...values);
        const n = values.length;
        const slot = n ? (ww - pad * 2) / n : ww - pad * 2;
        const barW = slot * 0.55;
        ctx.font = "13px IBM Plex Sans Arabic, sans-serif";
        values.forEach((v, i) => {
            const x = pad + i * slot + (slot - barW) / 2;
            const h = ((hh - pad * 2) * v) / maxVal;
            const y = hh - pad - h;
            ctx.fillStyle = "#1B3F7E";
            ctx.fillRect(x, y, barW, h);
            ctx.fillStyle = "#4A5578";
            const lb = labels[i] || "";
            ctx.fillText(lb.slice(0, 12), x - 6, hh - pad + 18);
        });
    }

    function drawLineChart(canvas, labels, values) {
        const r = cssRatio(canvas);
        const ctx = r.ctx;
        const ww = r.w;
        const hh = r.h;
        ctx.clearRect(0, 0, ww, hh);
        const pad = 40;
        const maxVal = Math.max(1, ...values);
        const minVal = 0;
        const dx = (ww - pad * 2) / Math.max(values.length - 1, 1);
        ctx.beginPath();
        ctx.strokeStyle = "#1B3F7E";
        ctx.lineWidth = 2;
        values.forEach((v, i) => {
            const x = pad + i * dx;
            const y = hh - pad - ((hh - pad * 2) * (v - minVal)) / (maxVal - minVal);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();
        ctx.fillStyle = "#1B5DA8";
        values.forEach((v, i) => {
            const x = pad + i * dx;
            const y = hh - pad - ((hh - pad * 2) * (v - minVal)) / (maxVal - minVal);
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
        ctx.font = "12px IBM Plex Sans Arabic, sans-serif";
        ctx.fillStyle = "#8A93AA";
        labels.forEach((lb, i) => {
            const x = pad + i * dx;
            ctx.fillText(String(lb).slice(-5), x - 14, hh - 12);
        });
    }

    function renderPieSvg(container, slices) {
        if (!container) return;
        const total = slices.reduce((s, x) => s + x.value, 0) || 1;
        let angle = 0;
        const cx = 100;
        const cy = 100;
        const r = 90;
        let pathHtml = "";
        slices.forEach((sl) => {
            const frac = sl.value / total;
            const a1 = angle;
            const a2 = angle + frac * Math.PI * 2;
            angle = a2;
            const x1 = cx + r * Math.cos(a1 - Math.PI / 2);
            const y1 = cy + r * Math.sin(a1 - Math.PI / 2);
            const x2 = cx + r * Math.cos(a2 - Math.PI / 2);
            const y2 = cy + r * Math.sin(a2 - Math.PI / 2);
            const large = frac > 0.5 ? 1 : 0;
            pathHtml +=
                '<path d="M ' +
                cx +
                " " +
                cy +
                " L " +
                x1 +
                " " +
                y1 +
                " A " +
                r +
                " " +
                r +
                " 0 " +
                large +
                " 1 " +
                x2 +
                " " +
                y2 +
                ' Z" fill="' +
                sl.color +
                '" stroke="#fff" stroke-width="1"/>';
        });
        let leg = "";
        slices.forEach((sl) => {
            leg +=
                '<div class="pie-legend-row"><span class="pie-dot" style="background:' +
                sl.color +
                '"></span><span>' +
                sl.label +
                " (" +
                sl.value +
                ")</span></div>";
        });
        container.innerHTML =
            '<div class="pie-svg-inner"><svg width="200" height="200" viewBox="0 0 200 200">' +
            pathHtml +
            "</svg></div><div class=\"pie-legend\">" +
            leg +
            "</div>";
    }

    w.ITDSCharts = { drawBarChart, drawLineChart, renderPieSvg };
})(window);
