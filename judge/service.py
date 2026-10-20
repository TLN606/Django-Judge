import shutil
from dataclasses import dataclass

from .checker import OutputChecker
from .compiler import get_compiler
from .executor import ProgramExecutor


@dataclass
class JudgeResult:
    status: str
    score: float = 0
    execution_time: float = 0
    memory_used: int | None = None
    actual_output: str = ''
    error_message: str = ''


class JudgeService:
    """Điều phối: biên dịch -> thực thi -> so sánh output."""

    def __init__(self):
        self.executor = ProgramExecutor()
        self.checker = OutputChecker()

    # ------------------------------------------------------------------
    # Chấm nhiều Test Case: biên dịch MỘT lần rồi chạy lần lượt
    # ------------------------------------------------------------------
    def judge_all(
        self,
        source_code: str,
        tests: list[tuple[str, str]],
        time_limit: float = 2.0,
        language: str = 'cpp',
        memory_limit_mb: int | None = None,
    ) -> list[JudgeResult]:
        """Chấm ``source_code`` trên danh sách ``(input, expected_output)``."""

        compiler = get_compiler(language)

        if compiler is None:
            return [
                JudgeResult(
                    status='system_error',
                    error_message=f'Language "{language}" is not supported.',
                )
                for _ in tests
            ]

        compile_result = compiler.compile(source_code)

        try:

            if not compile_result.success:
                return [
                    JudgeResult(
                        status='compile_error',
                        error_message=compile_result.error_message,
                    )
                    for _ in tests
                ]

            return [
                self._run_one(
                    compile_result.command,
                    input_data,
                    expected_output,
                    time_limit,
                    memory_limit_mb,
                )
                for input_data, expected_output in tests
            ]

        finally:
            if compile_result.work_dir:
                shutil.rmtree(compile_result.work_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Chấm một Test Case (giữ nguyên chữ ký cũ để tương thích)
    # ------------------------------------------------------------------
    def judge(
        self,
        source_code: str,
        input_data: str,
        expected_output: str,
        time_limit: float = 2.0,
        language: str = 'cpp',
        memory_limit_mb: int | None = None,
    ) -> JudgeResult:

        return self.judge_all(
            source_code,
            [(input_data, expected_output)],
            time_limit=time_limit,
            language=language,
            memory_limit_mb=memory_limit_mb,
        )[0]

    # ------------------------------------------------------------------
    def _run_one(
        self,
        command,
        input_data,
        expected_output,
        time_limit,
        memory_limit_mb,
    ) -> JudgeResult:

        execution = self.executor.execute(
            command=command,
            input_data=input_data,
            time_limit=time_limit,
            memory_limit_mb=memory_limit_mb,
        )

        if execution.timed_out:
            return JudgeResult(
                status='time_limit',
                execution_time=execution.execution_time,
                actual_output=execution.output,
                error_message=execution.error_message,
            )

        if not execution.success:
            return JudgeResult(
                status='runtime_error',
                execution_time=execution.execution_time,
                actual_output=execution.output,
                error_message=execution.error_message,
            )

        check = self.checker.check(
            expected_output=expected_output,
            actual_output=execution.output,
        )

        if not check.accepted:
            return JudgeResult(
                status='wrong_answer',
                execution_time=execution.execution_time,
                actual_output=execution.output,
                error_message=check.message,
            )

        return JudgeResult(
            status='accepted',
            score=100,
            execution_time=execution.execution_time,
            actual_output=execution.output,
        )
