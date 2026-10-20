"""Biên dịch (hoặc kiểm tra cú pháp) mã nguồn của sinh viên.

Mỗi lần gọi ``compile`` tạo một thư mục tạm riêng; bên gọi chịu trách
nhiệm xóa thư mục này (xem ``JudgeService``) thông qua ``work_dir``.
"""
import py_compile
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CompileResult:
    success: bool
    executable_path: str | None = None
    error_message: str = ''
    work_dir: str | None = None
    command: list[str] | None = None


class CppCompiler:
    """Biên dịch C++ bằng g++ (C++17, -O2)."""

    language = 'cpp'

    def __init__(self):
        self.compiler = 'g++'

    def compile(self, source_code: str) -> CompileResult:

        temp_dir = tempfile.mkdtemp(prefix='minijudge_')
        source_path = Path(temp_dir) / 'solution.cpp'
        executable_path = Path(temp_dir) / 'solution.exe'

        try:
            source_path.write_text(source_code, encoding='utf-8')

            process = subprocess.run(
                [
                    self.compiler,
                    str(source_path),
                    '-std=c++17',
                    '-O2',
                    '-o',
                    str(executable_path),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if process.returncode != 0:
                return CompileResult(
                    success=False,
                    error_message=process.stderr,
                    work_dir=temp_dir,
                )

            return CompileResult(
                success=True,
                executable_path=str(executable_path),
                work_dir=temp_dir,
                command=[str(executable_path)],
            )

        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                error_message='Compilation timed out.',
                work_dir=temp_dir,
            )

        except FileNotFoundError:
            return CompileResult(
                success=False,
                error_message=(
                    'g++ compiler was not found. '
                    'Please install MinGW/GCC '
                    'and add g++ to PATH.'
                ),
                work_dir=temp_dir,
            )

        except Exception as e:
            return CompileResult(
                success=False,
                error_message=str(e),
                work_dir=temp_dir,
            )


class PythonCompiler:
    """Python không cần biên dịch: chỉ kiểm tra cú pháp rồi chạy bằng interpreter."""

    language = 'python'

    def compile(self, source_code: str) -> CompileResult:

        temp_dir = tempfile.mkdtemp(prefix='minijudge_')
        source_path = Path(temp_dir) / 'solution.py'

        try:
            source_path.write_text(source_code, encoding='utf-8')
            py_compile.compile(str(source_path), doraise=True)

        except py_compile.PyCompileError as e:
            return CompileResult(
                success=False,
                error_message=str(e),
                work_dir=temp_dir,
            )

        except Exception as e:
            return CompileResult(
                success=False,
                error_message=str(e),
                work_dir=temp_dir,
            )

        return CompileResult(
            success=True,
            executable_path=str(source_path),
            work_dir=temp_dir,
            command=[sys.executable, str(source_path)],
        )


def get_compiler(language: str):
    """Trả về trình biên dịch phù hợp với ngôn ngữ; None nếu chưa hỗ trợ."""

    if language == 'cpp':
        return CppCompiler()

    if language == 'python':
        return PythonCompiler()

    return None
