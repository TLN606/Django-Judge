import re
from dataclasses import dataclass


@dataclass
class ImportedProblemData:

    title: str
    description: str
    input_description: str
    output_description: str
    constraints: str

    difficulty: str
    time_limit: float
    memory_limit: int

    test_cases: list[dict]


class ProblemPackageError(Exception):
    pass


# =========================================================
# FILE DECODING
# =========================================================

def decode_text(data: bytes) -> str:

    for encoding in (
        'utf-8-sig',
        'utf-8',
        'cp1258',
        'cp1252',
    ):

        try:
            return data.decode(encoding)

        except UnicodeDecodeError:
            continue

    raise ProblemPackageError(
        'Unable to decode package text files.'
    )


# =========================================================
# PROBLEM.TXT
# =========================================================

def parse_problem_file(content: str) -> dict:

    content = content.replace('\r\n', '\n').strip()

    if not content:

        raise ProblemPackageError(
            'problem.txt is empty.'
        )


    sections = {

        'DESCRIPTION': '',
        'INPUT DESCRIPTION': '',
        'OUTPUT DESCRIPTION': '',
        'CONSTRAINTS': '',
    }


    metadata = {}


    current_section = None

    buffer = []


    def save_section():

        nonlocal buffer

        if current_section is None:
            return

        sections[current_section] = (
            '\n'.join(buffer).strip()
        )

        buffer = []


    for raw_line in content.split('\n'):

        line = raw_line.strip()


        # =================================================
        # METADATA
        # =================================================

        metadata_match = re.match(
            r'^(TITLE|DIFFICULTY|TIME_LIMIT|MEMORY_LIMIT)\s*:\s*(.*)$',
            line,
            re.IGNORECASE
        )


        if metadata_match:

            save_section()

            key = metadata_match.group(1).upper()

            value = metadata_match.group(2).strip()

            metadata[key] = value

            current_section = None

            continue


        # =================================================
        # SECTION HEADER
        # =================================================

        section_match = re.match(
            r'^(DESCRIPTION|INPUT DESCRIPTION|OUTPUT DESCRIPTION|CONSTRAINTS)\s*:\s*$',
            line,
            re.IGNORECASE
        )


        if section_match:

            save_section()

            current_section = (
                section_match.group(1).upper()
            )

            continue


        # =================================================
        # CONTENT
        # =================================================

        if current_section is not None:

            buffer.append(raw_line)


    save_section()


    # =====================================================
    # REQUIRED VALUES
    # =====================================================

    title = metadata.get('TITLE', '').strip()

    if not title:

        raise ProblemPackageError(
            'TITLE is missing in problem.txt.'
        )


    difficulty = (
        metadata.get(
            'DIFFICULTY',
            'easy'
        )
        .strip()
        .lower()
    )


    if difficulty not in {
        'easy',
        'medium',
        'hard',
    }:

        raise ProblemPackageError(
            'DIFFICULTY must be easy, medium, or hard.'
        )


    try:

        time_limit = float(
            metadata.get(
                'TIME_LIMIT',
                '1'
            )
        )

    except ValueError:

        raise ProblemPackageError(
            'TIME_LIMIT must be a number.'
        )


    if time_limit <= 0:

        raise ProblemPackageError(
            'TIME_LIMIT must be greater than 0.'
        )


    try:

        memory_limit = int(
            metadata.get(
                'MEMORY_LIMIT',
                '256'
            )
        )

    except ValueError:

        raise ProblemPackageError(
            'MEMORY_LIMIT must be an integer.'
        )


    if memory_limit <= 0:

        raise ProblemPackageError(
            'MEMORY_LIMIT must be greater than 0.'
        )


    return {

        'title': title,

        'description':
            sections['DESCRIPTION'],

        'input_description':
            sections['INPUT DESCRIPTION'],

        'output_description':
            sections['OUTPUT DESCRIPTION'],

        'constraints':
            sections['CONSTRAINTS'],

        'difficulty':
            difficulty,

        'time_limit':
            time_limit,

        'memory_limit':
            memory_limit,
    }


# =========================================================
# TEST CASE FILES
# =========================================================

TEST_CASE_PATTERN = re.compile(
    r'^\s*\[TESTCASE\s+(\d+)\]\s*$',
    re.IGNORECASE | re.MULTILINE
)


def parse_test_cases_file(
    content: str,
    file_name: str,
    expected_count: int,
) -> list[str]:

    content = content.replace(
        '\r\n',
        '\n'
    )


    if not content.strip():

        raise ProblemPackageError(
            f'{file_name} is empty.'
        )


    lines = content.split('\n')


    # =====================================================
    # FIRST LINE = NUMBER OF TEST CASES
    # =====================================================

    count_index = None

    for index, line in enumerate(lines):

        if line.strip():

            count_index = index

            break


    if count_index is None:

        raise ProblemPackageError(
            f'{file_name} does not contain test case count.'
        )


    try:

        declared_count = int(
            lines[count_index].strip()
        )

    except ValueError:

        raise ProblemPackageError(
            f'The first non-empty line of {file_name} '
            f'must be the number of test cases.'
        )


    if declared_count != expected_count:

        raise ProblemPackageError(
            f'{file_name} declares {declared_count} '
            f'test cases, but problem package expects '
            f'{expected_count}.'
        )


    body = '\n'.join(
        lines[count_index + 1:]
    )


    # =====================================================
    # MARKER FORMAT
    # =====================================================

    marker_matches = list(
        TEST_CASE_PATTERN.finditer(body)
    )


    if marker_matches:

        cases = []


        for index, match in enumerate(marker_matches):

            marker_number = int(
                match.group(1)
            )


            expected_marker = index + 1


            if marker_number != expected_marker:

                raise ProblemPackageError(
                    f'{file_name}: expected '
                    f'[TESTCASE {expected_marker}] '
                    f'but found '
                    f'[TESTCASE {marker_number}].'
                )


            start = match.end()


            if index + 1 < len(marker_matches):

                end = marker_matches[
                    index + 1
                ].start()

            else:

                end = len(body)


            case_content = body[
                start:end
            ].strip()


            cases.append(
                case_content
            )


        if len(cases) != expected_count:

            raise ProblemPackageError(
                f'{file_name} contains '
                f'{len(cases)} test case blocks, '
                f'expected {expected_count}.'
            )


        return cases


    # =====================================================
    # SIMPLE ONE-LINE FORMAT
    # =====================================================

    raw_cases = body.split('\n')

    cases = [

        line.strip()

        for line in raw_cases

        if line.strip()

    ]


    if len(cases) != expected_count:

        raise ProblemPackageError(
            f'{file_name} contains '
            f'{len(cases)} data lines, '
            f'expected {expected_count}. '
            f'For multi-line test cases, use '
            f'[TESTCASE N] markers.'
        )


    return cases


# =========================================================
# PACKAGE VALIDATION
# =========================================================

def validate_package(
    problem_content: bytes,
    input_content: bytes,
    output_content: bytes,
) -> ImportedProblemData:

    problem_text = decode_text(
        problem_content
    )

    input_text = decode_text(
        input_content
    )

    output_text = decode_text(
        output_content
    )


    problem_data = parse_problem_file(
        problem_text
    )


    # Get number of test cases
    first_non_empty_line = None


    for line in input_text.splitlines():

        if line.strip():

            first_non_empty_line = line.strip()

            break


    if first_non_empty_line is None:

        raise ProblemPackageError(
            'input.txt does not contain test case count.'
        )


    try:

        test_case_count = int(
            first_non_empty_line
        )

    except ValueError:

        raise ProblemPackageError(
            'input.txt first line must be an integer.'
        )


    if test_case_count <= 0:

        raise ProblemPackageError(
            'Problem package must contain at least one test case.'
        )


    inputs = parse_test_cases_file(
        input_text,
        'input.txt',
        test_case_count
    )


    outputs = parse_test_cases_file(
        output_text,
        'output.txt',
        test_case_count
    )


    if len(inputs) != len(outputs):

        raise ProblemPackageError(
            'Number of input and output test cases does not match.'
        )


    test_cases = []


    for index, (
        input_data,
        expected_output
    ) in enumerate(
        zip(inputs, outputs),
        start=1
    ):

        if not expected_output.strip():

            raise ProblemPackageError(
                f'Test Case {index} has empty expected output.'
            )


        test_cases.append({

            'input_data':
                input_data,

            'expected_output':
                expected_output,

            'is_sample':
                index == 1,
        })


    return ImportedProblemData(

        title=problem_data['title'],

        description=problem_data['description'],

        input_description=
            problem_data['input_description'],

        output_description=
            problem_data['output_description'],

        constraints=
            problem_data['constraints'],

        difficulty=
            problem_data['difficulty'],

        time_limit=
            problem_data['time_limit'],

        memory_limit=
            problem_data['memory_limit'],

        test_cases=
            test_cases,
    )