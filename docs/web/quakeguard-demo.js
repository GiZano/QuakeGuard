/**
 * QuakeGuard — Live Demo (client-side simulation)
 * Faithful echo of the backend's POST /demo/trigger-earthquake flow:
 * trigger a quake per geographic zone, walk the pipeline,
 * and keep a rolling "last 10 critical events" history (persisted to localStorage).
 * No MQTT broker / network required.
 */
(function () {
    'use strict';

    window.QUAKEGUARD_ZONES = [
        { id: 1, name: 'Italy - North', lat: 45.46, lng: 9.19, cover: 'Lombardy, Veneto, Piedmont' },
        { id: 2, name: 'Italy - Center', lat: 42.85, lng: 12.57, cover: 'Tuscany, Lazio, Umbria' },
        { id: 3, name: 'Italy - South & Islands', lat: 38.12, lng: 15.65, cover: 'Campania, Sicily, Sardinia' },
        { id: 4, name: 'Western Europe', lat: 48.86, lng: 2.35, cover: 'France, Spain, Germany, UK' },
        { id: 5, name: 'North America', lat: 39.83, lng: -98.58, cover: 'USA, Canada, Mexico' },
        { id: 6, name: 'South America', lat: -14.24, lng: -51.93, cover: 'Brazil, Argentina, Chile' },
        { id: 7, name: 'East Asia', lat: 35.68, lng: 139.69, cover: 'China, Japan, India' },
        { id: 8, name: 'Unknown Region', lat: 21.0, lng: 0.0, cover: 'Fallback for unmapped coordinates' }
    ];

    var STORE_KEY = 'quakeguard_demo_history';

    // Magnitude proxy: M = log10(PGA_calib) + b, where PGA_calib = PGA / K_CALIBRATION
    // (K_CALIBRATION = 1.6, B_OFFSET = 3.0) — reproduced as the docs describe.
    var K_CALIBRATION = 1.6;
    var B_OFFSET = 3.0;
    var THRESHOLD = 4.5;

    function magnitudeFromPga(pga) {
        return Math.log10(pga / K_CALIBRATION) + B_OFFSET;
    }

    var panel = document.getElementById('qg-demo');
    if (!panel) return;

    var zoneSel = document.getElementById('demo-zone');
    var magSlider = document.getElementById('demo-mag');
    var magRead = document.getElementById('demo-mag-read');
    var msgInput = document.getElementById('demo-msg');
    var triggerBtn = document.getElementById('demo-trigger');
    var feed = document.getElementById('demo-feed');
    var consoleEl = document.getElementById('demo-console');
    var toast = document.getElementById('alert-toast');
    var aiTitle = document.getElementById('ai-report-title');
    var aiBody = document.getElementById('ai-report-body');

    var T = (window.QuakeGuardI18n && window.QuakeGuardI18n.t) || function (k) { return k; };

    // Build zone selector (translated)
    window.QUAKEGUARD_ZONES.forEach(function (z) {
        var opt = document.createElement('option');
        opt.value = z.id;
        opt.textContent = T('zone_' + z.id);
        zoneSel.appendChild(opt);
    });
    zoneSel.value = 1; // default: Italy - North

    function selectedZone() {
        var id = parseInt(zoneSel.value, 10);
        for (var i = 0; i < window.QUAKEGUARD_ZONES.length; i++) {
            if (window.QUAKEGUARD_ZONES[i].id === id) return window.QUAKEGUARD_ZONES[i];
        }
        return window.QUAKEGUARD_ZONES[0];
    }

    function updateMagnitude() {
        if (magRead) magRead.textContent = parseFloat(magSlider.value).toFixed(1);
        magSlider.setAttribute('aria-valuetext', 'Magnitude ' + parseFloat(magSlider.value).toFixed(1));
    }
    magSlider.addEventListener('input', updateMagnitude);
    updateMagnitude();

    function nowStamp() {
        var d = new Date();
        function p(n) { return (n < 10 ? '0' : '') + n; }
        return p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds());
    }

    function log(html, cls) {
        if (!consoleEl) return;
        var line = document.createElement('div');
        line.className = 'demo-line ' + (cls || '');
        var t = document.createElement('span');
        t.className = 't';
        t.textContent = nowStamp();
        line.appendChild(t);
        line.insertAdjacentHTML('beforeend', html);
        consoleEl.appendChild(line);
        consoleEl.scrollTop = consoleEl.scrollHeight;
    }

    function showToast(text) {
        if (!toast) return;
        toast.textContent = text;
        toast.style.display = 'block';
        toast.style.animation = 'none';
        void toast.offsetWidth;
        toast.style.animation = 'toastIn 0.3s ease';
        window.clearTimeout(showToast._t);
        showToast._t = window.setTimeout(function () { toast.style.display = 'none'; }, 2600);
    }

    function loadHistory() {
        try { return JSON.parse(localStorage.getItem(STORE_KEY)) || []; }
        catch (e) { return []; }
    }
    function saveHistory(h) { try { localStorage.setItem(STORE_KEY, JSON.stringify(h)); } catch (e) {} }

    function renderFeed() {
        var items = loadHistory();
        feed.innerHTML = '';
        if (!items.length) {
            feed.innerHTML = '<div class="text-center text-muted small py-3">No events yet. Trigger an earthquake below.</div>';
            return;
        }
        items.forEach(function (it) {
            var el = document.createElement('a');
            el.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
            el.style.background = 'rgba(3,21,32,0.6)';
            el.style.color = '#eaf2ff';
            el.style.border = '1px solid rgba(255,255,255,0.08)';

            var left = document.createElement('div');
            var tspan = document.createElement('span');
            tspan.className = 't';
            tspan.style.color = '#00f5ff';
            tspan.textContent = it.time;
            left.appendChild(tspan);
            left.appendChild(document.createTextNode(' \u00a0 '));
            var zname = document.createElement('strong');
            zname.textContent = it.zone;
            left.appendChild(zname);
            var msg = document.createElement('div');
            msg.className = 'small';
            msg.style.color = '#9db4d0';
            msg.textContent = it.message;
            left.appendChild(msg);

            var badge = document.createElement('span');
            badge.className = 'badge rounded-pill text-bg-warning';
            badge.textContent = 'M ' + it.mag.toFixed(1);

            el.appendChild(left);
            el.appendChild(badge);
            feed.appendChild(el);
        });
    }

    function pipelineSteps() {
        return [
            { txt: T('dp_1'), ok: true },
            { txt: T('dp_2'), ok: true },
            { txt: T('dp_3'), ok: true },
            { txt: T('dp_4'), ok: true },
            { txt: T('dp_5'), ok: true },
            { txt: T('dp_6'), ok: true },
            { txt: T('dp_7'), ok: true },
            { txt: T('dp_8'), ok: true },
            { txt: T('dp_9'), ok: true },
            { txt: T('dp_10'), ok: true },
            { txt: T('dp_11'), final: true }
        ];
    }

    function aiSeverity(mag) {
        if (mag >= 7.0) return 'Severe';
        if (mag >= 6.0) return 'Strong';
        if (mag >= 5.0) return 'Moderate';
        return 'Light';
    }

    function renderAiReport(zone, mag) {
        if (!aiTitle || !aiBody) return;
        var sev = aiSeverity(mag);
        aiTitle.textContent = 'Magnitude ' + mag.toFixed(1) + ' · ' + T('zone_' + zone.id);
        aiBody.textContent = sev + ' event estimated at M' + mag.toFixed(1) + ' in the ' + zone.cover +
            ' region. Shaking intensity IV–V MMI; recommend staying away from windows and tall furniture, and monitoring aftershocks over the next 2 hours.';
    }

    triggerBtn.addEventListener('click', function () {
        var zone = selectedZone();
        var mag = parseFloat(magSlider.value);
        var message = msgInput.value.trim() || T('demo_msg_ph');

        // Harmless edge: vibrate the device if the browser supports it.
        try { if (window.navigator.vibrate) window.navigator.vibrate([120, 70, 120, 70, 240]); } catch (e) {}

        // Animate the ingestion → alert pipeline.
        var steps = pipelineSteps();
        var i = 0;
        var interval = window.setInterval(function () {
            if (i < steps.length) {
                var step = steps[i];
                log(step.txt, step.cls || (step.ok ? 'ok' : ''));
                i++;
            } else {
                window.clearInterval(interval);
                var items = loadHistory();
                items.unshift({
                    time: nowStamp(),
                    zone: T('zone_' + zone.id),
                    mag: mag,
                    message: message + ' · ' + zone.cover
                });
                if (items.length > 10) items.length = 10;
                saveHistory(items);
                renderFeed();
                renderAiReport(zone, mag);
                showToast('ALERT · M' + mag.toFixed(1) + ' · ' + T('zone_' + zone.id).toUpperCase());
            }
        }, 160);
    });

    renderFeed();
})();