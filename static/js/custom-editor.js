document.addEventListener('DOMContentLoaded', function () {

    const textarea = document.getElementById('sourceCodeInput');
    const highlight = document.getElementById('syntaxHighlight');
    const lineNumbers = document.getElementById('lineNumbers');

    const languageSelect =
    document.getElementById('languageSelect');

    const filename = document.querySelector(
        '.submission-code-filename'
    );

    if (!textarea || !highlight || !lineNumbers) {
        console.error('MiniJudge: editor elements not found.');
        return;
    }


    /* =========================================================
       HTML ESCAPE
    ========================================================= */

    function escapeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }


    /* =========================================================
       CREATE TOKEN
    ========================================================= */

    function span(className, text) {
        return '<span class="' + className + '">' +
            escapeHtml(text) +
            '</span>';
    }


    /* =========================================================
       C++ HIGHLIGHTER
       Single-pass lexer
    ========================================================= */

    function highlightCpp(code) {

        let result = '';
        let i = 0;

        const keywords = new Set([
            'if',
            'else',
            'for',
            'while',
            'do',
            'switch',
            'case',
            'default',
            'break',
            'continue',
            'return',
            'class',
            'struct',
            'public',
            'private',
            'protected',
            'new',
            'delete',
            'using',
            'namespace',
            'try',
            'catch',
            'throw',
            'static',
            'virtual',
            'override',
            'template',
            'typename',
            'this'
        ]);

        const types = new Set([
            'int',
            'long',
            'short',
            'float',
            'double',
            'char',
            'bool',
            'void',
            'auto',
            'size_t',
            'string',
            'const',
            'unsigned',
            'signed'
        ]);

        const builtins = new Set([
            'cout',
            'cin',
            'cerr',
            'endl',
            'std'
        ]);

        const booleans = new Set([
            'true',
            'false',
            'nullptr'
        ]);


        while (i < code.length) {

            /* -----------------------------------------------
               // COMMENT
            ----------------------------------------------- */

            if (
                code[i] === '/' &&
                code[i + 1] === '/'
            ) {

                let end = code.indexOf('\n', i);

                if (end === -1) {
                    end = code.length;
                }

                result += span(
                    'mj-code-comment',
                    code.substring(i, end)
                );

                i = end;

                continue;
            }


            /* -----------------------------------------------
               /* COMMENT
            ----------------------------------------------- */

            if (
                code[i] === '/' &&
                code[i + 1] === '*'
            ) {

                let end = code.indexOf(
                    '*/',
                    i + 2
                );

                if (end === -1) {
                    end = code.length - 2;
                }

                end += 2;

                result += span(
                    'mj-code-comment',
                    code.substring(i, end)
                );

                i = end;

                continue;
            }


            /* -----------------------------------------------
               STRING
            ----------------------------------------------- */

            if (code[i] === '"') {

                let j = i + 1;

                while (j < code.length) {

                    if (code[j] === '\\') {
                        j += 2;
                        continue;
                    }

                    if (code[j] === '"') {
                        j++;
                        break;
                    }

                    j++;
                }

                result += span(
                    'mj-code-string',
                    code.substring(i, j)
                );

                i = j;

                continue;
            }


            /* -----------------------------------------------
               CHARACTER
            ----------------------------------------------- */

            if (code[i] === "'") {

                let j = i + 1;

                while (j < code.length) {

                    if (code[j] === '\\') {
                        j += 2;
                        continue;
                    }

                    if (code[j] === "'") {
                        j++;
                        break;
                    }

                    j++;
                }

                result += span(
                    'mj-code-string',
                    code.substring(i, j)
                );

                i = j;

                continue;
            }


            /* -----------------------------------------------
               PREPROCESSOR
            ----------------------------------------------- */

            if (
                code[i] === '#' &&
                (
                    i === 0 ||
                    code[i - 1] === '\n'
                )
            ) {

                let end = code.indexOf('\n', i);

                if (end === -1) {
                    end = code.length;
                }

                result += span(
                    'mj-code-preprocessor',
                    code.substring(i, end)
                );

                i = end;

                continue;
            }


            /* -----------------------------------------------
               NUMBER
            ----------------------------------------------- */

            if (/[0-9]/.test(code[i])) {

                let j = i;

                while (
                    j < code.length &&
                    /[A-Za-z0-9._]/.test(code[j])
                ) {
                    j++;
                }

                result += span(
                    'mj-code-number',
                    code.substring(i, j)
                );

                i = j;

                continue;
            }


            /* -----------------------------------------------
               IDENTIFIER
            ----------------------------------------------- */

            if (
                /[A-Za-z_]/.test(code[i])
            ) {

                let j = i + 1;

                while (
                    j < code.length &&
                    /[A-Za-z0-9_]/.test(code[j])
                ) {
                    j++;
                }

                const word =
                    code.substring(i, j);


                if (types.has(word)) {

                    result += span(
                        'mj-code-type',
                        word
                    );

                }

                else if (keywords.has(word)) {

                    result += span(
                        'mj-code-keyword',
                        word
                    );

                }

                else if (builtins.has(word)) {

                    result += span(
                        'mj-code-builtin',
                        word
                    );

                }

                else if (booleans.has(word)) {

                    result += span(
                        'mj-code-boolean',
                        word
                    );

                }

                else {

                    /*
                     * Nếu sau identifier là '('
                     * thì coi là function.
                     */

                    let k = j;

                    while (
                        k < code.length &&
                        /\s/.test(code[k])
                    ) {
                        k++;
                    }

                    if (code[k] === '(') {

                        result += span(
                            'mj-code-function',
                            word
                        );

                    } else {

                        result += escapeHtml(word);

                    }
                }

                i = j;

                continue;
            }


            /* -----------------------------------------------
               OPERATORS
            ----------------------------------------------- */

            const twoChar =
                code.substring(i, i + 2);

            const threeChar =
                code.substring(i, i + 3);

            if (
                threeChar === '>>=' ||
                threeChar === '<<='
            ) {

                result += span(
                    'mj-code-operator',
                    threeChar
                );

                i += 3;

                continue;
            }


            if (
                [
                    '<<',
                    '>>',
                    '==',
                    '!=',
                    '<=',
                    '>=',
                    '++',
                    '--',
                    '&&',
                    '||',
                    '->',
                    '+=',
                    '-=',
                    '*=',
                    '/=',
                    '%='
                ].includes(twoChar)
            ) {

                result += span(
                    'mj-code-operator',
                    twoChar
                );

                i += 2;

                continue;
            }


            if (
                '+-*/%=<>!&|'
                    .includes(code[i])
            ) {

                result += span(
                    'mj-code-operator',
                    code[i]
                );

                i++;

                continue;
            }


            /* -----------------------------------------------
               NORMAL CHARACTER
            ----------------------------------------------- */

            result += escapeHtml(code[i]);

            i++;
        }


        return result;
    }


    /* =========================================================
       PYTHON
    ========================================================= */

    function highlightPython(code) {

        let result = '';
        let i = 0;

        const keywords = new Set([
            'def',
            'return',
            'if',
            'else',
            'elif',
            'for',
            'while',
            'in',
            'import',
            'from',
            'as',
            'class',
            'try',
            'except',
            'finally',
            'with',
            'lambda',
            'pass',
            'break',
            'continue',
            'and',
            'or',
            'not',
            'is'
        ]);

        const builtins = new Set([
            'print',
            'len',
            'range',
            'input',
            'int',
            'float',
            'str',
            'list',
            'dict',
            'set',
            'tuple'
        ]);

        while (i < code.length) {

            /* Comment */

            if (code[i] === '#') {

                let end = code.indexOf('\n', i);

                if (end === -1) {
                    end = code.length;
                }

                result += span(
                    'mj-code-comment',
                    code.substring(i, end)
                );

                i = end;

                continue;
            }


            /* String */

            if (
                code[i] === '"' ||
                code[i] === "'"
            ) {

                const quote = code[i];

                let j = i + 1;

                while (j < code.length) {

                    if (code[j] === '\\') {
                        j += 2;
                        continue;
                    }

                    if (code[j] === quote) {
                        j++;
                        break;
                    }

                    j++;
                }

                result += span(
                    'mj-code-string',
                    code.substring(i, j)
                );

                i = j;

                continue;
            }


            /* Number */

            if (/[0-9]/.test(code[i])) {

                let j = i;

                while (
                    j < code.length &&
                    /[A-Za-z0-9._]/.test(code[j])
                ) {
                    j++;
                }

                result += span(
                    'mj-code-number',
                    code.substring(i, j)
                );

                i = j;

                continue;
            }


            /* Identifier */

            if (/[A-Za-z_]/.test(code[i])) {

                let j = i + 1;

                while (
                    j < code.length &&
                    /[A-Za-z0-9_]/.test(code[j])
                ) {
                    j++;
                }

                const word =
                    code.substring(i, j);


                if (
                    word === 'True' ||
                    word === 'False' ||
                    word === 'None'
                ) {

                    result += span(
                        'mj-code-boolean',
                        word
                    );

                }

                else if (keywords.has(word)) {

                    result += span(
                        'mj-code-keyword',
                        word
                    );

                }

                else if (builtins.has(word)) {

                    result += span(
                        'mj-code-builtin',
                        word
                    );

                }

                else {

                    let k = j;

                    while (
                        k < code.length &&
                        /\s/.test(code[k])
                    ) {
                        k++;
                    }

                    if (code[k] === '(') {

                        result += span(
                            'mj-code-function',
                            word
                        );

                    } else {

                        result += escapeHtml(word);

                    }
                }

                i = j;

                continue;
            }


            /* Operators */

            if (
                '+-*/%=<>!&|'
                    .includes(code[i])
            ) {

                result += span(
                    'mj-code-operator',
                    code[i]
                );

                i++;

                continue;
            }


            result += escapeHtml(code[i]);

            i++;
        }

        return result;
    }


    /* =========================================================
       UPDATE
    ========================================================= */

    function updateHighlight() {

        const code = textarea.value || '';

        const language =
            languageSelect
                ? languageSelect.value
                : 'cpp';


        if (language === 'python') {

            highlight.innerHTML =
                highlightPython(code);

        } else {

            highlight.innerHTML =
                highlightCpp(code);

        }


        updateLineNumbers();

        syncScroll();
    }


    /* =========================================================
       LINE NUMBERS
    ========================================================= */

    function updateLineNumbers() {

        const count =
            (textarea.value || '')
                .split('\n')
                .length;

        let html = '';

        for (let i = 1; i <= count; i++) {

            html +=
                '<span>' + i + '</span>';

        }

        lineNumbers.innerHTML = html;
    }


    /* =========================================================
       SCROLL
    ========================================================= */

    function syncScroll() {

        highlight.scrollTop =
            textarea.scrollTop;

        highlight.scrollLeft =
            textarea.scrollLeft;

        lineNumbers.scrollTop =
            textarea.scrollTop;
    }


    /* =========================================================
       INPUT
    ========================================================= */

    textarea.addEventListener(
        'input',
        updateHighlight
    );


    /* =========================================================
       SCROLL
    ========================================================= */

    textarea.addEventListener(
        'scroll',
        syncScroll
    );


    /* =========================================================
       TAB
    ========================================================= */

    textarea.addEventListener(
        'keydown',
        function (event) {

            if (event.key !== 'Tab') {
                return;
            }

            event.preventDefault();

            const start =
                textarea.selectionStart;

            const end =
                textarea.selectionEnd;

            textarea.value =
                textarea.value.substring(0, start) +
                '    ' +
                textarea.value.substring(end);

            textarea.selectionStart =
                textarea.selectionEnd =
                    start + 4;

            updateHighlight();
        }
    );


    /* =========================================================
       LANGUAGE
    ========================================================= */

    if (languageSelect) {

        languageSelect.addEventListener(
            'change',
            function () {

                if (filename) {

                    filename.textContent =
                        languageSelect.value === 'python'
                            ? 'solution.py'
                            : 'solution.cpp';
                }

                updateHighlight();
            }
        );
    }


    /* =========================================================
       INITIAL
    ========================================================= */

    updateHighlight();

});