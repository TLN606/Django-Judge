# Tài liệu thiết kế phần mềm (SDD)
**Mini Judge – Web Classroom + Online Judge** — Nhóm 2, lớp D23CTC2 · Phiên bản 1.0 · 21/10/2026

Tài liệu đi kèm: `docs/srs/SRS.md`, sơ đồ trong `docs/uml/png/`, lược đồ CSDL `docs/erd/ddl.sql`.

---

## 1. Kiến trúc tổng thể
Ứng dụng web monolith theo mô hình **MVT của Django**:

| Tầng | Thành phần | Vai trò |
|---|---|---|
| Trình bày | `templates/`, `static/` (WhiteNoise phục vụ file tĩnh) | Giao diện HTML/CSS/JS |
| Điều khiển | `*/views.py`, `*/urls.py`, `*/forms.py` | Nhận request, kiểm tra quyền, gọi nghiệp vụ |
| Nghiệp vụ | `submissions/grading.py`, `judge/`, `problems/services/` | Chấm bài, nhập/xuất gói bài |
| Dữ liệu | `*/models.py`, PostgreSQL | Lưu trữ |

Sơ đồ: `docs/uml/png/07_architecture.png` (kiến trúc), `09_deployment.png` (triển khai).

### 1.1 Cấu trúc module
| App | Trách nhiệm |
|---|---|
| `accounts` | Người dùng tùy biến (`role`: teacher/student), đăng ký, đăng nhập |
| `classrooms` | Lớp học, thành viên, danh sách cấm |
| `problems` | Bài tập, Test Case, lượt làm bài (Attempt), import/export |
| `submissions` | Bài nộp, kết quả từng Test Case, điều phối chấm (`grading.py`) |
| `judge` | Lõi chấm: `compiler` → `executor` → `checker`, điều phối bởi `service` |

## 2. Thiết kế bộ chấm (Online Judge)

Sơ đồ: `04_seq_submit_judge.png` (tuần tự), `06_activity_judge.png` (hoạt động).

1. `submit_solution` kiểm tra quyền, khóa `ProblemAttempt` bằng `select_for_update` trong `transaction.atomic`, tạo `Submission(status=running)`, chuyển Attempt sang `locked`.
2. `grade_submission` lấy các Test Case và gọi `JudgeService.judge_all(...)`.
3. `JudgeService` chọn `Compiler` theo ngôn ngữ (`get_compiler`), biên dịch **một lần**, sau đó chạy từng Test Case qua `ProgramExecutor.execute` và so khớp bằng `OutputChecker`.
4. Thư mục tạm luôn được xóa trong khối `finally`.
5. `grade_submission` lưu `SubmissionResult` cho từng Test Case, tính điểm `= đạt / tổng × 100`, ghi trạng thái tổng (lỗi đầu tiên hoặc `accepted`) và `judged_at`.

| Thành phần | Chi tiết |
|---|---|
| `CppCompiler` | `g++ -std=c++17 -O2`, thời gian biên dịch tối đa 10 s |
| `PythonCompiler` | Kiểm tra cú pháp bằng `py_compile`, chạy bằng `python` |
| `ProgramExecutor` | `subprocess.run` với `timeout`; giới hạn bộ nhớ `RLIMIT_AS` (Linux/macOS) |
| `OutputChecker` | So sánh sau khi `strip()` hai đầu |

Trạng thái: `accepted`, `wrong_answer`, `compile_error`, `runtime_error`, `time_limit`, `system_error` (`memory_limit` được khai báo trong model nhưng chưa được bộ chấm sinh ra).

**Hạn chế thiết kế:** chấm đồng bộ trong tiến trình web; chương trình của người nộp chạy cùng quyền với server (chưa cô lập bằng container). Hướng mở rộng: hàng đợi (Celery) và sandbox container.

## 3. Thiết kế dữ liệu
- Lược đồ quan hệ và DDL PostgreSQL: `docs/erd/ddl.sql` (9 bảng nghiệp vụ); ERD: `docs/uml/png/08_erd.png`.
- Lược đồ ở dạng chuẩn **3NF**: mỗi bảng có khóa chính đại diện (`id`); thuộc tính không khóa phụ thuộc trực tiếp vào khóa; các quan hệ nhiều–nhiều giữa người dùng và lớp (`ClassroomMember`), giữa người dùng và bài tập (`ProblemAttempt`) được tách thành bảng riêng; kết quả từng Test Case tách khỏi bài nộp (`SubmissionResult`).
- Ràng buộc: mã lớp duy nhất; `(classroom, student)` duy nhất trong `ClassroomMember`; `(problem, student)` duy nhất trong `ProblemAttempt`.

## 4. Thiết kế phân quyền
| Quy tắc | Áp dụng |
|---|---|
| Phải đăng nhập | Mọi endpoint nghiệp vụ (`@login_required`); chưa đăng nhập → 302 tới `/accounts/login/` |
| Teacher chủ lớp | Tạo bài, quản lý Test Case, publish/close/reopen, import/export, kick/ban/unban, reset, xem mọi bài nộp của lớp |
| Student là thành viên | Xem bài `published`/`closed` của lớp, nộp bài, xem bài nộp của chính mình |
| Test Case ẩn | Chỉ Teacher thấy Expected Output; Student chỉ thấy Expected Output của Sample |
| Admin | `/admin/` (Django Admin) |

## 5. Đặc tả endpoint

Hệ thống render HTML phía server (không có REST API). Với mọi endpoint dưới đây, người chưa đăng nhập nhận **302 → `/accounts/login/`**, trừ khi ghi chú khác. Kết quả "302" là chuyển hướng tới trang nêu trong cột *Kết quả*. Mã 404 khi đối tượng (`id`) không tồn tại; 405 khi dùng sai phương thức ở endpoint khai báo chỉ nhận POST.

### 5.1 Tài khoản (`/accounts/`)
| Method | URL | Quyền | Request body | Response |
|---|---|---|---|---|
| GET | `/accounts/register/` | Khách | — | 200 form đăng ký; đã đăng nhập → 302 `/` |
| POST | `/accounts/register/` | Khách | `username`, `email`, `password1`, `password2` | 302 → `/classrooms/` (tạo user role=student và đăng nhập); lỗi → 200 kèm lỗi form |
| GET | `/accounts/login/` | Khách | — | 200 form đăng nhập |
| POST | `/accounts/login/` | Khách | `username`, `password` | 302 khi đúng; sai → 200 kèm lỗi |
| POST | `/accounts/logout/` | Đã đăng nhập | — | 302 |

### 5.2 Lớp học (`/classrooms/`)
| Method | URL | Quyền | Request body | Response |
|---|---|---|---|---|
| GET | `/classrooms/` | Đăng nhập | — | 200 danh sách lớp |
| GET | `/classrooms/<classroom_id>/` | Chủ lớp / thành viên | — | 200 chi tiết lớp; 404 nếu không có lớp |
| GET, POST | `/classrooms/create/` | Teacher | `name`, `description` | GET 200; POST 302 → chi tiết lớp (mã lớp tự sinh); Student → 302 `/classrooms/` |
| GET, POST | `/classrooms/join/` | Student | `code` | GET 200; POST thành công 302 → chi tiết lớp; mã sai / bị ban / đã là thành viên → 200 kèm lỗi; không phải Student → 302 |
| POST | `/classrooms/<classroom_id>/members/<student_id>/kick/` | Chủ lớp / Admin | — | 302 → chi tiết lớp; GET → 405 |
| POST | `/classrooms/<classroom_id>/members/<student_id>/ban/` | Chủ lớp / Admin | — | 302 → chi tiết lớp (xóa thành viên, tạo ban `is_active=True`) |
| POST | `/classrooms/<classroom_id>/members/<student_id>/unban/` | Chủ lớp / Admin | — | 302 → chi tiết lớp (`is_active=False`) |

### 5.3 Bài tập (`/problems/`)
| Method | URL | Quyền | Request body | Response |
|---|---|---|---|---|
| GET | `/problems/` | Đăng nhập | — | 200 danh sách bài (Teacher: bài lớp mình dạy; Student: bài `published`/`closed` của lớp đã tham gia) |
| GET | `/problems/<problem_id>/` | Chủ lớp / thành viên | — | 200 đề bài; không có quyền → 302 `/problems/`; 404 |
| GET, POST | `/problems/classroom/<classroom_id>/create/` | Chủ lớp / Admin | `title`, `description`, `input_description`, `output_description`, `constraints`, `difficulty`, `time_limit`, `memory_limit` + formset `test_cases-*` (`input_data`, `expected_output`, `is_sample`) | POST 302 → đề bài (trạng thái `draft`); lỗi → 200 |
| GET, POST | `/problems/<problem_id>/edit/` | Chủ lớp / Admin | như tạo bài | POST 302 → đề bài |
| GET, POST | `/problems/classroom/<classroom_id>/import/` | Chủ lớp / Admin | `package_zip` (file `.zip`) hoặc `package_folder` (các file `problem.txt`, `input.txt`, `output.txt`) | 302 → đề bài đã tạo (`draft`); gói lỗi → 200 kèm thông báo |
| GET | `/problems/<problem_id>/export/` | Chủ lớp / Admin | — | 200 file ZIP (`application/zip`); bài không có Test Case → 302 → đề bài kèm thông báo lỗi |
| GET | `/problems/<problem_id>/test-cases/` | Teacher chủ lớp | — | 200 danh sách Test Case |
| GET, POST | `/problems/<problem_id>/test-cases/add/` | Teacher chủ lớp | `input_data`, `expected_output`, `is_sample` | POST 302 → danh sách Test Case |
| GET, POST | `/problems/<problem_id>/test-cases/<test_case_id>/edit/` | Teacher chủ lớp | như thêm | POST 302 |
| GET, POST | `/problems/<problem_id>/test-cases/<test_case_id>/delete/` | Teacher chủ lớp | — | GET 200 trang xác nhận; POST 302 → danh sách Test Case |
| POST | `/problems/<problem_id>/publish/` | Chủ lớp / Admin | — | 302 → đề bài (`status=published`); GET → 405 |
| POST | `/problems/<problem_id>/close/` | Chủ lớp / Admin | — | 302 (`status=closed`) |
| POST | `/problems/<problem_id>/reopen/` | Chủ lớp / Admin | — | 302 (`status=published`) |

### 5.4 Bài nộp (`/submissions/`)
| Method | URL | Quyền | Request body | Response |
|---|---|---|---|---|
| GET | `/submissions/problem/<problem_id>/submit/` | Student thành viên | — | 200 form nộp bài; Teacher/không phải thành viên → 302 |
| POST | `/submissions/problem/<problem_id>/submit/` | Student thành viên, bài `published` | `language` (`cpp`\|`python`), `source_code` | 302 → `/submissions/<id>/` sau khi chấm xong; Attempt đã `locked` → 200 kèm lỗi, không tạo bài nộp |
| GET | `/submissions/problem/<problem_id>/` | Student (bài nộp của mình) / Teacher chủ lớp (mọi bài nộp) | — | 200 danh sách bài nộp |
| GET | `/submissions/<submission_id>/` | Chủ bài nộp / Teacher chủ lớp | — | 200 kết quả từng Test Case; người khác → 302 `/problems/` |
| POST | `/submissions/problem/<problem_id>/reset/<student_id>/` | Teacher chủ lớp / Admin | — | 302 → danh sách bài nộp; Attempt về `available`; không có quyền → 302 đề bài |

### 5.5 Khác
| Method | URL | Mô tả |
|---|---|---|
| GET | `/` | Trang chủ |
| GET | `/admin/` | Django Admin (quản lý user, lớp, bài…) |

## 6. Thiết kế triển khai
- **Container:** `Dockerfile` (Python 3.13-slim + `g++`, Gunicorn), `docker-entrypoint.sh` chạy `migrate` (và `seed_demo` nếu `SEED_DEMO=1`) trước khi khởi động.
- **Cục bộ:** `docker-compose.yml` gồm `web` và `db` (PostgreSQL 16, có healthcheck).
- **Đám mây:** `render.yaml` (Blueprint) tạo Web Service Docker và PostgreSQL trên Render.
- **CI/CD:** GitHub Actions — lint (`flake8`) → test + coverage ≥ 80% trên PostgreSQL → build và smoke test bằng Docker Compose → gọi Deploy Hook của Render.
- **Cấu hình:** biến môi trường `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, `SEED_DEMO` (xem `.env.example`).

Vì Vercel chạy hàm serverless không cho tiến trình dài và không có trình biên dịch `g++`, hệ thống không triển khai được trên Vercel; Render (Docker) được chọn.
