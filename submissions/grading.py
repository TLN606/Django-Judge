"""Chấm một Submission trên toàn bộ Test Case của bài tập."""
from django.utils import timezone

from judge.service import JudgeService

from .models import SubmissionResult


def grade_submission(submission, problem, judge_service=None):
    """Chấm ``submission``, lưu SubmissionResult cho từng Test Case.

    Trạng thái tổng lấy theo lỗi đầu tiên gặp; điểm = % Test Case đạt.
    """

    judge_service = judge_service or JudgeService()

    test_cases = list(problem.test_cases.all())
    total_tests = len(test_cases)

    final_status = 'accepted'
    final_error = ''
    total_execution_time = 0
    passed_tests = 0

    if total_tests == 0:
        final_status = 'system_error'
        final_error = 'Problem has no test cases.'
        score = 0

    else:
        results = judge_service.judge_all(
            source_code=submission.source_code,
            tests=[(tc.input_data, tc.expected_output) for tc in test_cases],
            time_limit=problem.time_limit,
            language=submission.language,
            memory_limit_mb=problem.memory_limit,
        )

        for test_case, judge_result in zip(test_cases, results):

            total_execution_time += judge_result.execution_time

            SubmissionResult.objects.create(
                submission=submission,
                test_case=test_case,
                status=judge_result.status,
                execution_time=judge_result.execution_time,
                memory_used=judge_result.memory_used,
                actual_output=judge_result.actual_output,
                error_message=judge_result.error_message,
            )

            if judge_result.status == 'accepted':
                passed_tests += 1

            elif final_status == 'accepted':
                final_status = judge_result.status
                final_error = judge_result.error_message

        score = (passed_tests / total_tests) * 100

    submission.status = final_status
    submission.score = score
    submission.execution_time = total_execution_time
    submission.error_message = final_error
    submission.judged_at = timezone.now()
    submission.save()

    return submission
