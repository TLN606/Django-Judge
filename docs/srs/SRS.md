# Đặc tả yêu cầu phần mềm (SRS)
**Hệ thống Web Classroom tích hợp Online Judge (Mini Judge)** — Nhóm 2, lớp D23CTC2
Phiên bản 1.0 · 21/10/2026 · Theo cấu trúc IEEE 830

Nhóm thực hiện: Nguyễn Lê Hải Triều (Nhóm trưởng, 23Q74802012007), Trịnh Lâm Ngân (23Q74802012011), Nguyễn Quang Duy (23Q74802012002).

---

## 1. Giới thiệu

### 1.1 Mục đích
Tài liệu mô tả đầy đủ yêu cầu của hệ thống Mini Judge, làm cơ sở cho thiết kế, lập trình, kiểm thử và nghiệm thu. Đối tượng đọc: giảng viên hướng dẫn, các thành viên nhóm.

### 1.2 Phạm vi
Mini Judge là ứng dụng web cho phép giáo viên tổ chức lớp học, giao bài tập lập trình kèm Test Case; sinh viên tham gia lớp bằng mã, nộp mã nguồn C++ hoặc Python và nhận kết quả chấm tự động. Hệ thống **không** bao gồm: thi đấu có bảng xếp hạng, REST API công khai, chấm điểm bằng AI, thanh toán.

### 1.3 Định nghĩa, từ viết tắt
| Thuật ngữ | Ý nghĩa |
|---|---|
| Teacher / Student / Admin | Giáo viên / Sinh viên / Quản trị viên |
| Classroom | Lớp học, có mã lớp duy nhất |
| Problem | Bài tập lập trình trong một lớp |
| Test Case | Cặp (Input, Expected Output) dùng để chấm |
| Sample Test Case | Test Case được hiển thị cho sinh viên; các Test Case còn lại là *ẩn* |
| Submission | Một lần nộp mã nguồn |
| Attempt | Lượt làm bài của một sinh viên với một bài tập (mỗi lượt cho phép một lần nộp) |
| AC / WA / CE / RE / TLE | Accepted / Wrong Answer / Compile Error / Runtime Error / Time Limit Exceeded |

### 1.4 Tài liệu tham khảo
1. IEEE Std 830-1998, *Recommended Practice for Software Requirements Specifications*.
2. Mẫu báo cáo thực hành LAB và hướng dẫn của môn Công nghệ Phần mềm (TS. Lê Tỷ Khánh).
3. Django 5.2 Documentation — https://docs.djangoproject.com/en/5.2/
4. Tài liệu thiết kế `docs/design/SDD.md`, lược đồ CSDL `docs/erd/ddl.sql`, sơ đồ UML `docs/uml/`.

---

## 2. Mô tả tổng quan

### 2.1 Bối cảnh sản phẩm
Ứng dụng web độc lập theo mô hình Django MVT, gồm các thành phần: giao diện web (template), tầng xử lý (view), tầng dữ liệu (ORM + PostgreSQL) và **bộ chấm bài** (biên dịch → thực thi → so sánh). Bộ chấm gọi trình biên dịch/interpreter của hệ điều hành thông qua tiến trình con (xem `docs/uml/07_architecture.png`).

### 2.2 Chức năng chính (tóm tắt)
Quản lý tài khoản; quản lý lớp và thành viên (kick/ban/unban); quản lý bài tập và Test Case (kể cả nhập/xuất gói bài, publish/close/reopen); nộp bài và chấm tự động; xem kết quả, lịch sử nộp; reset lượt làm bài.

### 2.3 Người dùng
| Actor | Mô tả | Quyền chính |
|---|---|---|
| Student | Sinh viên, tự đăng ký | Tham gia lớp, xem bài, nộp bài, xem kết quả của mình |
| Teacher | Giáo viên | Tạo lớp, ra bài, quản lý Test Case, xem bài nộp, reset lượt, kick/ban |
| Admin | Quản trị (Django Admin) | Quản lý tài khoản và dữ liệu lớp học |
| Online Judge | Thành phần chấm bài trong hệ thống | Biên dịch, thực thi, so sánh output |

Tài khoản đăng ký công khai luôn có vai trò Student; tài khoản Teacher/Admin do Admin tạo.

### 2.4 Môi trường vận hành
- Server: Linux (Docker, Python 3.13) hoặc Windows khi phát triển; cần `g++` để chấm C++.
- CSDL: PostgreSQL 16 (SQLite khi phát triển cục bộ).
- Client: trình duyệt hiện đại (Chrome, Edge, Firefox), màn hình từ 360 px trở lên.

### 2.5 Ràng buộc
- Ngôn ngữ/Framework: Python + Django (yêu cầu của môn học).
- Ngôn ngữ chấm được hỗ trợ: C++17 và Python 3.
- Giới hạn bộ nhớ khi chấm chỉ có hiệu lực trên Linux/macOS (`RLIMIT_AS`).
- Chấm bài chạy đồng bộ trong tiến trình web; chưa có hàng đợi.
- Triển khai trên gói miễn phí (Render) có thể bị "ngủ" khi không dùng.

### 2.6 Giả định và phụ thuộc
Người nộp bài là sinh viên của lớp (đáng tin cậy ở mức môn học); máy chủ có sẵn trình biên dịch; có kết nối tới CSDL.

---

## 3. Yêu cầu chức năng

Mỗi yêu cầu có mã FR, liên kết User Story (US) và Use Case (UC) trong báo cáo.

### 3.1 Tài khoản
| ID | Yêu cầu | US / UC |
|---|---|---|
| FR-01 | Hệ thống cho phép đăng ký bằng tên đăng nhập, email, mật khẩu (nhập 2 lần). Tài khoản mới luôn có vai trò Student. | US01 / UC01 |
| FR-02 | Mật khẩu phải qua bộ kiểm tra của Django (đủ độ dài, không quá phổ biến, không toàn số, không giống tên đăng nhập). | US01 |
| FR-03 | Hệ thống cho phép đăng nhập/đăng xuất; thông tin sai hiển thị thông báo lỗi. Các trang nghiệp vụ yêu cầu đăng nhập, người chưa đăng nhập bị chuyển về trang đăng nhập. | US02 / UC02 |
| FR-04 | Admin quản lý tài khoản qua trang `/admin/`. | US17 / UC16 |

### 3.2 Lớp học
| ID | Yêu cầu | US / UC |
|---|---|---|
| FR-05 | Teacher tạo lớp (tên, mô tả); hệ thống sinh mã lớp duy nhất. Student không được tạo lớp. | US10 / UC09 |
| FR-06 | Student tham gia lớp bằng mã (không phân biệt hoa/thường). Từ chối nếu mã không tồn tại, Student đang bị ban, hoặc là Teacher. Tham gia lại không tạo thành viên trùng. | US03 / UC03 |
| FR-07 | Hiển thị danh sách lớp và chi tiết lớp (thành viên, bài tập) cho Teacher chủ lớp và Student là thành viên. | US04, US11 / UC04, UC10 |
| FR-08 | Teacher chủ lớp có thể kick (xóa khỏi lớp), ban (xóa khỏi lớp và chặn tham gia lại) và unban thành viên; chỉ nhận yêu cầu POST. Student bị ban không thể tham gia lại bằng mã lớp. | US21 / UC21 |
| FR-09 | Admin xem/quản lý dữ liệu lớp học qua `/admin/`. | US18 / UC17 |

### 3.3 Bài tập và Test Case
| ID | Yêu cầu | US / UC |
|---|---|---|
| FR-10 | Teacher chủ lớp tạo bài tập (tiêu đề, mô tả, định dạng input/output, ràng buộc, độ khó, giới hạn thời gian mặc định 1 s, bộ nhớ mặc định 256 MB) kèm Test Case; bài mới ở trạng thái `draft`. | US12 / UC11 |
| FR-11 | Teacher chủ lớp sửa bài tập và Test Case (thêm/sửa/xóa). | US13, US14 / UC12, UC13 |
| FR-12 | Teacher chủ lớp chuyển trạng thái bài: `draft → published` (publish), `published → closed` (close), `closed → published` (reopen). Chỉ bài `published` mới nhận bài nộp. | US22 / UC22 |
| FR-13 | Student chỉ thấy bài tập `published`/`closed` của lớp mình tham gia; Teacher thấy bài của lớp mình dạy. | US05, US06 / UC05 |
| FR-14 | Sinh viên chỉ thấy Input/Expected Output của Sample Test Case; Test Case ẩn không bao giờ lộ đáp án cho Student. | US06 |
| FR-15 | Teacher xuất bài tập thành gói ZIP (`problem.txt`, `input.txt`, `output.txt`) và nhập gói ZIP hoặc thư mục vào lớp của mình. Gói sai định dạng, thiếu file, không phải ZIP hoặc có đường dẫn nguy hiểm (path traversal) bị từ chối kèm thông báo; bài nhập vào ở trạng thái `draft`. | US23 / UC23 |

### 3.4 Nộp bài và chấm tự động
| ID | Yêu cầu | US / UC |
|---|---|---|
| FR-16 | Student là thành viên lớp nộp mã nguồn C++ hoặc Python cho bài `published`. Teacher và người không thuộc lớp không được nộp. | US07 / UC06 |
| FR-17 | Mỗi Attempt cho phép **một** lần nộp; sau khi nộp, Attempt chuyển `locked`. Nộp lần hai bị từ chối với thông báo cho đến khi Teacher reset. Việc kiểm tra và khóa Attempt thực hiện trong giao dịch để tránh nộp trùng. | US07, US24 |
| FR-18 | Hệ thống biên dịch mã (C++: `g++ -std=c++17 -O2`; Python: kiểm tra cú pháp) **một lần** cho mỗi bài nộp. | US19 / UC18 |
| FR-19 | Hệ thống chạy chương trình trên từng Test Case với giới hạn thời gian và bộ nhớ của bài. | US19, US20 / UC19 |
| FR-20 | Hệ thống so sánh output thực tế với Expected Output sau khi loại bỏ khoảng trắng đầu/cuối, và gán trạng thái cho từng Test Case: AC, WA, CE, RE, TLE hoặc System Error. | US20 / UC20 |
| FR-21 | Trạng thái bài nộp là trạng thái của Test Case lỗi đầu tiên (hoặc AC nếu tất cả đạt); **điểm = số Test Case đạt / tổng số × 100**. Bài không có Test Case cho kết quả System Error. | US08 |
| FR-22 | Ngôn ngữ không được hỗ trợ cho kết quả System Error. Thư mục tạm của lần chấm luôn được xóa sau khi chấm. | US19 |
| FR-23 | Student xem kết quả từng Test Case của bài nộp của chính mình; Teacher xem bài nộp thuộc lớp mình dạy. Người khác không xem được. | US08, US16 / UC07, UC15 |
| FR-24 | Student xem lịch sử nộp bài của mình theo bài; Teacher xem danh sách bài nộp của mọi sinh viên trong bài. | US09, US15 / UC08, UC14 |
| FR-25 | Teacher chủ lớp (hoặc Admin) reset Attempt của một Student: Attempt trở về `available`, tăng `reset_count`, ghi người reset và thời điểm; chỉ nhận POST. | US24 / UC24 |

---

## 4. Yêu cầu phi chức năng

| ID | Nhóm | Yêu cầu | Cách kiểm chứng |
|---|---|---|---|
| NFR-01 | Hiệu năng | Với bài có giới hạn thời gian *T*, mỗi Test Case bị dừng và ghi TLE khi chạy quá *T*. | Unit test `test_infinite_loop_times_out`, `test_time_limit` |
| NFR-02 | Hiệu năng | Mã nguồn chỉ được biên dịch một lần cho toàn bộ Test Case của một bài nộp. | Unit test `test_compile_is_done_only_once` |
| NFR-03 | Bảo mật | Mật khẩu lưu dạng băm của Django; cookie phiên và CSRF chỉ gửi qua HTTPS khi `DEBUG=0`. | Kiểm tra cấu hình `settings.py` |
| NFR-04 | Bảo mật | Mọi form dùng CSRF token; các thao tác kick/ban/unban và publish/close/reopen chỉ nhận POST (GET trả 405); thao tác reset chỉ xử lý POST. | Unit test `test_kick_requires_post`; middleware CSRF của Django |
| NFR-05 | Bảo mật | Phân quyền theo vai trò và theo chủ sở hữu lớp; truy cập trái quyền bị chuyển hướng hoặc không thực hiện. | Unit test phân quyền |
| NFR-06 | Bảo mật | Khóa bí mật, thông tin CSDL và danh sách host lấy từ biến môi trường, không ghi cứng trong mã nguồn. | Kiểm tra `settings.py`, `.env.example` |
| NFR-07 | Bảo mật | Gói bài nhập vào không được ghi ra ngoài thư mục đích (chống path traversal). | Unit test `test_path_traversal_is_rejected` |
| NFR-08 | Độ tin cậy | Hai yêu cầu nộp cùng lúc không tạo hai bài nộp cho một Attempt. | Cơ chế khóa dòng `select_for_update` trong giao dịch |
| NFR-09 | Khả dụng | Giao diện sử dụng được trên màn hình rộng 360 px trở lên (responsive). | Ảnh chụp giao diện di động trong báo cáo |
| NFR-10 | Khả dụng | Lỗi nhập liệu của các form (đăng ký, tham gia lớp, nộp bài…) hiển thị ngay trên form. | Kiểm tra giao diện |
| NFR-11 | Bảo trì | Mã nguồn có unit test tự động với độ phủ ≥ 80% và pipeline CI chặn khi dưới ngưỡng. | `coverage report --fail-under=80` trong CI |
| NFR-12 | Khả chuyển | Chạy được bằng Docker Compose (web + PostgreSQL) và bằng venv trên Windows/Linux. | `README.md`, `docker-compose.yml` |
| NFR-13 | Khả chuyển | Chấm được cả C++ lẫn Python; thêm ngôn ngữ mới chỉ cần thêm một lớp Compiler. | Thiết kế `judge/compiler.py` |

---

## 5. Giao diện bên ngoài

### 5.1 Giao diện người dùng
Các màn hình chính: Đăng nhập/Đăng ký, Danh sách lớp, Chi tiết lớp, Danh sách bài tập, Đề bài, Quản lý Test Case, Nộp bài, Kết quả bài nộp, Lịch sử nộp bài, Import bài. Ảnh minh họa có trong báo cáo.

### 5.2 Giao diện phần mềm
- PostgreSQL 16 qua driver `psycopg2`.
- `g++` (hỗ trợ C++17) và Python 3 qua tiến trình con (`subprocess`).

### 5.3 Giao diện truyền thông
HTTP/HTTPS; danh sách đường dẫn và tham số xem `docs/design/SDD.md`, mục "Đặc tả endpoint".

---

## 6. Truy vết yêu cầu

| User Story | Yêu cầu chức năng |
|---|---|
| US01 | FR-01, FR-02 |
| US02 | FR-03 |
| US03 | FR-06 |
| US04, US11 | FR-07 |
| US05, US06 | FR-13, FR-14 |
| US07 | FR-16, FR-17 |
| US08 | FR-21, FR-23 |
| US09 | FR-24 |
| US10 | FR-05 |
| US12 | FR-10 |
| US13, US14 | FR-11 |
| US15, US16 | FR-23, FR-24 |
| US17, US18 | FR-04, FR-09 |
| US19 | FR-18, FR-19, FR-22 |
| US20 | FR-19, FR-20 |
| US21 | FR-08 |
| US22 | FR-12 |
| US23 | FR-15 |
| US24 | FR-17, FR-25 |

## 7. Tiêu chí nghiệm thu chung
Toàn bộ unit test pass; độ phủ mã ≥ 80%; chấm đúng các trạng thái AC, WA, CE, RE, TLE trên bài mẫu; chạy được bằng `docker compose up` (kiểm chứng thủ công) và triển khai được lên nền tảng đám mây.
