import pytest
from pytest_bdd import scenarios

pytestmark = pytest.mark.integration

scenarios("features/bedside_lamp.feature")
