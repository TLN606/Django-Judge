from dataclasses import dataclass


@dataclass
class CheckResult:
    accepted: bool
    message: str = ''


class OutputChecker:

    def check(
        self,
        expected_output: str,
        actual_output: str,
    ) -> CheckResult:

        expected = expected_output.strip()
        actual = actual_output.strip()

        if expected == actual:

            return CheckResult(
                accepted=True,
                message='Accepted',
            )

        return CheckResult(
            accepted=False,
            message='Wrong Answer',
        )