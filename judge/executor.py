import os
import subprocess
import time
from dataclasses import dataclass

try:  # chỉ có trên Linux/macOS
    import resource
except ImportError:  # Windows
    resource = None


@dataclass
class ExecutionResult:
    success: bool
    output: str = ''
    error_message: str = ''
    execution_time: float = 0.0
    return_code: int | None = None
    timed_out: bool = False


def _limit_memory(memory_limit_mb: int | None):
    """Tạo hàm preexec để giới hạn bộ nhớ ảo của tiến trình con (chỉ POSIX)."""

    if not memory_limit_mb or resource is None or os.name != 'posix':
        return None

    limit = int(memory_limit_mb) * 1024 * 1024

    def apply():
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

    return apply


class ProgramExecutor:

    def execute(
        self,
        executable_path: str | None = None,
        input_data: str = '',
        time_limit: float = 2.0,
        command: list[str] | None = None,
        memory_limit_mb: int | None = None,
    ) -> ExecutionResult:

        if command is None:
            command = [executable_path]

        start_time = time.perf_counter()

        try:

            process = subprocess.run(
                command,
                input=input_data,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=time_limit,
                preexec_fn=_limit_memory(memory_limit_mb),
            )

            execution_time = time.perf_counter() - start_time

            if process.returncode != 0:
                return ExecutionResult(
                    success=False,
                    output=process.stdout,
                    error_message=process.stderr,
                    execution_time=execution_time,
                    return_code=process.returncode,
                )

            return ExecutionResult(
                success=True,
                output=process.stdout,
                execution_time=execution_time,
                return_code=process.returncode,
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                error_message='Time Limit Exceeded.',
                execution_time=time.perf_counter() - start_time,
                timed_out=True,
            )

        except FileNotFoundError:
            return ExecutionResult(
                success=False,
                error_message='Executable not found.',
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                error_message=str(e),
            )
