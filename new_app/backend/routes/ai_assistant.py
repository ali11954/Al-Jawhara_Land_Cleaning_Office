import os
import json
from flask import Blueprint, request, jsonify
from auth import token_required
from db import get_db, fetch_all, fetch_one
from datetime import datetime, timedelta

ai_bp = Blueprint('ai', __name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')


def _call_gemini(prompt, system_instruction=''):
    if not GEMINI_API_KEY:
        return None, 'GEMINI_API_KEY not configured'
    import urllib.request
    import urllib.error

    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}'

    contents = []
    if system_instruction:
        contents.append({'role': 'user', 'parts': [{'text': system_instruction}]})
        contents.append({'role': 'model', 'parts': [{'text': 'حسناً، أنا جاهز للمساعدة.'}]})
    contents.append({'role': 'user', 'parts': [{'text': prompt}]})

    data = json.dumps({
        'contents': contents,
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 2048,
        }
    }).encode('utf-8')

    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            text = result['candidates'][0]['content']['parts'][0]['text']
            return text, None
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')
        return None, f'Gemini API error {e.code}: {body[:300]}'
    except Exception as e:
        return None, str(e)


def _get_employee_stats():
    with get_db() as conn:
        employees = fetch_all(conn, """SELECT id, full_name, position, company_id, is_active, region,
            salary, hire_date FROM employees ORDER BY full_name""")
        companies = fetch_all(conn, "SELECT id, name FROM clean_companies ORDER BY name")
        company_map = {c['id']: c['name'] for c in (companies or [])}
    return employees, company_map


def _get_attendance_stats(days=30):
    with get_db() as conn:
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        records = fetch_all(conn, """SELECT a.*, e.full_name, e.company_id
            FROM attendance a JOIN employees e ON a.employee_id = e.id
            WHERE a.date >= %s ORDER BY a.date DESC""", (since,))
    return records or []


def _get_evaluation_stats():
    with get_db() as conn:
        evals = fetch_all(conn, """SELECT ev.*, e.full_name
            FROM evaluations ev JOIN employees e ON ev.employee_id = e.id
            ORDER BY ev.date DESC LIMIT 200""")
    return evals or []


def _get_financial_stats():
    with get_db() as conn:
        transactions = fetch_all(conn, """SELECT * FROM financial_transactions
            ORDER BY created_at DESC LIMIT 200""")
        salaries = fetch_all(conn, """SELECT s.*, e.full_name
            FROM salaries s JOIN employees e ON s.employee_id = e.id
            ORDER BY s.created_at DESC LIMIT 100""")
    return transactions or [], salaries or []


@ai_bp.route('/api/ai/chat', methods=['POST'])
@token_required
def ai_chat(current_user):
    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'success': False, 'message': 'الرسالة مطلوبة'}), 400

    employees, company_map = _get_employee_stats()
    active_count = sum(1 for e in employees if e.get('is_active'))
    inactive_count = len(employees) - active_count

    companies_summary = {}
    for e in employees:
        cname = company_map.get(e.get('company_id'), 'بدون شركة')
        if cname not in companies_summary:
            companies_summary[cname] = {'active': 0, 'inactive': 0}
        if e.get('is_active'):
            companies_summary[cname]['active'] += 1
        else:
            companies_summary[cname]['inactive'] += 1

    system_instruction = f"""أنت مساعد ذكي لنظام إدارة شركة "أرض الجوهرة لخدمات النظافة".
الوقت الحالي: {datetime.now().strftime('%Y-%m-%d %H:%M')}

معلومات الشركة:
- إجمالي الموظفين: {len(employees)} ({active_count} نشط، {inactive_count} غير نشط)
- الشركات: {json.dumps(companies_summary, ensure_ascii=False)}

قواعد:
- أجب بالعربية دائماً
- كن مختصراً ومفيداً
- لا تختلق معلومات غير موجودة"""

    reply, error = _call_gemini(user_message, system_instruction)
    if error:
        return jsonify({'success': False, 'message': error}), 500

    return jsonify({'success': True, 'data': {'reply': reply}})


@ai_bp.route('/api/ai/report-analysis', methods=['POST'])
@token_required
def report_analysis(current_user):
    data = request.get_json()
    report_type = data.get('type', 'general')

    employees, company_map = _get_employee_stats()
    attendance = _get_attendance_stats(30)
    evaluations = _get_evaluation_stats()
    transactions, salaries = _get_financial_stats()

    context_parts = []

    if report_type in ('general', 'employees'):
        active = [e for e in employees if e.get('is_active')]
        by_company = {}
        for e in active:
            cn = company_map.get(e.get('company_id'), 'بدون شركة')
            by_company.setdefault(cn, []).append(e)
        context_parts.append(f"الموظفون النشطون: {len(active)}")
        for cn, emps in by_company.items():
            context_parts.append(f"  {cn}: {len(emps)} موظف")

    if report_type in ('general', 'attendance'):
        present = sum(1 for r in attendance if r.get('attendance_status') == 'present')
        late = sum(1 for r in attendance if r.get('attendance_status') == 'late')
        absent = sum(1 for r in attendance if r.get('attendance_status') == 'absent')
        total = len(attendance)
        rate = round((present + late) / total * 100, 1) if total else 0
        context_parts.append(f"\nالحضور (آخر 30 يوم): إجمالي {total} سجل")
        context_parts.append(f"  حاضر: {present}, متأخر: {late}, غائب: {absent}")
        context_parts.append(f"  نسبة الحضور: {rate}%")
        absence_by_emp = {}
        for r in attendance:
            if r.get('attendance_status') in ('absent',):
                name = r.get('full_name', '?')
                absence_by_emp[name] = absence_by_emp.get(name, 0) + 1
        if absence_by_emp:
            sorted_abs = sorted(absence_by_emp.items(), key=lambda x: -x[1])[:10]
            context_parts.append("  أكثر الغيابات:")
            for name, count in sorted_abs:
                context_parts.append(f"    {name}: {count} مرة")

    if report_type in ('general', 'evaluations') and evaluations:
        scores = [e.get('score', 0) for e in evaluations if e.get('score')]
        if scores:
            avg = sum(scores) / len(scores)
            context_parts.append(f"\nالتقييمات: {len(evaluations)} تقييم، متوسط {avg:.1f}")

    if report_type in ('general', 'financial') and salaries:
        total_sal = sum(float(s.get('total_salary', 0) or 0) for s in salaries)
        context_parts.append(f"\nالرواتب: إجمالي {total_sal:,.0f} ريال لـ {len(salaries)} موظف")

    context = '\n'.join(context_parts) if context_parts else 'لا توجد بيانات كافية'

    system_instruction = f"""أنت محلل بيانات ذكي لشركة "أرض الجوهرة لخدمات النظافة".
حلل البيانات التالية وقدم توصيات عملية بالعربية.

قدم تحليلاً يتضمن:
1. ملخص الوضع الحالي
2. نقاط القوة
3. نقاط تحتاج تحسين
4. توصيات عملية
كن مختصراً ومحدداً."""

    prompt = f"""البيانات:
{context}

قم بتحليل البيانات وأعطني تقريراً شاملاً مع التوصيات."""

    reply, error = _call_gemini(prompt, system_instruction)
    if error:
        return jsonify({'success': False, 'message': error}), 500

    return jsonify({'success': True, 'data': {'analysis': reply, 'context': context}})


@ai_bp.route('/api/ai/attendance-prediction', methods=['POST'])
@token_required
def attendance_prediction(current_user):
    attendance = _get_attendance_stats(90)

    emp_absences = {}
    emp_total = {}
    for r in attendance:
        name = r.get('full_name', '?')
        emp_total[name] = emp_total.get(name, 0) + 1
        if r.get('attendance_status') in ('absent', 'sick'):
            emp_absences[name] = emp_absences.get(name, 0) + 1

    emp_data = []
    for name in emp_absences:
        total = emp_total.get(name, 1)
        rate = emp_absences[name] / total
        emp_data.append(f"{name}: غياب {emp_absences[name]} من {total} ({rate*100:.0f}%)")

    context = '\n'.join(emp_data[:30]) if emp_data else 'لا توجد بيانات غياب كافية'

    system_instruction = """أنت محلل غياب ذكي لشركة نظافة.
حلل الأنماط وتوقّع:
1. الموظفون المعرضون للغياب المتكرر
2. أيام الأسبوع الأكثر غياباً
3. توصيات لتقليل الغياب
قدم تحليلاً مختصراً بالعربية."""

    prompt = f"""بيانات الغياب لل员工 последние 90 يوم:
{context}

حلل أنماط الغياب وتنبأ بالغياب المحتمل."""

    reply, error = _call_gemini(prompt, system_instruction)
    if error:
        return jsonify({'success': False, 'message': error}), 500

    return jsonify({'success': True, 'data': {'prediction': reply}})


@ai_bp.route('/api/ai/evaluation-review', methods=['POST'])
@token_required
def evaluation_review(current_user):
    data = request.get_json()
    employee_id = data.get('employee_id')

    with get_db() as conn:
        if employee_id:
            emp = fetch_one(conn, "SELECT * FROM employees WHERE id=%s", (employee_id,))
            evals = fetch_all(conn, """SELECT * FROM evaluations WHERE employee_id=%s
                ORDER BY date DESC LIMIT 20""", (employee_id,))
            attendance = fetch_all(conn, """SELECT * FROM attendance WHERE employee_id=%s
                AND date >= %s ORDER BY date DESC""",
                (employee_id, (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')))
        else:
            emp = None
            evals = fetch_all(conn, """SELECT * FROM evaluations ORDER BY date DESC LIMIT 100""")
            attendance = fetch_all(conn, """SELECT * FROM attendance WHERE date >= %s ORDER BY date DESC""",
                ((datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),))

    evals = evals or []
    attendance = attendance or []

    emp_name = emp.get('full_name', 'جميع الموظفين') if emp else 'جميع الموظفين'
    scores = [e.get('score', 0) for e in evals if e.get('score')]
    avg_score = sum(scores) / len(scores) if scores else 0
    present = sum(1 for a in attendance if a.get('attendance_status') == 'present')
    late = sum(1 for a in attendance if a.get('attendance_status') == 'late')
    absent = sum(1 for a in attendance if a.get('attendance_status') in ('absent', 'sick'))
    total_att = len(attendance)

    context = f"""الموظف: {emp_name}
عدد التقييمات: {len(evals)}
متوسط التقييم: {avg_score:.1f}
الحضور: {present} حاضر، {late} متأخر، {absent} غائب من {total_att}"""

    system_instruction = """أنت خبير موارد بشرية لشركة نظافة.
اكتب ملخص تقييم أداء احترافي يتضمن:
1. تقييم عام للأداء
2. نقاط القوة
3. نقاط تحتاج تحسين
4. توصيات للتطوير
اكتب بالعربية بأسلوب رسمي احترافي."""

    prompt = f"""بيانات الموظف:
{context}

اكتب ملخص تقييم أداء احترافي."""

    reply, error = _call_gemini(prompt, system_instruction)
    if error:
        return jsonify({'success': False, 'message': error}), 500

    return jsonify({'success': True, 'data': {'review': reply, 'employee': emp_name,
        'avg_score': round(avg_score, 1), 'attendance_rate': round((present + late) / total_att * 100, 1) if total_att else 0}})


@ai_bp.route('/api/ai/financial-anomaly', methods=['POST'])
@token_required
def financial_anomaly(current_user):
    transactions, salaries = _get_financial_stats()

    tx_lines = []
    for t in transactions[:30]:
        tx_lines.append(f"{t.get('transaction_type','?')}: {t.get('amount',0)} - {t.get('description','')[:40]}")

    sal_lines = []
    for s in salaries[:20]:
        sal_lines.append(f"{s.get('full_name','?')}: راتب {s.get('total_salary',0)} / أساسي {s.get('base_salary',0)}")

    context = f"""المعاملات المالية الأخيرة ({len(transactions)} معاملة):
{chr(10).join(tx_lines)}

الرواتب الأخيرة ({len(salaries)} راتب):
{chr(10).join(sal_lines)}"""

    system_instruction = """أنت محلل مالي ذكي لشركة نظافة.
فحص المعاملات المالية وأكتشف الشذوذ:
1. مبالغ غير طبيعية
2. أنماط مشبوهة
3. معاملات مكررة محتملة
4. توصيات للتحسين
قدم تقريراً مختصراً بالعربية."""

    prompt = f"""{context}

افحص المعاملات واكتشف أي شذوذ مالي."""

    reply, error = _call_gemini(prompt, system_instruction)
    if error:
        return jsonify({'success': False, 'message': error}), 500

    return jsonify({'success': True, 'data': {'report': reply}})
