# Tài liệu dự án

| Thư mục | Nội dung |
|---|---|
| `srs/SRS.md` | Đặc tả yêu cầu phần mềm (IEEE 830) |
| `design/SDD.md` | Thiết kế phần mềm, đặc tả endpoint |
| `erd/ddl.sql` | DDL PostgreSQL của 9 bảng nghiệp vụ |
| `uml/*.puml`, `uml/png/` | Sơ đồ PlantUML (nguồn) và ảnh PNG |
| `ci/ci-cd.yml` | Workflow GitHub Actions — chuyển vào `.github/workflows/` |

Dựng lại ảnh sơ đồ: `java -jar plantuml.jar -charset UTF-8 -tpng -o png uml/*.puml`
