(function () {
    'use strict';

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function starString(rating) {
        const full = Math.floor(rating);
        return '★'.repeat(full) + (rating % 1 ? '☆' : '');
    }

    function itemHtml(item, rank) {
        const qty = String(rank).padStart(2, '0');
        if (item.kind === 'book') {
            return (
                '<div class="ticket-item" data-key="' + item._key + '">' +
                    '<div class="ticket-item-row">' +
                        '<span class="item-qty">' + qty + '</span>' +
                        '<span class="item-name">' + escapeHtml(item.title.toUpperCase()) + ' &ndash; ' + escapeHtml(item.author.toUpperCase()) + '</span>' +
                        '<span class="item-amt">' + item.pages + 'pg</span>' +
                    '</div>' +
                    '<div class="ticket-item-sub">' + starString(item.rating) + ' (' + item.rating.toFixed(1) + ') &middot; ' + item.duration + 'd</div>' +
                '</div>'
            );
        }
        return (
            '<div class="ticket-item" data-key="' + item._key + '">' +
                '<div class="ticket-item-row">' +
                    '<span class="item-qty">' + qty + '</span>' +
                    '<span class="item-name">' + escapeHtml(item.name.toUpperCase()) + '</span>' +
                    '<span class="item-amt">x' + item.amount + '</span>' +
                '</div>' +
            '</div>'
        );
    }

    function rankRowHtml(item, position, total) {
        const label = item.kind === 'book' ? item.title : item.name;
        let options = '';
        for (let i = 1; i <= total; i++) {
            options += '<option value="' + i + '"' + (i === position ? ' selected' : '') + '>' + i + '</option>';
        }
        return (
            '<div class="rank-row" data-key="' + item._key + '">' +
                '<select class="rank-select" aria-label="Rank for ' + escapeHtml(label) + '">' + options + '</select>' +
                '<span class="rank-row-name">' + escapeHtml(label) + '</span>' +
            '</div>'
        );
    }

    function init() {
        const dataEl = document.getElementById('ticketData');
        const ticketItemsEl = document.getElementById('ticketItems');
        const rankListEl = document.getElementById('rankList');

        // --- Period / Length pill groups: set hidden input, submit form ---
        document.querySelectorAll('.pill-group[data-hidden]').forEach(function (group) {
            const hidden = document.getElementById(group.getAttribute('data-hidden'));
            group.querySelectorAll('.pill').forEach(function (pill) {
                pill.addEventListener('click', function () {
                    hidden.value = pill.getAttribute('data-value');
                    document.getElementById('controlsForm').submit();
                });
            });
        });

        const metricSelect = document.getElementById('metric');
        if (metricSelect) {
            metricSelect.addEventListener('change', function () {
                document.getElementById('controlsForm').submit();
            });
        }

        // --- Font pill group: client-side only, no reload ---
        const fontGroup = document.getElementById('fontPillGroup');
        if (fontGroup) {
            fontGroup.querySelectorAll('.pill').forEach(function (pill) {
                pill.addEventListener('click', function () {
                    fontGroup.querySelectorAll('.pill').forEach(function (p) { p.classList.remove('active'); });
                    pill.classList.add('active');
                    const ticket = document.getElementById('ticket');
                    ticket.classList.toggle('ticket-compatible', pill.getAttribute('data-value') === 'compatible');
                    ticket.classList.toggle('ticket-classic', pill.getAttribute('data-value') !== 'compatible');
                });
            });
        }

        // --- Client-side reorder via rank dropdowns ---
        if (dataEl && ticketItemsEl && rankListEl) {
            let items = JSON.parse(dataEl.textContent || '[]').map(function (item, index) {
                item._key = index;
                return item;
            });

            function render() {
                const total = items.length;
                ticketItemsEl.innerHTML = items.map(function (item, i) { return itemHtml(item, i + 1); }).join('');
                rankListEl.innerHTML = items.map(function (item, i) { return rankRowHtml(item, i + 1, total); }).join('');
            }

            rankListEl.addEventListener('change', function (e) {
                if (!e.target.classList.contains('rank-select')) return;
                const row = e.target.closest('.rank-row');
                const key = parseInt(row.getAttribute('data-key'), 10);
                const fromIndex = items.findIndex(function (item) { return item._key === key; });
                const toIndex = parseInt(e.target.value, 10) - 1;
                if (fromIndex === -1 || toIndex === fromIndex) return;
                const [moved] = items.splice(fromIndex, 1);
                items.splice(toIndex, 0, moved);
                render();
            });

            render();
        }

        // --- Action buttons ---
        const ticketEl = document.getElementById('ticket');

        const printBtn = document.getElementById('printBtn');
        if (printBtn) {
            printBtn.addEventListener('click', function () { window.print(); });
        }

        const downloadBtn = document.getElementById('downloadImageBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', function () {
                if (typeof html2canvas !== 'function') {
                    alert('Image export is unavailable right now. Please try again in a moment.');
                    return;
                }
                html2canvas(ticketEl, { backgroundColor: '#fffef8', scale: 2 }).then(function (canvas) {
                    const link = document.createElement('a');
                    link.download = 'read-receipt.png';
                    link.href = canvas.toDataURL('image/png');
                    link.click();
                });
            });
        }

        const viewTabBtn = document.getElementById('viewNewTabBtn');
        if (viewTabBtn) {
            viewTabBtn.addEventListener('click', function () {
                const win = window.open('', '_blank');
                if (!win) return;
                win.document.write(
                    '<!DOCTYPE html><html><head><title>ReadReceipts</title>' +
                    '<link rel="stylesheet" href="/static/style.css"></head>' +
                    '<body style="display:flex;justify-content:center;padding:2rem;background:#e9ded0;">' +
                    ticketEl.outerHTML +
                    '</body></html>'
                );
                win.document.close();
            });
        }
    }

    document.addEventListener('DOMContentLoaded', init);
})();
