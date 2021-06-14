from typing import List

from pytest import fixture
from tests import facade


class TestCase:
    @fixture
    def setup_test_case(self):
        pass


def assert_errors(left: List[facade.EnviumError], right: List[facade.EnviumError]):
    assert [repr(e) for e in left] == [repr(e) for e in right]
