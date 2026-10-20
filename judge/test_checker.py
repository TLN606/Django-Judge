from django.test import SimpleTestCase

from judge.checker import OutputChecker


class OutputCheckerTests(SimpleTestCase):

    def setUp(self):
        self.checker = OutputChecker()

    def test_equal_output_is_accepted(self):
        result = self.checker.check('30', '30')
        self.assertTrue(result.accepted)
        self.assertEqual(result.message, 'Accepted')

    def test_trailing_whitespace_and_newline_are_ignored(self):
        self.assertTrue(self.checker.check('30', '30\n').accepted)
        self.assertTrue(self.checker.check('30\n', '  30  \n\n').accepted)

    def test_different_output_is_wrong_answer(self):
        result = self.checker.check('30', '25\n')
        self.assertFalse(result.accepted)
        self.assertEqual(result.message, 'Wrong Answer')

    def test_empty_output_is_wrong_when_answer_expected(self):
        self.assertFalse(self.checker.check('1', '').accepted)
