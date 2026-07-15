# University Medical Center — Upgrade Guide
## কী কী নতুন যোগ হয়েছে

| # | Feature | ফাইল |
|---|---------|-------|
| 1 | **Doctor Time Slot System** | `clinic/models.py` → `DoctorAvailability`, `clinic/views.py` → `manage_availability`, `book_appointment` |
| 2 | **Notification System** | `clinic/models.py` → `Notification`, `templates/notifications.html` |
| 3 | **Doctor Profile Page** | `templates/doctor_profile.html`, `accounts/models.py` (specialty, dept, bio fields) |
| 4 | **Prescription PDF** | `clinic/views.py` → `prescription_pdf` (ReportLab) |
| 5 | **Search & Filter** | Doctor list filter (specialty/dept), Student history filter (status/date) |
| 6 | **Reschedule** | `clinic/views.py` → `reschedule_appointment`, `templates/reschedule.html` |
| 7 | **Health Card** | `templates/health_card.html` — সব diagnosis একসাথে |
| 8 | **Admin Reports** | `clinic/views.py` → `admin_reports`, Chart.js দিয়ে monthly + status + top doctors |

---

## ইনস্টলেশন স্টেপ

### ১. নতুন packages install করো
```bash
pip install reportlab Pillow
# MySQL ব্যবহার করলে:
pip install mysqlclient
```

### ২. ফাইলগুলো replace করো (তোমার project-এ)

```
medical_center/
├── accounts/
│   ├── admin.py              ← replace
│   ├── context_processors.py ← replace
│   ├── models.py             ← replace (নতুন fields: specialty, department, bio, qualifications, experience_years)
│   ├── views.py              ← replace
│   └── migrations/
│       └── 0003_profile_doctor_fields.py  ← নতুন file, এখানে copy করো
│
├── clinic/
│   ├── admin.py              ← replace
│   ├── forms.py              ← replace
│   ├── models.py             ← replace (নতুন models: DoctorAvailability, Notification)
│   ├── urls.py               ← replace
│   ├── views.py              ← replace
│   └── migrations/
│       └── 0003_doctoravailability_notification.py  ← নতুন file, copy করো
│
├── medical_center/
│   └── settings.py           ← replace (password টা তোমার নিজেরটা দিও!)
│
└── templates/
    ├── base.html                  ← replace
    ├── book_appointment.html      ← replace
    ├── student_history.html       ← replace
    ├── doctor_list.html           ← replace
    ├── doctor_profile.html        ← নতুন
    ├── health_card.html           ← নতুন
    ├── manage_availability.html   ← নতুন
    ├── notifications.html         ← নতুন
    ├── reschedule.html            ← নতুন
    ├── admin_reports.html         ← নতুন
    └── accounts/
        └── profile.html          ← replace
```

### ৩. Migrations চালাও
```bash
python manage.py makemigrations accounts
python manage.py makemigrations clinic
python manage.py migrate
```
অথবা শুধু:
```bash
python manage.py migrate
```

### ৪. Server চালাও
```bash
python manage.py runserver
```

---

## নতুন URL গুলো

| URL | কী করে |
|-----|---------|
| `/doctors/<id>/` | Doctor profile page |
| `/health-card/` | Student health card |
| `/reschedule/<id>/` | Appointment reschedule |
| `/prescription/<id>/pdf/` | PDF download |
| `/doctor/availability/` | Doctor নিজের schedule manage করবে |
| `/notifications/` | সব notifications |
| `/admin-reports/` | Staff-only analytics |

---

## Doctor Setup (প্রথমবার)
1. Doctor হিসেবে login করো
2. **My Profile** এ গিয়ে specialty, department, bio fill করো
3. **My Schedule** এ গিয়ে available days ও times add করো
4. এরপর students সেই slots দেখে book করতে পারবে

---

## যদি Notification Bell কাজ না করে
`accounts/context_processors.py` ঠিকমতো `settings.py`-তে আছে কিনা check করো:
```python
'accounts.context_processors.user_role',
```
এটা `TEMPLATES → OPTIONS → context_processors` এর মধ্যে থাকতে হবে।
