# Mini Judge – Web Classroom + Online Judge

Hệ thống lớp học trực tuyến tích hợp chấm bài tự động, xây dựng bằng **Python / Django 5.2**.
Giáo viên tạo lớp, ra bài tập kèm Test Case; sinh viên tham gia lớp bằng mã, nộp bài **C++** hoặc **Python**
và nhận kết quả chấm ngay (Accepted / Wrong Answer / Compile Error / Runtime Error / Time Limit / System Error).

> Bài tập lớn môn Công nghệ Phần mềm – Nhóm 2 – D23CTC2.

## Chức năng chính
- Đăng ký / đăng nhập, phân quyền **Teacher** / **Student**.
- Lớp học: tạo lớp, tham gia bằng mã, kick / ban / unban sinh viên.
- Bài tập: tạo, sửa, publish / close / reopen, quản lý Test Case, import / export gói bài (ZIP).
- Nộp bài & chấm tự động; mỗi sinh viên 1 lượt nộp cho đến khi giáo viên reset.
- Điểm = % Test Case đạt, xem kết quả từng Test Case.

## Chạy trên máy (không Docker)
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
copy .env.example .env          # tuỳ chọn; mặc định dùng SQLite
python manage.py migrate
python manage.py seed_demo      # dữ liệu mẫu (tuỳ chọn)
python manage.py runserver
```
Cần cài **g++** (MinGW / GCC) và thêm vào `PATH` để chấm bài C++. Chấm Python không cần g++.

Tài khoản mẫu sau `seed_demo` (mật khẩu `Demo@12345`): `teacher_demo`, `student_demo`, `student_demo2`; mã lớp `DEMO0001`.

## Chạy bằng Docker (Django + PostgreSQL)
```bash
docker compose up --build
```
Mở http://localhost:8000 — migrate và seed dữ liệu mẫu chạy tự động khi container khởi động.

## Kiểm thử
```bash
python manage.py test                      # chạy toàn bộ unit test
coverage run manage.py test && coverage report
```
Kết quả đo được: **121 test, độ phủ 93%** (statement coverage, không tính migrations / test / admin).
CI yêu cầu độ phủ tối thiểu 80% (`coverage report --fail-under=80`).

## CI/CD (GitHub Actions)
`.github/workflows/ci-cd.yml`: lint (flake8) → test + coverage trên PostgreSQL → build & smoke test bằng `docker compose` → deploy lên Render qua Deploy Hook.

## Triển khai lên Render
1. Đẩy mã lên GitHub.
2. Render → **New → Blueprint** → chọn repo (file `render.yaml` tạo sẵn Web Service Docker + PostgreSQL).
3. (Tuỳ chọn, để CI tự deploy) Render → Service → Settings → **Deploy Hook**; thêm vào GitHub → Settings → Secrets → `RENDER_DEPLOY_HOOK`.

Lưu ý: gói miễn phí của Render “ngủ” sau thời gian không dùng nên lần truy cập đầu có thể chậm.

## Biến môi trường
Xem `.env.example`: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, `SEED_DEMO`.

## Cấu trúc thư mục
```
accounts/     người dùng, đăng ký / đăng nhập, lệnh seed_demo
classrooms/   lớp học, thành viên, ban
problems/     bài tập, Test Case, import / export gói bài
submissions/  nộp bài, lưu kết quả, grading.py (điều phối chấm)
judge/        compiler -> executor -> checker -> service (lõi chấm)
config/       settings, urls
```

## Hạn chế đã biết
- Bộ chấm chạy trực tiếp trong tiến trình server (giới hạn thời gian + bộ nhớ, chưa sandbox bằng container riêng); chỉ nên cho người dùng tin cậy nộp bài.
- Giới hạn bộ nhớ (`RLIMIT_AS`) chỉ áp dụng trên Linux/macOS.
- Chấm đồng bộ trong request; chưa có hàng đợi (Celery).
