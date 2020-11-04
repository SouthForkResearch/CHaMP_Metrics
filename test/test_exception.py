import unittest
from lib import env
from lib.exception import *

class ExceptionTest(unittest.TestCase):

    def test_returncode(self):
        """
        test the exception return codes
        :return:
        """

        with self.assertRaises(DataException) as de:
            raise DataException("Data Exception is I")

        with self.assertRaises(NetworkException) as ne:
            raise NetworkException("Network Exception is I")

        with self.assertRaises(MissingException) as me:
            raise MissingException("Missing Exception is I")

        self.assertEqual(de.exception.returncode, 2)
        self.assertEqual(ne.exception.returncode, 3)
        self.assertEqual(me.exception.returncode, 4)