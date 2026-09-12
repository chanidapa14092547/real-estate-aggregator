// ============================================
// Real Estate Dashboard - Pumpkin Grill
// ============================================

// === Utilities ===
const formatThaiPrice = (num) => {
    if (!num || isNaN(num)) return '฿0';
    if (num >= 1_000_000) {
        return `฿${(num / 1_000_000).toFixed(2)} ล้าน`;
    } else if (num >= 100_000) {
        return `฿${(num / 100_000).toFixed(1)} แสน`;
    }
    return `฿${Math.round(num).toLocaleString()}`;
};

const formatNumber = (num) => {
    if (!num || isNaN(num)) return '0';
    return Math.round(num).toLocaleString();
};

const formatCompact = (num) => {
    if (!num || isNaN(num)) return '0';
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(0)}K`;
    return num.toString();
};

// Count-up animation
const animateValue = (element, start, end, duration, formatter) => {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(eased * (end - start) + start);
        
        if (progress < 1) {
            element.textContent = formatNumber(current);
            window.requestAnimationFrame(step);
        } else {
            element.textContent = formatter(end);
        }
    };
    window.requestAnimationFrame(step);
};

// === Chart.js Global Config ===
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = 'Inter, sans-serif';
Chart.defaults.font.size = 12;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 15, 35, 0.95)';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(99, 102, 241, 0.3)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.padding = 12;

const gridColor = 'rgba(255, 255, 255, 0.06)';
const chartColors = {
    indigo: 'rgba(99, 102, 241, 0.8)',
    violet: 'rgba(139, 92, 246, 0.8)',
    emerald: 'rgba(16, 185, 129, 0.8)',
    amber: 'rgba(245, 158, 11, 0.8)',
    rose: 'rgba(244, 63, 94, 0.8)',
    cyan: 'rgba(6, 182, 212, 0.8)',
};

// === Global State ===
let currentPage = 1;
const perPage = 15;

// === Init ===
document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchCharts();
    fetchListings();
    fetchPipeline();

    document.getElementById('predict-form').addEventListener('submit', handlePredict);
    document.getElementById('filter-type').addEventListener('change', () => { currentPage = 1; fetchListings(); });
    document.getElementById('filter-zone').addEventListener('change', () => { currentPage = 1; fetchListings(); });
});

// === Stats Cards ===
async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        
        if (data.error) {
            document.getElementById('stat-total').textContent = 'ไม่มีข้อมูล';
            return;
        }

        animateValue(
            document.getElementById('stat-total'), 0, data.total_listings, 2000,
            (v) => formatNumber(v)
        );
        animateValue(
            document.getElementById('stat-avg-price'), 0, data.avg_price, 2000,
            (v) => formatThaiPrice(v)
        );
        animateValue(
            document.getElementById('stat-avg-sqm'), 0, Math.round(data.avg_price_per_sqm), 2000,
            (v) => `฿${formatNumber(v)} / ตร.ม.`
        );
        animateValue(
            document.getElementById('stat-median'), 0, data.median_price, 2000,
            (v) => formatThaiPrice(v)
        );
    } catch (e) {
        console.error('Error fetching stats:', e);
    }
}

// === Charts ===
async function fetchCharts() {
    // 1. Price by Zone (Bar)
    fetch('/api/charts/price-by-zone').then(r => r.json()).then(data => {
        const ctx = document.getElementById('chart-price-by-zone').getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(99, 102, 241, 0.8)');
        gradient.addColorStop(1, 'rgba(139, 92, 246, 0.4)');

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'ราคาเฉลี่ย (บาท)',
                    data: data.data,
                    backgroundColor: gradient,
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `ราคาเฉลี่ย: ${formatThaiPrice(ctx.raw)}`
                        }
                    }
                },
                scales: {
                    y: { grid: { color: gridColor }, ticks: { callback: (v) => formatCompact(v) } },
                    x: { grid: { display: false } }
                }
            }
        });
    });

    // 2. Type Breakdown (Doughnut)
    fetch('/api/charts/type-breakdown').then(r => r.json()).then(data => {
        new Chart(document.getElementById('chart-type-breakdown'), {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.data,
                    backgroundColor: [chartColors.indigo, chartColors.violet, chartColors.emerald, chartColors.amber],
                    borderWidth: 0,
                    hoverOffset: 8,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '68%',
                plugins: {
                    legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyle: 'circle' } },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.label}: ${formatNumber(ctx.raw)} ประกาศ (${((ctx.raw / ctx.dataset.data.reduce((a,b)=>a+b,0)) * 100).toFixed(1)}%)`
                        }
                    }
                }
            }
        });
    });

    // 3. Price vs Area (Scatter)
    fetch('/api/charts/price-vs-area').then(r => r.json()).then(data => {
        const scatterColors = [chartColors.indigo, chartColors.emerald, chartColors.amber, chartColors.rose];
        data.datasets.forEach((ds, i) => {
            ds.backgroundColor = scatterColors[i % scatterColors.length];
            ds.pointRadius = 3.5;
            ds.pointHoverRadius = 6;
        });
        new Chart(document.getElementById('chart-price-vs-area'), {
            type: 'scatter',
            data: { datasets: data.datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { padding: 12, usePointStyle: true } },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.x.toFixed(0)} ตร.ม. / ${formatThaiPrice(ctx.raw.y)}`
                        }
                    }
                },
                scales: {
                    y: { grid: { color: gridColor }, title: { display: true, text: 'ราคา (บาท)', color: '#94a3b8' }, ticks: { callback: v => formatCompact(v) } },
                    x: { grid: { color: gridColor }, title: { display: true, text: 'พื้นที่ (ตร.ม.)', color: '#94a3b8' } }
                }
            }
        });
    });

    // 4. Price Distribution (Histogram)
    fetch('/api/charts/price-distribution').then(r => r.json()).then(data => {
        const ctx = document.getElementById('chart-price-distribution').getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(139, 92, 246, 0.8)');
        gradient.addColorStop(1, 'rgba(99, 102, 241, 0.3)');

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'จำนวนประกาศ',
                    data: data.data,
                    backgroundColor: gradient,
                    borderRadius: 4,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: gridColor } },
                    x: { grid: { display: false }, ticks: { maxRotation: 45, font: { size: 10 } } }
                }
            }
        });
    });

    // 5. Price Trend (Line)
    fetch('/api/charts/price-trend').then(r => r.json()).then(data => {
        const ctx = document.getElementById('chart-price-trend').getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.2)');
        gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'ราคาเฉลี่ย',
                    data: data.data,
                    borderColor: chartColors.emerald,
                    borderWidth: 2.5,
                    tension: 0.4,
                    fill: true,
                    backgroundColor: gradient,
                    pointBackgroundColor: chartColors.emerald,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: (ctx) => `ราคาเฉลี่ย: ${formatThaiPrice(ctx.raw)}` } }
                },
                scales: {
                    y: { grid: { color: gridColor }, ticks: { callback: v => formatCompact(v) } },
                    x: { grid: { color: gridColor }, ticks: { maxRotation: 45, font: { size: 10 } } }
                }
            }
        });
    });

    // 6. Feature Importance (Horizontal Bar)
    fetch('/api/charts/feature-importance').then(r => r.json()).then(data => {
        new Chart(document.getElementById('chart-feature-importance'), {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'ความสำคัญ',
                    data: data.data,
                    backgroundColor: chartColors.amber,
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: gridColor } },
                    y: { grid: { display: false }, ticks: { font: { size: 11 } } }
                }
            }
        });
    });
}

// === Data Table ===
async function fetchListings() {
    const type = document.getElementById('filter-type').value;
    const zone = document.getElementById('filter-zone').value;
    
    let url = `/api/listings?page=${currentPage}&per_page=${perPage}`;
    if (type !== 'all') url += `&type=${encodeURIComponent(type)}`;
    if (zone !== 'all') url += `&zone=${encodeURIComponent(zone)}`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        
        const tbody = document.getElementById('listings-tbody');
        tbody.innerHTML = '';
        
        if (data.listings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:2rem; color:var(--text-muted)">ไม่พบข้อมูล</td></tr>';
            document.getElementById('pagination').innerHTML = '';
            return;
        }
        
        data.listings.forEach((item, i) => {
            const tr = document.createElement('tr');
            tr.style.animationDelay = `${i * 30}ms`;
            tr.innerHTML = `
                <td title="${item.title || ''}">${(item.title || 'ไม่มีหัวข้อ').substring(0, 40)}${(item.title || '').length > 40 ? '...' : ''}</td>
                <td><span class="type-badge">${item.property_type || '-'}</span></td>
                <td>${item.location || '-'}</td>
                <td><span class="zone-badge zone-${(item.zone || '').replace(/\s/g, '-')}">${item.zone || '-'}</span></td>
                <td class="price-cell">${formatThaiPrice(item.price_thb)}</td>
                <td>${item.area_sqm ? parseFloat(item.area_sqm).toFixed(0) + ' ตร.ม.' : '-'}</td>
                <td>${item.price_per_sqm ? '฿' + formatNumber(Math.round(parseFloat(item.price_per_sqm))) : '-'}</td>
            `;
            tbody.appendChild(tr);
        });

        // Pagination
        renderPagination(data.page, data.pages);
        
    } catch (e) {
        console.error('Error fetching listings:', e);
    }
}

function renderPagination(current, total) {
    const pag = document.getElementById('pagination');
    pag.innerHTML = '';
    
    if (total <= 1) return;
    
    const maxButtons = 7;
    let start = Math.max(1, current - Math.floor(maxButtons / 2));
    let end = Math.min(total, start + maxButtons - 1);
    if (end - start < maxButtons - 1) start = Math.max(1, end - maxButtons + 1);
    
    // Previous
    if (current > 1) {
        const prev = document.createElement('button');
        prev.className = 'page-btn';
        prev.textContent = '‹';
        prev.onclick = () => { currentPage = current - 1; fetchListings(); };
        pag.appendChild(prev);
    }
    
    // First page
    if (start > 1) {
        addPageBtn(pag, 1, current);
        if (start > 2) {
            const dots = document.createElement('span');
            dots.className = 'page-dots';
            dots.textContent = '...';
            pag.appendChild(dots);
        }
    }
    
    // Page buttons
    for (let i = start; i <= end; i++) {
        addPageBtn(pag, i, current);
    }
    
    // Last page
    if (end < total) {
        if (end < total - 1) {
            const dots = document.createElement('span');
            dots.className = 'page-dots';
            dots.textContent = '...';
            pag.appendChild(dots);
        }
        addPageBtn(pag, total, current);
    }
    
    // Next
    if (current < total) {
        const next = document.createElement('button');
        next.className = 'page-btn';
        next.textContent = '›';
        next.onclick = () => { currentPage = current + 1; fetchListings(); };
        pag.appendChild(next);
    }
}

function addPageBtn(container, pageNum, current) {
    const btn = document.createElement('button');
    btn.className = `page-btn ${pageNum === current ? 'active' : ''}`;
    btn.textContent = pageNum;
    btn.onclick = () => { currentPage = pageNum; fetchListings(); };
    container.appendChild(btn);
}

// === Price Predictor ===
async function handlePredict(e) {
    e.preventDefault();
    
    const btn = document.getElementById('predict-btn');
    const spinner = document.getElementById('predict-spinner');
    const resultDiv = document.getElementById('prediction-result');
    
    btn.disabled = true;
    spinner.classList.remove('hidden');
    resultDiv.classList.add('hidden');
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    data.has_bts = formData.get('has_bts') === 'on' ? 1 : 0;
    
    ['area_sqm', 'bedrooms', 'bathrooms', 'floor'].forEach(k => {
        data[k] = parseFloat(data[k]) || 0;
    });

    try {
        const res = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        
        if (result.error) {
            alert('เกิดข้อผิดพลาด: ' + result.error);
        } else {
            const priceEl = document.getElementById('predicted-price');
            priceEl.textContent = result.formatted_price;
            document.getElementById('model-info').textContent = `โมเดล: ${result.model_info}`;
            resultDiv.classList.remove('hidden');
            
            // Animate the result
            resultDiv.style.animation = 'none';
            resultDiv.offsetHeight; // Trigger reflow
            resultDiv.style.animation = 'fadeIn 0.5s ease';
        }
    } catch (err) {
        console.error('Prediction error:', err);
        alert('ไม่สามารถทำนายราคาได้');
    } finally {
        btn.disabled = false;
        spinner.classList.add('hidden');
    }
}

// === Pipeline Report ===
async function fetchPipeline() {
    try {
        const res = await fetch('/api/pipeline-report');
        const data = await res.json();
        const container = document.getElementById('pipeline-content');
        
        if (!data.initial_rows) {
            container.innerHTML = '<p style="color: var(--text-muted)">ยังไม่มีรายงาน — กรุณารัน pipeline ก่อน</p>';
            return;
        }
        
        const ops = data.operations || {};
        const dedupRemoved = ops.deduplication || 0;
        const missingRemoved = ops.missing_values || 0;
        const spamRemoved = ops.spam_outliers || 0;
        const totalRemoved = dedupRemoved + missingRemoved + spamRemoved;
        
        const afterDedup = data.initial_rows - dedupRemoved;
        const afterMissing = afterDedup - missingRemoved;
        const afterSpam = afterMissing - spamRemoved;
        
        const steps = [
            { label: 'ข้อมูลเริ่มต้น', val: data.initial_rows, color: '#94a3b8', detail: `${formatNumber(data.initial_rows)} records` },
            { label: 'ลบข้อมูลซ้ำ', val: afterDedup, color: '#6366f1', detail: `-${formatNumber(dedupRemoved)} ซ้ำ` },
            { label: 'จัดการค่าว่าง', val: afterMissing, color: '#8b5cf6', detail: `-${formatNumber(missingRemoved)} ค่าว่าง` },
            { label: 'กรองสแปม/Outlier', val: afterSpam, color: '#f59e0b', detail: `-${formatNumber(spamRemoved)} สแปม` },
            { label: 'ข้อมูลสุดท้าย', val: data.final_rows || afterSpam, color: '#10b981', detail: `${formatNumber(data.final_rows || afterSpam)} records` },
        ];
        
        const max = data.initial_rows || 1;
        
        let html = `
            <div class="pipeline-summary">
                <div class="pipeline-stat">
                    <span class="pipeline-stat-label">เวลาทั้งหมด</span>
                    <span class="pipeline-stat-value">${data.total_time || 0}s</span>
                </div>
                <div class="pipeline-stat">
                    <span class="pipeline-stat-label">ลบทั้งหมด</span>
                    <span class="pipeline-stat-value" style="color: var(--warning)">${formatNumber(totalRemoved)}</span>
                </div>
                <div class="pipeline-stat">
                    <span class="pipeline-stat-label">Best Model R²</span>
                    <span class="pipeline-stat-value" style="color: var(--success)">${getBestR2(data.modeling)}</span>
                </div>
            </div>
        `;
        
        html += steps.map(s => `
            <div class="pipeline-bar">
                <div class="pipeline-label">${s.label}</div>
                <div class="pipeline-track">
                    <div class="pipeline-fill" style="width: 0%; background: ${s.color}" data-width="${(s.val / max) * 100}%"></div>
                </div>
                <div class="pipeline-val">${s.detail}</div>
            </div>
        `).join('');
        
        container.innerHTML = html;
        
        // Animate bars
        setTimeout(() => {
            container.querySelectorAll('.pipeline-fill').forEach(el => {
                el.style.width = el.getAttribute('data-width');
            });
        }, 200);
        
    } catch (e) {
        console.error('Error fetching pipeline report:', e);
    }
}

function getBestR2(modeling) {
    if (!modeling) return 'N/A';
    let best = 0;
    for (const [name, metrics] of Object.entries(modeling)) {
        if (metrics.R2 > best) best = metrics.R2;
    }
    return best.toFixed(4);
}
