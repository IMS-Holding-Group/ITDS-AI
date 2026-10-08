# ITDS-AI — نظام ذكي لتوزيع المهام

## 1. نظرة عامة على المشروع

**ITDS-AI** (Intelligent Task Distribution System) هو نظام ويب محلي يهدف إلى مساعدة المدراء على إنشاء المهام، وتقييم أنسب الموظفين لتنفيذها باستخدام قواعد رياضية واضحة (محاكاة قرار ذكي داخل الخادم)، ومتابعة الإرهاق الوظيفي للفريق.

**لماذا يُبنى هذا النظام؟** في فرق العمل الحقيقية، توزيع المهام يعتمد غالباً على الحدس أو على الحمل الظاهر فقط. هذا المشروع يجمع بين **بيانات الموظف** (مهارات، أداء، سرعة، حمل حالي) وبيانات المهمة (مهارات مطلوبة، أولوية، وقت) ليقترح توزيعاً أكثر عدالة مع تنبيهات عند ارتفاع خطر الإرهاق.

**لمن هذا المشروع؟** لطلاب هندسة البرمجيات وتطبيقات الويب الذين يحتاجون مشروع تخرج يغطي: واجهة أمامية بسيطة، خلفية Flask، SQLite، جلسات وصلاحيات، ووحدة «ذكاء» داخلية بدون مكتبات تعلم معقدة.

**Flask** (إطار عمل ويب خفيف لـ Python — يوفّر التوجيه، القوالب، والجلسات دون الحاجة لإعداد ضخم مثل الأطر الكاملة).

---

## 2. ما هو «الذكاء الاصطناعي» المستخدم هنا؟

في هذا المشروع لا يوجد نموذج تعلم عميق خارجي. يوجد **محرك قرار قابل للشرح**: دوال Python تحسب **درجة مطابقة** بين الموظف والمهمة، و**مؤشر إرهاق** من حمل العمل وسجل التأخر، و**تحليلات** للتقارير.

**مثال واقعي للمطابقة:** مهمة تحتاج `Python` و`Flask` و`SQL`؛ الموظف ألف يمتلك هذه المهارات الثلاث بدرجة تطابق عالية، بينما الموظف باء يمتلك مهارتين فقط — فيُفضّل ألف حتى لو كان الحمل لديه أعلى قليلاً، ضمن معادلة توازن بين المهارات والأداء والتوفر والسرعة.

**مثال واقعي للإرهاق:** موظف لديه 5 مهام نشطة من أصل 5 مسموح، وأخر مهامه كانت تتجاوز وقت التقدير بنسبة كبيرة — يرتفع مؤشر الخطر ويُرسل تنبيه للمدير.

---

## 3. متطلبات التشغيل

| المكوّن | ملاحظات |
|---------|---------|
| **Python** | إصدار 3.10 أو أحدث موصى به |
| **pip** | لإدارة الحزم (`pip install -r requirements.txt`) |
| **متصفح حديث** | Chrome / Edge / Firefox لعرض الواجهة والطباعة |

**SQLite** (محرك قاعدة بيانات مدمج مع Python — ملف واحد `itds.db` يشبه دفتراً منظماً من الجداول، يقرأه التطبيق عبر مكتبة `sqlite3` المدمجة).

---

## 4. خطوات التثبيت والتشغيل

1. افتح موجه الأوامر (Command Prompt) من قائمة ابدأ  
2. انتقل للمجلد: `cd D:\VSCode\Projects\ITDS-AI`  
3. ثبّت المتطلبات: `pip install -r requirements.txt`  
4. أنشئ قاعدة البيانات وعبّئها بالبيانات: `python database.py`  
5. شغّل الخادم: `python app.py`  
6. افتح المتصفح على: `http://127.0.0.1:5000`  
7. سجّل دخولاً بالحساب: `ahmed@itds.com` / ``  

**ملاحظة:** عند أول تشغيل لـ `python app.py` يتم أيضاً استدعاء تهيئة الجداول والبذور إن لزم الأمر عبر `init_database()` في `app.py`.

---

## 5. هيكل المجلدات والملفات

```
ITDS-AI/
├── app.py                 # إنشاء التطبيق وتسجيل المسارات
├── config.py              # المسارات والمفتاح السري
├── database.py            # الجداول، التهيئة، البيانات الافتراضية، كلمات المرور
├── decorators.py          # حماية الصفحات وواجهات JSON
├── requirements.txt       # Flask و Gunicorn (محليًا وعلى Render)
├── render.yaml            # تعريف النشر على Render
├── README.md              # هذا الملف
├── models/                # تمثيل الكائنات (User, Employee, AdminProfile, Task)
├── routes/                # auth, admin_routes, employee_routes, api
├── ai_engine/             # matcher, burnout_detector, analyzer
├── static/
│   ├── css/               # base, components, auth, admin, employee
│   ├── js/                # main, charts, admin_dashboard, employee_dashboard, notifications
│   └── assets/fonts/      # خط IBM Plex Sans Arabic (ملفات .ttf)
└── templates/             # قوالب HTML (base + admin + employee + auth)
```

- **`static/`**: ملفات الواجهة الثابتة يخدمها Flask من المسار `/static/...`.  
- **`templates/`**: قوالب Jinja2 التي يعرضها `render_template`.  
- **`routes/api.py`**: جميع المسارات تحت `/api/...` تُرجع **JSON** للاستخدام من JavaScript.

---

## 6. شرح قاعدة البيانات

### الجداول والعلاقات

1. **`users`** — كل حساب (مدير أو موظف): الاسم، البريد، كلمة المرور المختومة، الدور.  
2. **`employees`** — صف إضافي للموظف مرتبط بـ `user_id` فريد: القسم، المهارات (JSON كنص)، درجات الأداء والسرعة، الحمل، الإرهاق، التوفر.  
3. **`tasks`** — المهام مع الحالة والأولوية والمهارات المطلوبة والمواعيد والتعيين وحقول ناتجة عن المحرك (`ai_match_score`, `ai_notes`).  
4. **`notifications`** — إشعارات لكل مستخدم (تعيين، إكمال، إرهاق عالٍ، إلخ).  
5. **`performance_logs`** — سجل إنجاز بعد إكمال المهمة لاستخدام التحليلات ومؤشر الإرهاق.

**العلاقات:** `employees.user_id → users.id`، `tasks.assigned_to → employees.id`، `tasks.created_by → users.id`، الإشعارات والسجلات تشير إلى الموظف أو المستخدم أو المهمة حسب العمود.

**JSON في SQLite:** عمود `skills` أو `required_skills` يُخزَّن كنص JSON مثل `["Python","Flask"]` لسهولة القراءة من الخوارزميات.

---

## 7. شرح محرك الذكاء الاصطناعي (الخوارزميات)

### أ) مطابقة المهام — `ai_engine/matcher.py`

**الفكرة:** لكل موظف متاح نحسب:

`score = skill_match×0.40 + performance×0.30 + availability×0.20 + speed×0.10`

- **`skill_match`**: نسبة المهارات المطلوبة التي يمتلكها الموظف (0–100).  
- **`performance`**: `performance_score` من الجدول.  
- **`availability`**: `(1 - current_workload/max_workload)×100`.  
- **`speed`**: `speed_score`.

**مقتطف مبسّط مع شرح الأسطر (عربي):**

```python
def find_best_match(conn, task_row):
    required = _parse_skills(task_row["required_skills"])  # تحويل المهارات المطلوبة إلى قائمة نصية نظيفة
    rows = conn.execute("SELECT e.*, u.name AS emp_name FROM employees e JOIN users u ...").fetchall()
    scored = []
    for row in rows:
        emp_skills = _parse_skills(row["skills"])              # مهارات الموظف من JSON
        sm = _skill_match_percent(required, emp_skills)       # نسبة التطابق 0–100
        perf = float(row["performance_score"] or 0)          # درجة الأداء المخزنة
        mx = max(int(row["max_workload"] or 1), 1)           # تجنب القسمة على صفر
        cur = int(row["current_workload"] or 0)
        availability = (1 - min(1.0, cur / mx)) * 100.0      # كلما زاد الحمل قل التوفر
        spd = float(row["speed_score"] or 0)
        total = sm * 0.40 + perf * 0.30 + availability * 0.20 + spd * 0.10  # الجمع المرجّح
        scored.append({...})
    scored.sort(key=lambda x: x["score"], reverse=True)       # ترتيب تنازلي
    return scored[:3]                                         # أفضل ثلاثة موظفين
```

### ب) كاشف الإرهاق — `ai_engine/burnout_detector.py`

`burnout_risk = workload_ratio×0.50 + overtime_factor×0.30 + performance_drop×0.20`

- **`workload_ratio`**: `current_workload / max_workload` (بحد أقصى 1).  
- **`overtime_factor`**: إن وُجدت مهمة مكتملة ضمن آخر 3 مهام بحيث `actual_hours > estimated_hours×1.2` يصبح العامل 1 وإلا 0.  
- **`performance_drop`**: إن انخفضت درجات سجل الأداء ضمن آخر 30 يوماً أكثر من 10 نقاط بين أقدم وأحدث سجل يصبح 1 وإلا 0.

**المستويات:** ≤0.3 آمن، 0.3–0.6 تحذير، >0.6 خطر مع إشعار للمدير (مع منع التكرار ضمن نافذة زمنية قصيرة في الكود).

### ج) محلل البيانات — `ai_engine/analyzer.py`

يجمع إحصاءات الفترة المحددة (أسبوع/شهر/ربع): متوسط أداء الموظفين من `performance_logs`، معدل الإنجاز في الموعد، توزيع المهام حسب الأولوية والحالة، وتقرير الإرهاق اعتماداً على القيم المخزنة في `employees`.

---

## 8. شرح واجهات الـ API (JSON)

| الطلب | المسار | الوصف |
|--------|--------|--------|
| GET | `/api/tasks/stats` | إحصاءات المهام (للمدير: إضافة عدد المتاحين؛ للموظف: مهامه فقط) |
| GET | `/api/employees/stats` | أداء وحمل الموظفين (مدير فقط) |
| GET | `/api/ai/match/<task_id>` | إعادة حساب أفضل 3 موظفين لمهمة موجودة |
| GET | `/api/ai/burnout` | تحديث مخاطر الإرهاق وإرجاع القائمة (مدير) |
| GET | `/api/reports/summary?range=week|month|quarter` | بيانات التقارير للرسوم (مدير) |
| GET | `/api/notifications` | إشعارات المستخدم الحالي + عدد غير المقروء |
| POST | `/api/notifications/read/<id>` | تعيين إشعار كمقروء |
| GET | `/api/dashboard/recent-tasks` | آخر 5 مهام للوحة المدير |
| GET | `/api/dashboard/burnout-alerts` | موظفون بخطر > 0.6 |
| GET | `/api/employee/summary` | لوحة الموظف (بطاقات، عاجل، نشاط) |

**مثال استجابة تسجيل الدخول (POST `/login` مع JSON):**

```json
{"success": true, "redirect": "/admin/dashboard"}
```

---

## 9. شرح النماذج (Models)

| الملف | الغرض | أهم الحقول والدوال |
|-------|--------|---------------------|
| `user.py` | تمييز نوع المستخدم | `User`، `Admin`، `EmployeeUser` مع `dashboard_path()` و`from_row()` لتحويل صف SQLite إلى كائن. |
| `employee.py` | تمثيل الموظف مع الحقول التشغيلية | `Employee.from_join_row()` لربط صف يضم أعمدة الموظف والاسم. |
| `admin.py` | ملخص بيانات المدير | `AdminProfile.from_row()` للعرض البسيط. |
| `task.py` | مهمة مع اسم المعين الاختياري | `Task.from_row()` لقراءة صف المهام. |

---

## 10. دوال Python الرئيسية (ملخص)

| الدالة | الملف | دورها |
|--------|-------|--------|
| `init_database` | `database.py` | إنشاء الجداول، البذور عند الحاجة، ثم تحديث الإرهاق عبر `detect_burnout`. |
| `hash_password` / `verify_password` | `database.py` | تخزين كلمة المرور باستخدام **SHA-256** مع **salt** عشوائي (`hashlib` و`secrets`). |
| `sync_employee_workloads` | `database.py` | إعادة حساب الحمل بناءً على المهام النشطة. |
| `tasks_create` | `admin_routes.py` | إنشاء مهمة وتشغيل `find_best_match` وتخزين النتائج في `ai_notes`. |
| `tasks_assign` / `tasks_status` | `admin_routes.py` | تعيين الموظف، تغيير الحالة، إنشاء سجل أداء عند الإكمال، إشعارات. |
| `task_start` / `task_finish` | `employee_routes.py` | انتقال الحالة من `assigned` إلى `in_progress` ثم `in_review`. |

---

## 11. دليل استخدام النظام (وصف نصي للواجهات)

### المدير

1. **تسجيل الدخول:** صفحة مقسومة — جانب أزرق بتخطيط SVG، نموذج أبيض مع إظهار/إخفاء كلمة المرور وزر تحميل.  
2. **اللوحة:** بطاقات إحصاء، جديد المهام، بطاقات تنبيه إرهاق عالٍ، ورسم أعمدة لأداء الفريق.  
3. **المهام:** زر إضافة مهمة يفتح نافذة؛ بعد الحفظ تظهر أفضل 3 موظفين مع زر تعيين؛ الجدول يدعم الفلاتر وتعديل الحالة والتعيين اليدوي.  
4. **الموظفون:** جدول مع شريط حمل وتحذير ⚠️ عند `burnout_risk > 0.6`؛ إضافة موظف بكلمة مرور افتراضية ``.  
5. **التقارير:** فلاتر أسبوع/شهر/3 أشهر، خط بياني للمهام المكتملة، دائرة أولويات SVG، أعمدة للأداء، شرائط إرهاق، زر طباعة المتصفح.

### الموظف

1. **اللوحة:** تحية بالاسم تُحمَّل من API، بطاقات، مهام عاجلة، قائمة آخر نشاط.  
2. **مهامي:** تبويبات للتصفية؛ زر «ابدأ العمل» للحالة `assigned` و«أرسل للمراجعة» لـ `in_progress`.  
3. **أدائي:** حلقة SVG للنتيجة، خط زمني Canvas لآخر النقاط المسجلة، جدول السجل، بطاقة نصائح إرهاق.

---

## 12. البيانات الافتراضية وحسابات الدخول

| الدور | البريد | كلمة المرور |
|-------|--------|-------------|
| مدير | ahmed@itds.com |  |
| مدير | sara@itds.com |  |
| مدير | khaled@itds.com |  |
| موظف | m.salem@itds.com |  |
| موظف | n.qahtani@itds.com |  |
| موظف | r.otaibi@itds.com |  |
| موظف | maj.thaqafi@itds.com |  |

كما يوجد 12 موظفاً و20 مهمة وبيانات إشعارات أولية بعد تشغيل `database.py`.

---

## 13. الأسئلة الشائعة (FAQ)

**س: لماذا لا يوجد React أو Bootstrap؟**  
ج: المطلوب وف التخرج استخدام HTML/CSS/JS الخام مع تصميم متسق عبر متغيرات CSS.

**س: أين تُخزّن الجلسة؟**  
ج: في كعكة متصفح موقعة عبر `SECRET_KEY` في Flask (`session['user_id']`, `session['user_role']`, `session['user_name']`).

**س: كيف أُعيد تهيئة البيانات؟**  
ج: احذف ملف `itds.db` ثم نفّذ `python database.py` مجدداً.

**س: لماذا تُستخدم معادلات بسيطة بدل تعلم آلة؟**  
ج: لتكون النتائج **قابلة للشرح أمام لجنة التخرج** ولتجنب تعقيد النشر والاعتماديات.

---

## 14. قاموس المصطلحات (Glossary)

| المصطلح | شرح مبسّط | مثال من المشروع |
|---------|-----------|-----------------|
| **JSON** | صيغة نصية لتبادل البيانات بين المتصفح والخادم | استجابات `/api/...` وحقول المهارات في SQLite |
| **Jinja2** | محرك قوالب يربط HTML بمتغيرات الخادم | `{{ session.user_name }}` في `base.html` |
| **Blueprint** | تجميع مسارات Flask تحت بادئة URL | `admin_bp` مع البادئة `/admin` |
| **Prepared Statements** | استعلامات بمعاملات `?` لتقليل حقن SQL | جميع `execute(..., (?,))` في المشروع |
| **Workload** | عدد المهام النشطة للموظف ضمن حالات محددة | يُحدَّث عبر `sync_employee_workloads` |
| **Session** | حالة مستخدم متصلة بعد تسجيل الدخول | تخزين الدور والمعرف في الخادم موقّى |

---

## المكتبات المعتمدة (Python)

- `flask` — الخادم والموجه والجلسات  
- `gunicorn` — خادم WSGI للإنتاج ولوحة Render  
- `hashlib`, `secrets`, `sqlite3`, `json`, `datetime` — مدمجة مع Python  

---

## النشر على Render

1. ارفع الكود إلى Git بحيث يكون **جذر المستودع** هو مجلد المشروع (يظهر في الجذر ملفا `app.py` و`render.yaml`). إن وُضع المشروع في مجلد فرعي داخل مستودع أكبر، عيّن في Render الحقل **Root Directory** إلى مسار ذلك المجلد.
2. في [Render](https://render.com): **New → Blueprint** واختر المستودع لتطبيق `render.yaml` تلقائياً، أو أنشئ **Web Service** يدوياً:  
   - **Build Command:** `pip install -r requirements.txt`  
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`  
3. يعرّف الملف `render.yaml` المتغيرات `PYTHON_VERSION` و`ITDS_SECRET_KEY` (توليد تلقائي) و`FLASK_DEBUG=false`. يمكنك استبدال المفتاح من لوحة Render → Environment.  
4. **SQLite على Render:** على الخطة المجانية القرص **غير دائم**؛ أي إعادة نشر قد تحذف `itds.db` فيُعاد إنشاء القاعدة من البذور عند التشغيل. للاحتفاظ بالبيانات استخدم **Persistent Disk** وتوجيه مسار قاعدة البيانات إليه، أو انتقل لاحقاً إلى **PostgreSQL**.

---

## ترخيص الخط

ملفات **IBM Plex Sans Arabic** تخضع لترخيص IBM؛ يمكن استبدالها أو إضافة صيغة `woff2` داخل `static/css/base.css` عند توفر الملفات.

---

**تم بناء المشروع ضمن المسار:** `D:\VSCode\Projects\ITDS-AI` فقط، وفق القيود المذكورة في وثيقة التخرج.
