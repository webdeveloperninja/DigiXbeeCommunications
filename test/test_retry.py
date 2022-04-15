import unittest
import sys
from unittest.mock import MagicMock

sys.path.insert(0, '../')

from retry import try_or_retry_times


class TestRetry(unittest.TestCase):
    def raise_exception(self):
        raise Exception("Test")

    def test_should_retry_n_times_and_raise_exception(self):
        mock = MagicMock()
        mock.side_effect = self.raise_exception

        def should_raise_exception():
            try_or_retry_times(mock, 3, 1)

        self.assertRaises(Exception, should_raise_exception)
        self.assertEqual(mock.call_count, 3)


if __name__ == '__main__':
    unittest.main()
