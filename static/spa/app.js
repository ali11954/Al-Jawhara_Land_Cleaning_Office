/* ═══════════════════════════════════════════════════════════════
   Cleaning Company Management System - SPA
   ═══════════════════════════════════════════════════════════════ */
let currentPage = 'dashboard';
let charts = {};

// ── Utility ──
const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

function scoreClass(score) {
    if (score >= 90) return 'score-excellent';
    if (score >= 70) return 'score-good';
    if (score >= 50) return 'score-average';
    return 'score-poor';
}

function scoreBadge(score) {
    return `<span class="badge ${score >= 90 ? 'badge-success' : score >= 70 ? 'badge-info' : score >= 50 ? 'badge-warning' : 'badge-danger'}">${score}%</span>`;
}

function statusBadge(status) {
    const map = { present: ['badge-success', 'حاضر'], absent: ['badge-danger', 'غائب'], late: ['badge-warning', 'متأخر'], active: ['badge-success', 'نشط'], inactive: ['badge-danger', 'غير نشط'], paid: ['badge-success', 'مدفوع'], unpaid: ['badge-warning', 'غير مدفوع'] };
    const [cls, text] = map[status] || ['badge-secondary', status];
    return `<span class="badge ${cls}">${text}</span>`;
}

async function api(path, opts = {}) {
    const res = await fetch(`/api/v1${path}`, {
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', ...opts.headers },
        ...opts,
        body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    const data = await res.json();
    if (res.status === 401) { showPage('login'); return null; }
    return data;
}

function showAlert(msg, type = 'success') {
    const el = $('#alertBox');
    el.textContent = msg;
    el.className = `alert alert-${type}`;
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 3000);
}

function openModal(title, bodyHtml, footerHtml = '') {
    $('#modalTitle').textContent = title;
    $('#modalBody').innerHTML = bodyHtml;
    $('#modalFooter').innerHTML = footerHtml;
    $('#modalOverlay').classList.add('active');
}

function closeModal() { $('#modalOverlay').classList.remove('active'); }

async function handleLogin() {
    const username = $('#loginUsername').value.trim();
    const password = $('#loginPassword').value;
    const errEl = $('#loginError');
    errEl.style.display = 'none';
    try {
        const res = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
            credentials: 'same-origin',
        });
        const data = await res.json();
        if (data.status === 'ok') {
            const r = await api('/profile');
            if (r && r.status === 'ok') {
                $('#userDisplay').textContent = r.data.username;
                navigate('dashboard');
            } else {
                errEl.textContent = 'خطأ في تحميل البيانات';
                errEl.style.display = 'block';
            }
        } else {
            errEl.textContent = data.message || 'بيانات الدخول غير صحيحة';
            errEl.style.display = 'block';
        }
    } catch (err) {
        errEl.textContent = 'خطأ في الاتصال بالخادم';
        errEl.style.display = 'block';
    }
}

function navigate(page) {
    currentPage = page;
    document.querySelectorAll('.topnav-links a').forEach(a => a.classList.toggle('active', a.dataset.page === page));
    document.getElementById('navLinks').classList.remove('open');
    showPage(page);
}

async function showPage(page) {
    if (page === 'login') { $('#loginPage').style.display = 'flex'; $('#appLayout').classList.remove('active'); return; }
    $('#loginPage').style.display = 'none'; $('#appLayout').classList.add('active');
    Object.values(charts).forEach(c => c.destroy()); charts = {};
    const fn = { dashboard: loadDashboard, employees: loadEmployees, attendance: loadAttendance, evaluations: loadEvaluations, companies: loadCompanies, salaries: loadSalaries, contracts: loadContracts, invoices: loadInvoices, suppliers: loadSuppliers, supplierInvoices: loadSupplierInvoices, accounts: loadAccounts, journal: loadJournal, loans: loadLoans, penalties: loadPenalties, overtime: loadOvertime, users: loadUsers, reports: loadReports, settings: loadSettings }[page];
    if (fn) await fn();
}

// ═══════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════
async function loadDashboard() {
    const r = await api('/dashboard');
    if (!r || r.status !== 'ok') return;
    const s = r.data.stats;
    let html = `
    <div class="stats-grid">
        <div class="stat-card"><div class="label">إجمالي الموظفين</div><div class="value">${s.total_employees}</div></div>
        <div class="stat-card success"><div class="label">الموظفون النشطون</div><div class="value">${s.active_employees}</div></div>
        <div class="stat-card warning"><div class="label">الشركات</div><div class="value">${s.total_companies}</div></div>
        <div class="stat-card"><div class="label">المناطق</div><div class="value">${s.total_areas}</div></div>
        <div class="stat-card success"><div class="label">التقييمات اليوم</div><div class="value">${s.evaluations_today}</div></div>
        <div class="stat-card warning"><div class="label">متوسط التقييم</div><div class="value ${scoreClass(s.avg_score)}">${s.avg_score}%</div></div>
        <div class="stat-card success"><div class="label">الحاضرون اليوم</div><div class="value">${s.present_today}</div></div>
    </div>
    <div class="charts-grid">
        <div class="chart-box"><h3>التقييمات - آخر 7 أيام</h3><canvas id="evalChart"></canvas></div>
        <div class="chart-box"><h3>الحضور - آخر 7 أيام</h3><canvas id="attChart"></canvas></div>
    </div>
    <div class="card">
        <div class="card-header"><h3>آخر التقييمات</h3></div>
        <div class="table-wrap">
            <table><thead><tr><th>التقييم</th><th>المُقيَّم</th><th>التاريخ</th><th>الدرجة</th></tr></thead>
            <tbody>${r.data.recent_evaluations.map(e => `<tr><td>${e.evaluated || '-'}</td><td>${e.evaluator || '-'}</td><td>${e.date || '-'}</td><td>${scoreBadge(e.score)}</td></tr>`).join('') || '<tr><td colspan="4" style="text-align:center;color:var(--text-secondary)">لا توجد تقييمات</td></tr>'}</tbody></table>
        </div>
    </div>`;
    $('#pageContent').innerHTML = html;

    const c1 = r.data.charts.evaluation;
    charts.eval = new Chart($('#evalChart'), { type: 'line', data: { labels: c1.labels, datasets: [{ label: 'التقييم %', data: c1.data, borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,.1)', fill: true, tension: .4 }] }, options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 100 } } } });
    const c2 = r.data.charts.attendance;
    charts.att = new Chart($('#attChart'), { type: 'bar', data: { labels: c2.labels, datasets: [{ label: 'حاضر', data: c2.present, backgroundColor: '#16a34a' }, { label: 'غائب', data: c2.absent, backgroundColor: '#dc2626' }] }, options: { responsive: true, scales: { x: { stacked: true }, y: { beginAtZero: true, stacked: true } } } });
}

// ═══════════════════════════════════════════════════
// EMPLOYEES
// ═══════════════════════════════════════════════════
async function loadEmployees() {
    const r = await api('/employees');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>الموظفون</h2><button class="btn btn-primary" onclick="showAddEmployee()">+ إضافة موظف</button></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>الكود</th><th>الاسم</th><th>الوظيفة</th><th>الشركة</th><th>الراتب</th><th>الحالة</th><th>إجراءات</th></tr></thead><tbody>
    ${r.data.map(e => `<tr><td>${e.code}</td><td><a href="#" onclick="showEmployeeDetail(${e.id});return false" style="color:var(--primary);text-decoration:none">${e.full_name}</a></td><td>${e.position || '-'}</td><td>${e.company || '-'}</td><td>${(e.salary || 0).toLocaleString()}</td><td>${statusBadge(e.is_active ? 'active' : 'inactive')}</td>
    <td class="actions"><button class="btn btn-outline btn-sm" onclick="showEditEmployee(${e.id})">تعديل</button><button class="btn btn-danger btn-sm" onclick="deleteEmployee(${e.id})">تعطيل</button></td></tr>`).join('')}
    </tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

async function showAddEmployee() {
    const cos = await api('/companies');
    const options = cos && cos.status === 'ok' ? cos.data.map(c => `<option value="${c.id}">${c.name}</option>`).join('') : '';
    openModal('إضافة موظف', `
    <div class="form-group"><label>الاسم الكامل</label><input id="emp_name" required></div>
    <div class="grid-2"><div class="form-group"><label>الهاتف</label><input id="emp_phone"></div><div class="form-group"><label>الوظيفة</label><select id="emp_position"><option value="worker">عامل</option><option value="supervisor">مشرف</option><option value="driver">سائق</option></select></div></div>
    <div class="grid-2"><div class="form-group"><label>الراتب الكلي</label><input type="number" id="emp_salary" value="60000"></div><div class="form-group"><label>الراتب الأساسي</label><input type="number" id="emp_base" value="50000"></div></div>
    <div class="grid-2"><div class="form-group"><label>تاريخ التعيين</label><input type="date" id="emp_hire"></div><div class="form-group"><label>الشركة</label><select id="emp_company"><option value="">اختر...</option>${options}</select></div></div>`,
    `<button class="btn btn-primary" onclick="saveEmployee()">حفظ</button><button class="btn btn-outline" onclick="closeModal()">إلغاء</button>`);
}

async function saveEmployee() {
    const r = await api('/employees', { method: 'POST', body: {
        full_name: $('#emp_name').value, phone: $('#emp_phone').value, position: $('#emp_position').value,
        salary: +$('#emp_salary').value, base_salary: +$('#emp_base').value,
        hire_date: $('#emp_hire').value, company_id: $('#emp_company').value || null,
    }});
    if (r && r.status === 'ok') { closeModal(); showAlert('تمت الإضافة'); loadEmployees(); } else showAlert(r?.message || 'خطأ', 'error');
}

async function showEditEmployee(id) {
    const r = await api(`/employees/${id}`);
    if (!r || r.status !== 'ok') return;
    const e = r.data;
    const cos = await api('/companies');
    const options = cos && cos.status === 'ok' ? cos.data.map(c => `<option value="${c.id}" ${c.name === e.company ? 'selected' : ''}>${c.name}</option>`).join('') : '';
    openModal('تعديل موظف', `
    <div class="form-group"><label>الاسم الكامل</label><input id="emp_name" value="${e.full_name}"></div>
    <div class="grid-2"><div class="form-group"><label>الهاتف</label><input id="emp_phone" value="${e.phone || ''}"></div><div class="form-group"><label>الوظيفة</label><select id="emp_position"><option value="worker" ${e.position === 'worker' ? 'selected' : ''}>عامل</option><option value="supervisor" ${e.position === 'supervisor' ? 'selected' : ''}>مشرف</option><option value="driver" ${e.position === 'driver' ? 'selected' : ''}>سائق</option></select></div></div>
    <div class="grid-2"><div class="form-group"><label>الراتب الكلي</label><input type="number" id="emp_salary" value="${e.salary}"></div><div class="form-group"><label>الراتب الأساسي</label><input type="number" id="emp_base" value="${e.base_salary}"></div></div>
    <div class="grid-2"><div class="form-group"><label>تاريخ التعيين</label><input type="date" id="emp_hire" value="${e.hire_date || ''}"></div><div class="form-group"><label>الشركة</label><select id="emp_company"><option value="">اختر...</option>${options}</select></div></div>`,
    `<button class="btn btn-primary" onclick="updateEmployee(${id})">تحديث</button><button class="btn btn-outline" onclick="closeModal()">إلغاء</button>`);
}

async function updateEmployee(id) {
    const r = await api(`/employees/${id}`, { method: 'PUT', body: {
        full_name: $('#emp_name').value, phone: $('#emp_phone').value, position: $('#emp_position').value,
        salary: +$('#emp_salary').value, base_salary: +$('#emp_base').value,
        hire_date: $('#emp_hire').value, company_id: $('#emp_company').value || null,
    }});
    if (r && r.status === 'ok') { closeModal(); showAlert('تم التحديث'); loadEmployees(); } else showAlert(r?.message || 'خطأ', 'error');
}

async function deleteEmployee(id) {
    if (!confirm('هل تريد تعطيل هذا الموظف؟')) return;
    const r = await api(`/employees/${id}`, { method: 'DELETE' });
    if (r && r.status === 'ok') { showAlert('تم التعطيل'); loadEmployees(); }
}

async function showEmployeeDetail(id) {
    const r = await api(`/employees/${id}`);
    if (!r || r.status !== 'ok') return;
    const e = r.data;
    const st = e.attendance_stats;
    openModal(`تفاصيل: ${e.full_name}`, `
    <div class="stats-grid" style="margin-bottom:16px">
        <div class="stat-card"><div class="label">الكود</div><div class="value" style="font-size:1.2rem">${e.code}</div></div>
        <div class="stat-card success"><div class="label">الحضور</div><div class="value" style="font-size:1.2rem">${st.present}</div></div>
        <div class="stat-card danger"><div class="label">الغياب</div><div class="value" style="font-size:1.2rem">${st.absent}</div></div>
        <div class="stat-card warning"><div class="label">التأخير</div><div class="value" style="font-size:1.2rem">${st.late}</div></div>
    </div>
    <p><strong>الهاتف:</strong> ${e.phone || '-'}</p><p><strong>الوظيفة:</strong> ${e.position || '-'}</p>
    <p><strong>الراتب:</strong> ${(e.salary || 0).toLocaleString()}</p><p><strong>الشركة:</strong> ${e.company || '-'}</p>
    <h4 style="margin-top:16px;margin-bottom:8px">آخر الحضور</h4>
    <table><thead><tr><th>التاريخ</th><th>الحالة</th><th>الوردية</th></tr></thead>
    <tbody>${(e.recent_attendance || []).map(a => `<tr><td>${a.date}</td><td>${statusBadge(a.status)}</td><td>${a.shift || '-'}</td></tr>`).join('') || '<tr><td colspan="3" style="text-align:center">لا توجد سجلات</td></tr>'}</tbody></table>`);
}

// ═══════════════════════════════════════════════════
// ATTENDANCE
// ═══════════════════════════════════════════════════
async function loadAttendance() {
    const r = await api('/attendance');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>الحضور</h2><button class="btn btn-primary" onclick="showAddAttendance()">+ تسجيل حضور</button></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>التاريخ</th><th>الموظف</th><th>الحالة</th><th>الوردية</th><th>الدخول</th><th>الخروج</th><th>إجراءات</th></tr></thead><tbody>
    ${r.data.map(a => `<tr><td>${a.date}</td><td>${a.employee}</td><td>${statusBadge(a.status)}</td><td>${a.shift || '-'}</td><td>${a.check_in || '-'}</td><td>${a.check_out || '-'}</td>
    <td class="actions"><button class="btn btn-outline btn-sm" onclick="showEditAttendance(${a.id})">تعديل</button><button class="btn btn-danger btn-sm" onclick="deleteAttendance(${a.id})">حذف</button></td></tr>`).join('')}
    </tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

async function showAddAttendance() {
    const emps = await api('/employees');
    const options = emps && emps.status === 'ok' ? emps.data.map(e => `<option value="${e.id}">${e.full_name}</option>`).join('') : '';
    openModal('تسجيل حضور', `
    <div class="form-group"><label>الموظف</label><select id="att_emp"><option value="">اختر...</option>${options}</select></div>
    <div class="grid-2"><div class="form-group"><label>التاريخ</label><input type="date" id="att_date" value="${new Date().toISOString().slice(0,10)}"></div><div class="form-group"><label>الحالة</label><select id="att_status"><option value="present">حاضر</option><option value="absent">غائب</option><option value="late">متأخر</option></select></div></div>
    <div class="grid-2"><div class="form-group"><label>الوردية</label><select id="att_shift"><option value="morning">صباحية</option><option value="evening">مسائية</option></select></div></div>
    <div class="grid-2"><div class="form-group"><label>وقت الدخول</label><input type="time" id="att_checkin"></div><div class="form-group"><label>وقت الخروج</label><input type="time" id="att_checkout"></div></div>`,
    `<button class="btn btn-primary" onclick="saveAttendance()">حفظ</button><button class="btn btn-outline" onclick="closeModal()">إلغاء</button>`);
}

async function saveAttendance() {
    const r = await api('/attendance', { method: 'POST', body: {
        employee_id: +$('#att_emp').value, date: $('#att_date').value, status: $('#att_status').value,
        shift_type: $('#att_shift').value, check_in: $('#att_checkin').value || null, check_out: $('#att_checkout').value || null,
    }});
    if (r && r.status === 'ok') { closeModal(); showAlert('تم التسجيل'); loadAttendance(); } else showAlert(r?.message || 'خطأ', 'error');
}

async function showEditAttendance(id) {
    const list = await api('/attendance');
    if (!list || list.status !== 'ok') return;
    const a = list.data.find(x => x.id === id);
    if (!a) return;
    openModal('تعديل حضور', `
    <div class="form-group"><label>الموظف</label><input value="${a.employee}" disabled></div>
    <div class="grid-2"><div class="form-group"><label>التاريخ</label><input value="${a.date}" disabled></div><div class="form-group"><label>الحالة</label><select id="att_status"><option value="present" ${a.status==='present'?'selected':''}>حاضر</option><option value="absent" ${a.status==='absent'?'selected':''}>غائب</option><option value="late" ${a.status==='late'?'selected':''}>متأخر</option></select></div></div>
    <div class="grid-2"><div class="form-group"><label>الوردية</label><select id="att_shift"><option value="morning" ${a.shift==='morning'?'selected':''}>صباحية</option><option value="evening" ${a.shift==='evening'?'selected':''}>مسائية</option></select></div></div>
    <div class="grid-2"><div class="form-group"><label>وقت الدخول</label><input type="time" id="att_checkin" value="${a.check_in || ''}"></div><div class="form-group"><label>وقت الخروج</label><input type="time" id="att_checkout" value="${a.check_out || ''}"></div></div>`,
    `<button class="btn btn-primary" onclick="updateAttendance(${id})">تحديث</button><button class="btn btn-outline" onclick="closeModal()">إلغاء</button>`);
}

async function updateAttendance(id) {
    const r = await api(`/attendance/${id}`, { method: 'PUT', body: {
        status: $('#att_status').value, shift_type: $('#att_shift').value,
        check_in: $('#att_checkin').value || null, check_out: $('#att_checkout').value || null,
    }});
    if (r && r.status === 'ok') { closeModal(); showAlert('تم التحديث'); loadAttendance(); } else showAlert(r?.message || 'خطأ', 'error');
}

async function deleteAttendance(id) {
    if (!confirm('هل تريد حذف هذا السجل؟')) return;
    const r = await api(`/attendance/${id}`, { method: 'DELETE' });
    if (r && r.status === 'ok') { showAlert('تم الحذف'); loadAttendance(); }
}

// ═══════════════════════════════════════════════════
// EVALUATIONS
// ═══════════════════════════════════════════════════
async function loadEvaluations() {
    const r = await api('/evaluations');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>التقييمات</h2><button class="btn btn-primary" onclick="showAddEvaluation()">+ إضافة تقييم</button></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>التاريخ</th><th>المُقيَّم</th><th>المُقيَّم له</th><th>المكان</th><th>الدرجة</th></tr></thead><tbody>
    ${r.data.map(e => `<tr><td>${e.date || '-'}</td><td>${e.evaluator || '-'}</td><td>${e.evaluated || '-'}</td><td>${e.place || '-'}</td><td>${scoreBadge(e.score)}</td></tr>`).join('')}
    </tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

async function showAddEvaluation() {
    const emps = await api('/employees');
    const empOpts = emps && emps.status === 'ok' ? emps.data.map(e => `<option value="${e.id}">${e.full_name}</option>`).join('') : '';
    openModal('إضافة تقييم', `
    <div class="grid-2"><div class="form-group"><label>المُقيَّم</label><select id="eval_by"><option value="">اختر...</option>${empOpts}</select></div><div class="form-group"><label>المُقيَّم له</label><select id="eval_for"><option value="">اختر...</option>${empOpts}</select></div></div>
    <div class="grid-2"><div class="form-group"><label>المكان</label><input id="eval_place"></div><div class="form-group"><label>التاريخ</label><input type="date" id="eval_date" value="${new Date().toISOString().slice(0,10)}"></div></div>
    <div class="grid-3"><div class="form-group"><label>النظافة (1-5)</label><input type="number" id="eval_clean" min="1" max="5" value="3"></div><div class="form-group"><label>التنظيم (1-5)</label><input type="number" id="eval_org" min="1" max="5" value="3"></div><div class="form-group"><label>المعدات (1-5)</label><input type="number" id="eval_equip" min="1" max="5" value="3"></div></div>
    <div class="grid-2"><div class="form-group"><label>الوقت (1-5)</label><input type="number" id="eval_time" min="1" max="5" value="3"></div><div class="form-group"><label>السلامة (1-5)</label><input type="number" id="eval_safety" min="1" max="5" value="3"></div></div>
    <div class="form-group"><label>ملاحظات</label><textarea id="eval_notes" rows="2"></textarea></div>`,
    `<button class="btn btn-primary" onclick="saveEvaluation()">حفظ</button><button class="btn btn-outline" onclick="closeModal()">إلغاء</button>`);
}

async function saveEvaluation() {
    const r = await api('/evaluations', { method: 'POST', body: {
        evaluator_id: +$('#eval_by').value, evaluated_employee_id: +$('#eval_for').value,
        place_id: 1, date: $('#eval_date').value,
        cleanliness: +$('#eval_clean').value, organization: +$('#eval_org').value,
        equipment_condition: +$('#eval_equip').value, time: +$('#eval_time').value,
        safety_measures: +$('#eval_safety').value, comments: $('#eval_notes').value,
    }});
    if (r && r.status === 'ok') { closeModal(); showAlert('تمت الإضافة'); loadEvaluations(); } else showAlert(r?.message || 'خطأ', 'error');
}

// ═══════════════════════════════════════════════════
// COMPANIES
// ═══════════════════════════════════════════════════
async function loadCompanies() {
    const r = await api('/companies');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>الشركات</h2><button class="btn btn-primary" onclick="showAddCompany()">+ إضافة شركة</button></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>الاسم</th><th>الهاتف</th><th>البريد</th><th>المناطق</th><th>الحالة</th><th>إجراءات</th></tr></thead><tbody>
    ${r.data.map(c => `<tr><td><a href="#" onclick="showCompanyDetail(${c.id});return false" style="color:var(--primary);text-decoration:none">${c.name}</a></td><td>${c.phone || '-'}</td><td>${c.email || '-'}</td><td>${c.areas_count}</td><td>${statusBadge(c.is_active ? 'active' : 'inactive')}</td>
    <td class="actions"><button class="btn btn-outline btn-sm" onclick="showEditCompany(${c.id})">تعديل</button><button class="btn btn-danger btn-sm" onclick="deleteCompany(${c.id})">تعطيل</button></td></tr>`).join('')}
    </tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

async function showAddCompany() {
    openModal('إضافة شركة', `
    <div class="form-group"><label>اسم الشركة</label><input id="co_name" required></div>
    <div class="grid-2"><div class="form-group"><label>الهاتف</label><input id="co_phone"></div><div class="form-group"><label>البريد</label><input id="co_email" type="email"></div></div>`,
    `<button class="btn btn-primary" onclick="saveCompany()">حفظ</button><button class="btn btn-outline" onclick="closeModal()">إلغاء</button>`);
}

async function saveCompany() {
    const r = await api('/companies', { method: 'POST', body: { name: $('#co_name').value, phone: $('#co_phone').value, email: $('#co_email').value }});
    if (r && r.status === 'ok') { closeModal(); showAlert('تمت الإضافة'); loadCompanies(); } else showAlert(r?.message || 'خطأ', 'error');
}

async function showEditCompany(id) {
    const r = await api('/companies');
    if (!r || r.status !== 'ok') return;
    const c = r.data.find(x => x.id === id);
    if (!c) return;
    openModal('تعديل شركة', `
    <div class="form-group"><label>اسم الشركة</label><input id="co_name" value="${c.name}"></div>
    <div class="grid-2"><div class="form-group"><label>الهاتف</label><input id="co_phone" value="${c.phone || ''}"></div><div class="form-group"><label>البريد</label><input id="co_email" value="${c.email || ''}" type="email"></div></div>`,
    `<button class="btn btn-primary" onclick="updateCompany(${id})">تحديث</button><button class="btn btn-outline" onclick="closeModal()">إلغاء</button>`);
}

async function updateCompany(id) {
    const r = await api(`/companies/${id}`, { method: 'PUT', body: { name: $('#co_name').value, phone: $('#co_phone').value, email: $('#co_email').value }});
    if (r && r.status === 'ok') { closeModal(); showAlert('تم التحديث'); loadCompanies(); } else showAlert(r?.message || 'خطأ', 'error');
}

async function deleteCompany(id) {
    if (!confirm('هل تريد تعطيل هذه الشركة؟')) return;
    const r = await api(`/companies/${id}`, { method: 'DELETE' });
    if (r && r.status === 'ok') { showAlert('تم التعطيل'); loadCompanies(); }
}

async function showCompanyDetail(id) {
    const r = await api(`/companies/${id}`);
    if (!r || r.status !== 'ok') return;
    const c = r.data;
    openModal(`تفاصيل: ${c.name}`, `
    <p><strong>الهاتف:</strong> ${c.phone || '-'}</p><p><strong>البريد:</strong> ${c.email || '-'}</p>
    <h4 style="margin-top:16px;margin-bottom:8px">المناطق</h4>
    <table><thead><tr><th>الاسم</th><th>المشرف</th></tr></thead>
    <tbody>${(c.areas || []).map(a => `<tr><td>${a.name}</td><td>${a.supervisor || '-'}</td></tr>`).join('') || '<tr><td colspan="2" style="text-align:center">لا توجد مناطق</td></tr>'}</tbody></table>`);
}

// ═══════════════════════════════════════════════════
// SALARIES
// ═══════════════════════════════════════════════════
async function loadSalaries() {
    const r = await api('/salaries');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>الرواتب</h2><button class="btn btn-primary" onclick="calculateSalaries()">حساب الرواتب</button></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>الموظف</th><th>الراتب الأساسي</th><th>البدلات</th><th>الخصومات</th><th>الإجمالي</th><th>الحالة</th></tr></thead><tbody>
    ${r.data.map(s => `<tr><td>${s.employee || '-'}</td><td>${(s.base_salary || 0).toLocaleString()}</td><td>${(s.allowances || 0).toLocaleString()}</td><td>${(s.deductions || 0).toLocaleString()}</td><td style="font-weight:700">${(s.total_salary || 0).toLocaleString()}</td><td>${statusBadge(s.is_paid ? 'paid' : 'unpaid')}</td></tr>`).join('') || '<tr><td colspan="6" style="text-align:center;color:var(--text-secondary)">لا توجد رواتب</td></tr>'}</tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

async function calculateSalaries() {
    const period = prompt('أدخل الفترة (YYYY-MM):', new Date().toISOString().slice(0,7));
    if (!period) return;
    const r = await api('/salaries/calculate', { method: 'POST', body: { period }});
    if (r && r.status === 'ok') { showAlert(r.message); loadSalaries(); } else showAlert(r?.message || 'خطأ', 'error');
}

// ═══════════════════════════════════════════════════
// CONTRACTS
// ═══════════════════════════════════════════════════
async function loadContracts() {
    const r = await api('/contracts');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>العقود</h2><button class="btn btn-primary" onclick="showAddContract()">+ إضافة عقد</button></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>رقم العقد</th><th>الشركة</th><th>من</th><th>إلى</th><th>المبلغ</th><th>الحالة</th></tr></thead><tbody>
    ${r.data.map(c => `<tr><td>${c.contract_number}</td><td>${c.company || '-'}</td><td>${c.start_date || '-'}</td><td>${c.end_date || '-'}</td><td>${(c.total_amount || 0).toLocaleString()}</td><td>${statusBadge(c.status || 'active')}</td></tr>`).join('') || '<tr><td colspan="6" style="text-align:center;color:var(--text-secondary)">لا توجد عقود</td></tr>'}</tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

async function showAddContract() {
    const cos = await api('/companies');
    const options = cos && cos.status === 'ok' ? cos.data.map(c => `<option value="${c.id}">${c.name}</option>`).join('') : '';
    openModal('إضافة عقد', `
    <div class="form-group"><label>رقم العقد</label><input id="cont_num" required></div>
    <div class="form-group"><label>الشركة</label><select id="cont_co"><option value="">اختر...</option>${options}</select></div>
    <div class="grid-2"><div class="form-group"><label>تاريخ البداية</label><input type="date" id="cont_start"></div><div class="form-group"><label>تاريخ النهاية</label><input type="date" id="cont_end"></div></div>
    <div class="form-group"><label>المبلغ الإجمالي</label><input type="number" id="cont_amount" value="0"></div>`,
    `<button class="btn btn-primary" onclick="saveContract()">حفظ</button><button class="btn btn-outline" onclick="closeModal()">إلغاء</button>`);
}

async function saveContract() {
    const r = await api('/contracts', { method: 'POST', body: {
        contract_number: $('#cont_num').value, company_id: +$('#cont_co').value,
        start_date: $('#cont_start').value, end_date: $('#cont_end').value,
        total_amount: +$('#cont_amount').value,
    }});
    if (r && r.status === 'ok') { closeModal(); showAlert('تمت الإضافة'); loadContracts(); } else showAlert(r?.message || 'خطأ', 'error');
}

// ═══════════════════════════════════════════════════
// INVOICES
// ═══════════════════════════════════════════════════
async function loadInvoices() {
    const r = await api('/invoices');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>الفواتير</h2></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>رقم الفاتورة</th><th>الشركة</th><th>المبلغ</th><th>المدفوع</th><th>الحالة</th><th>التاريخ</th></tr></thead><tbody>
    ${r.data.map(i => `<tr><td>${i.invoice_number}</td><td>${i.company || '-'}</td><td>${(i.amount || 0).toLocaleString()}</td><td>${(i.paid_amount || 0).toLocaleString()}</td><td>${statusBadge(i.status || 'unpaid')}</td><td>${i.date || '-'}</td></tr>`).join('') || '<tr><td colspan="6" style="text-align:center;color:var(--text-secondary)">لا توجد فواتير</td></tr>'}</tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

// ═══════════════════════════════════════════════════
// SUPPLIERS
// ═══════════════════════════════════════════════════
async function loadSuppliers() {
    const r = await api('/suppliers');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>الموردون</h2><button class="btn btn-primary" onclick="showAddSupplier()">+ إضافة مورد</button></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>الاسم</th><th>الهاتف</th><th>البريد</th><th>إجراءات</th></tr></thead><tbody>
    ${r.data.map(s => `<tr><td>${s.name}</td><td>${s.phone || '-'}</td><td>${s.email || '-'}</td><td class="actions"><button class="btn btn-outline btn-sm" onclick="showEditSupplier(${s.id})">تعديل</button></td></tr>`).join('')}
    </tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

async function showAddSupplier() {
    openModal('إضافة مورد', `
    <div class="form-group"><label>اسم المورد</label><input id="sup_name" required></div>
    <div class="grid-2"><div class="form-group"><label>الهاتف</label><input id="sup_phone"></div><div class="form-group"><label>البريد</label><input id="sup_email" type="email"></div></div>`,
    `<button class="btn btn-primary" onclick="saveSupplier()">حفظ</button><button class="btn btn-outline" onclick="closeModal()">إلغاء</button>`);
}

async function saveSupplier() {
    const r = await api('/suppliers', { method: 'POST', body: { name: $('#sup_name').value, phone: $('#sup_phone').value, email: $('#sup_email').value }});
    if (r && r.status === 'ok') { closeModal(); showAlert('تمت الإضافة'); loadSuppliers(); } else showAlert(r?.message || 'خطأ', 'error');
}

async function showEditSupplier(id) {
    const list = await api('/suppliers');
    if (!list || list.status !== 'ok') return;
    const s = list.data.find(x => x.id === id);
    if (!s) return;
    openModal('تعديل مورد', `
    <div class="form-group"><label>اسم المورد</label><input id="sup_name" value="${s.name}"></div>
    <div class="grid-2"><div class="form-group"><label>الهاتف</label><input id="sup_phone" value="${s.phone || ''}"></div><div class="form-group"><label>البريد</label><input id="sup_email" value="${s.email || ''}" type="email"></div></div>`,
    `<button class="btn btn-primary" onclick="updateSupplier(${id})">تحديث</button><button class="btn btn-outline" onclick="closeModal()">إلغاء</button>`);
}

async function updateSupplier(id) {
    const r = await api(`/suppliers/${id}`, { method: 'PUT', body: { name: $('#sup_name').value, phone: $('#sup_phone').value, email: $('#sup_email').value }});
    if (r && r.status === 'ok') { closeModal(); showAlert('تم التحديث'); loadSuppliers(); } else showAlert(r?.message || 'خطأ', 'error');
}

// ═══════════════════════════════════════════════════
// SUPPLIER INVOICES
// ═══════════════════════════════════════════════════
async function loadSupplierInvoices() {
    const r = await api('/supplier-invoices');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>فواتير الموردين</h2></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>رقم الفاتورة</th><th>المورد</th><th>المبلغ</th><th>المدفوع</th><th>المتبقي</th><th>التاريخ</th></tr></thead><tbody>
    ${r.data.map(i => `<tr><td>${i.invoice_number}</td><td>${i.supplier || '-'}</td><td>${(i.amount || 0).toLocaleString()}</td><td>${(i.paid_amount || 0).toLocaleString()}</td><td>${(i.remaining_amount || 0).toLocaleString()}</td><td>${i.date || '-'}</td></tr>`).join('') || '<tr><td colspan="6" style="text-align:center;color:var(--text-secondary)">لا توجد فواتير</td></tr>'}</tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

// ═══════════════════════════════════════════════════
// ACCOUNTS
// ═══════════════════════════════════════════════════
async function loadAccounts() {
    const r = await api('/accounts');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>الحسابات</h2></div>
    <div class="stats-grid">
        <div class="stat-card"><div class="label">إجمالي الأصول</div><div class="value">${(r.data.total_assets || 0).toLocaleString()}</div></div>
        <div class="stat-card danger"><div class="label">إجمالي المصروفات</div><div class="value">${(r.data.total_expenses || 0).toLocaleString()}</div></div>
        <div class="stat-card success"><div class="label">إجمالي الإيرادات</div><div class="value">${(r.data.total_revenue || 0).toLocaleString()}</div></div>
        <div class="stat-card warning"><div class="label">صافي الدخل</div><div class="value">${(r.data.net_income || 0).toLocaleString()}</div></div>
    </div>
    <div class="card"><div class="card-header"><h3>دليل الحسابات</h3></div><div class="table-wrap"><table><thead><tr><th>الكود</th><th>الاسم</th><th>النوع</th><th>الرصيد</th></tr></thead><tbody>
    ${(r.data.accounts || []).map(a => `<tr><td>${a.code}</td><td>${a.name}</td><td>${a.type}</td><td>${(a.balance || 0).toLocaleString()}</td></tr>`).join('') || '<tr><td colspan="4" style="text-align:center">لا توجد حسابات</td></tr>'}</tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

// ═══════════════════════════════════════════════════
// JOURNAL
// ═══════════════════════════════════════════════════
async function loadJournal() {
    const r = await api('/accounts/journal');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>القيود اليومية</h2></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>رقم القيد</th><th>التاريخ</th><th>الوصف</th><th>المدين</th><th>الدائن</th></tr></thead><tbody>
    ${r.data.map(e => `<tr><td>${e.entry_number}</td><td>${e.date || '-'}</td><td>${e.description || '-'}</td><td>${(e.total_debit || 0).toLocaleString()}</td><td>${(e.total_credit || 0).toLocaleString()}</td></tr>`).join('') || '<tr><td colspan="5" style="text-align:center;color:var(--text-secondary)">لا توجد قيود</td></tr>'}</tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

// ═══════════════════════════════════════════════════
// LOANS / PENALTIES / OVERTIME
// ═══════════════════════════════════════════════════
async function loadLoans() {
    const r = await api('/loans');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>القروض</h2></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>رقم الموظف</th><th>المبلغ</th><th>التاريخ</th><th>الوصف</th><th>الحالة</th></tr></thead><tbody>
    ${r.data.map(l => `<tr><td>${l.employee_id}</td><td>${(l.amount || 0).toLocaleString()}</td><td>${l.date || '-'}</td><td>${l.description || '-'}</td><td>${statusBadge(l.is_settled ? 'paid' : 'unpaid')}</td></tr>`).join('') || '<tr><td colspan="5" style="text-align:center;color:var(--text-secondary)">لا توجد قروض</td></tr>'}</tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

async function loadPenalties() {
    const r = await api('/penalties');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>الخصومات</h2></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>رقم الموظف</th><th>المبلغ</th><th>التاريخ</th><th>الوصف</th><th>الحالة</th></tr></thead><tbody>
    ${r.data.map(p => `<tr><td>${p.employee_id}</td><td>${(p.amount || 0).toLocaleString()}</td><td>${p.date || '-'}</td><td>${p.description || '-'}</td><td>${statusBadge(p.is_settled ? 'paid' : 'unpaid')}</td></tr>`).join('') || '<tr><td colspan="5" style="text-align:center;color:var(--text-secondary)">لا توجد خصومات</td></tr>'}</tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

async function loadOvertime() {
    const r = await api('/overtime');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>العمل الإضافي</h2></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>رقم الموظف</th><th>المبلغ</th><th>التاريخ</th><th>الوصف</th></tr></thead><tbody>
    ${r.data.map(o => `<tr><td>${o.employee_id}</td><td>${(o.amount || 0).toLocaleString()}</td><td>${o.date || '-'}</td><td>${o.description || '-'}</td></tr>`).join('') || '<tr><td colspan="4" style="text-align:center;color:var(--text-secondary)">لا يوجد عمل إضافي</td></tr>'}</tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

// ═══════════════════════════════════════════════════
// USERS
// ═══════════════════════════════════════════════════
async function loadUsers() {
    const r = await api('/users');
    if (!r || r.status !== 'ok') return;
    let html = `<div class="page-header"><h2>المستخدمون</h2><button class="btn btn-primary" onclick="showAddUser()">+ إضافة مستخدم</button></div>
    <div class="card"><div class="table-wrap"><table><thead><tr><th>اسم المستخدم</th><th>البريد</th><th>الدور</th><th>الحالة</th><th>إجراءات</th></tr></thead><tbody>
    ${r.data.map(u => `<tr><td>${u.username}</td><td>${u.email || '-'}</td><td>${u.role}</td><td>${statusBadge(u.is_active ? 'active' : 'inactive')}</td>
    <td class="actions"><button class="btn btn-outline btn-sm" onclick="showEditUser(${u.id})">تعديل</button><button class="btn btn-warning btn-sm" onclick="toggleUser(${u.id})">toggle</button><button class="btn btn-danger btn-sm" onclick="deleteUser(${u.id})">حذف</button></td></tr>`).join('')}
    </tbody></table></div></div>`;
    $('#pageContent').innerHTML = html;
}

async function showAddUser() {
    openModal('إضافة مستخدم', `
    <div class="form-group"><label>اسم المستخدم</label><input id="user_name" required></div>
    <div class="form-group"><label>البريد</label><input id="user_email" type="email"></div>
    <div class="form-group"><label>كلمة المرور</label><input id="user_pass" type="password" required></div>
    <div class="form-group"><label>الدور</label><select id="user_role"><option value="worker">عامل</option><option value="supervisor">مشرف</option><option value="owner">مالك</option></select></div>`,
    `<button class="btn btn-primary" onclick="saveUser()">حفظ</button><button class="btn btn-outline" onclick="closeModal()">إلغاء</button>`);
}

async function saveUser() {
    const r = await api('/users', { method: 'POST', body: {
        username: $('#user_name').value, email: $('#user_email').value,
        password: $('#user_pass').value, role: $('#user_role').value,
    }});
    if (r && r.status === 'ok') { closeModal(); showAlert('تمت الإضافة'); loadUsers(); } else showAlert(r?.message || 'خطأ', 'error');
}

async function showEditUser(id) {
    const list = await api('/users');
    if (!list || list.status !== 'ok') return;
    const u = list.data.find(x => x.id === id);
    if (!u) return;
    openModal('تعديل مستخدم', `
    <div class="form-group"><label>اسم المستخدم</label><input value="${u.username}" disabled></div>
    <div class="form-group"><label>البريد</label><input id="user_email" value="${u.email || ''}"></div>
    <div class="form-group"><label>كلمة المرور الجديدة (اترك فارغ)</label><input id="user_pass" type="password"></div>
    <div class="form-group"><label>الدور</label><select id="user_role"><option value="worker" ${u.role==='worker'?'selected':''}>عامل</option><option value="supervisor" ${u.role==='supervisor'?'selected':''}>مشرف</option><option value="owner" ${u.role==='owner'?'selected':''}>مالك</option></select></div>`,
    `<button class="btn btn-primary" onclick="updateUser(${id})">تحديث</button><button class="btn btn-outline" onclick="closeModal()">إلغاء</button>`);
}

async function updateUser(id) {
    const body = { email: $('#user_email').value, role: $('#user_role').value };
    const pass = $('#user_pass').value;
    if (pass) body.password = pass;
    const r = await api(`/users/${id}`, { method: 'PUT', body });
    if (r && r.status === 'ok') { closeModal(); showAlert('تم التحديث'); loadUsers(); } else showAlert(r?.message || 'خطأ', 'error');
}

async function toggleUser(id) {
    const r = await api(`/users/${id}/toggle`, { method: 'POST' });
    if (r && r.status === 'ok') { showAlert('تم التغيير'); loadUsers(); }
}

async function deleteUser(id) {
    if (!confirm('هل تريد حذف هذا المستخدم؟')) return;
    const r = await api(`/users/${id}`, { method: 'DELETE' });
    if (r && r.status === 'ok') { showAlert('تم الحذف'); loadUsers(); } else showAlert(r?.message || 'خطأ', 'error');
}

// ═══════════════════════════════════════════════════
// REPORTS
// ═══════════════════════════════════════════════════
async function loadReports() {
    const [overview, att, evals, salary, top] = await Promise.all([
        api('/reports'), api('/reports/attendance-record'), api('/reports/daily-evaluations'),
        api('/reports/salary-report'), api('/reports/top-employees'),
    ]);
    let html = `<div class="page-header"><h2>التقارير</h2></div>`;

    if (overview && overview.status === 'ok') {
        const d = overview.data;
        html += `<div class="stats-grid">
            <div class="stat-card"><div class="label">إجمالي الموظفين</div><div class="value">${d.total_employees}</div></div>
            <div class="stat-card success"><div class="label">الموظفون النشطون</div><div class="value">${d.active_employees}</div></div>
            <div class="stat-card warning"><div class="label">الشركات</div><div class="value">${d.total_companies}</div></div>
            <div class="stat-card"><div class="label">المناطق</div><div class="value">${d.total_areas}</div></div>
            <div class="stat-card success"><div class="label">إجمالي التقييمات</div><div class="value">${d.total_evaluations}</div></div>
            <div class="stat-card"><div class="label">متوسط التقييم</div><div class="value ${scoreClass(d.avg_score)}">${d.avg_score}%</div></div>
        </div>`;
    }

    html += `<div class="grid-2">`;

    if (att && att.status === 'ok') {
        const a = att.data;
        html += `<div class="card"><div class="card-header"><h3>تقرير الحضور الشهري</h3></div>
            <div class="stats-grid"><div class="stat-card success"><div class="label">حاضر</div><div class="value">${a.present}</div></div>
            <div class="stat-card danger"><div class="label">غائب</div><div class="value">${a.absent}</div></div>
            <div class="stat-card warning"><div class="label">متأخر</div><div class="value">${a.late}</div></div>
            <div class="stat-card"><div class="label">نسبة الحضور</div><div class="value">${a.rate}%</div></div></div></div>`;
    }

    if (evals && evals.status === 'ok') {
        const e = evals.data;
        html += `<div class="card"><div class="card-header"><h3>تقييمات اليوم</h3></div>
            <div class="stats-grid"><div class="stat-card"><div class="label">عدد التقييمات</div><div class="value">${e.total}</div></div>
            <div class="stat-card"><div class="label">متوسط الدرجة</div><div class="value ${scoreClass(e.avg_score)}">${e.avg_score}%</div></div></div></div>`;
    }

    html += `</div><div class="grid-2">`;

    if (salary && salary.status === 'ok') {
        const s = salary.data;
        html += `<div class="card"><div class="card-header"><h3>تقرير الرواتب</h3></div>
            <div class="stats-grid"><div class="stat-card"><div class="label">الموظفون</div><div class="value">${s.total_employees}</div></div>
            <div class="stat-card warning"><div class="label">إجمالي الرواتب</div><div class="value">${s.total_salaries.toLocaleString()}</div></div>
            <div class="stat-card"><div class="label">متوسط الراتب</div><div class="value">${s.avg_salary.toLocaleString()}</div></div></div></div>`;
    }

    if (top && top.status === 'ok' && top.data.length) {
        html += `<div class="card"><div class="card-header"><h3>أفضل الموظفين</h3></div><div class="table-wrap"><table><thead><tr><th>#</th><th>الاسم</th><th>متوسط التقييم</th></tr></thead><tbody>
            ${top.data.map((t, i) => `<tr><td>${i+1}</td><td>${t.name}</td><td>${scoreBadge(t.avg_score)}</td></tr>`).join('')}
        </tbody></table></div></div>`;
    }

    html += `</div>`;
    $('#pageContent').innerHTML = html;
}

// ═══════════════════════════════════════════════════
// SETTINGS
// ═══════════════════════════════════════════════════
async function loadSettings() {
    const r = await api('/profile');
    const s = await api('/settings');
    let html = `<div class="page-header"><h2>الإعدادات</h2></div>
    <div class="grid-2">
        <div class="card"><div class="card-header"><h3>الملف الشخصي</h3></div>
            <p><strong>اسم المستخدم:</strong> ${r?.data?.username || '-'}</p>
            <p><strong>البريد:</strong> ${r?.data?.email || '-'}</p>
            <p><strong>الدور:</strong> ${r?.data?.role || '-'}</p></div>
        <div class="card"><div class="card-header"><h3>معلومات التطبيق</h3></div>
            <p><strong>اسم التطبيق:</strong> ${s?.data?.app_name || '-'}</p>
            <p><strong>الإصدار:</strong> ${s?.data?.version || '-'}</p></div>
    </div>`;
    $('#pageContent').innerHTML = html;
}

// ═══════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════
(async function init() {
    const r = await api('/profile');
    if (r && r.status === 'ok') {
        $('#userDisplay').textContent = r.data.username;
        navigate('dashboard');
    } else {
        $('#loginPage').style.display = 'flex';
    }
})();
