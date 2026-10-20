import io
import re
import zipfile

from .package_importer import ProblemPackageError


def safe_package_name(name: str) -> str:
    """
    Convert problem title into a safe folder/file name.
    """

    name = (name or "problem").strip()

    name = re.sub(
        r'[<>:"/\\|?*]+',
        '_',
        name
    )

    name = re.sub(
        r'\s+',
        '_',
        name
    )

    name = name.strip(' ._')

    if not name:
        name = "problem"

    return name[:80]


def build_problem_txt(problem) -> str:
    """
    Export Problem model into problem.txt
    """

    return (
        f"TITLE: {problem.title}\n"
        f"\n"
        f"DESCRIPTION:\n"
        f"{problem.description.strip()}\n"
        f"\n"
        f"INPUT DESCRIPTION:\n"
        f"{problem.input_description.strip()}\n"
        f"\n"
        f"OUTPUT DESCRIPTION:\n"
        f"{problem.output_description.strip()}\n"
        f"\n"
        f"CONSTRAINTS:\n"
        f"{problem.constraints.strip()}\n"
        f"\n"
        f"DIFFICULTY: {problem.difficulty}\n"
        f"TIME_LIMIT: {problem.time_limit:g}\n"
        f"MEMORY_LIMIT: {problem.memory_limit}\n"
    )


def build_test_cases_txt(test_cases) -> tuple[str, str]:
    """
    Build input.txt and output.txt.

    Format:

    3

    [TESTCASE 1]
    ...

    [TESTCASE 2]
    ...
    """

    test_cases = list(test_cases)

    if not test_cases:
        raise ProblemPackageError(
            "Cannot export a problem without test cases."
        )

    input_parts = [
        str(len(test_cases)),
        "",
    ]

    output_parts = [
        str(len(test_cases)),
        "",
    ]

    for index, test_case in enumerate(
        test_cases,
        start=1
    ):

        input_parts.extend([
            f"[TESTCASE {index}]",
            test_case.input_data.strip(),
            "",
        ])

        output_parts.extend([
            f"[TESTCASE {index}]",
            test_case.expected_output.strip(),
            "",
        ])

    input_text = "\n".join(input_parts).rstrip() + "\n"
    output_text = "\n".join(output_parts).rstrip() + "\n"

    return input_text, output_text


def build_problem_package(problem) -> tuple[bytes, str]:
    """
    Create a ZIP package containing:

    ProblemName/
        problem.txt
        input.txt
        output.txt
    """

    package_name = safe_package_name(
        problem.title
    )

    test_cases = problem.test_cases.all().order_by('id')

    problem_txt = build_problem_txt(
        problem
    )

    input_txt, output_txt = build_test_cases_txt(
        test_cases
    )

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        mode='w',
        compression=zipfile.ZIP_DEFLATED
    ) as archive:

        archive.writestr(
            f"{package_name}/problem.txt",
            problem_txt.encode('utf-8')
        )

        archive.writestr(
            f"{package_name}/input.txt",
            input_txt.encode('utf-8')
        )

        archive.writestr(
            f"{package_name}/output.txt",
            output_txt.encode('utf-8')
        )

    zip_buffer.seek(0)

    filename = f"{package_name}.zip"

    return zip_buffer.getvalue(), filename