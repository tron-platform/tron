
import pytest
from unittest.mock import MagicMock
from app.shared.serializers.serializers import serialize_settings

def test_serialize_settings():

    mock_settings = MagicMock()

    mock_settings.key = "disable_workload"
    mock_settings.value = "true"

    result = serialize_settings([mock_settings])

    expected_result = {
        "disable_workload": "true",
    }

    assert result == expected_result
