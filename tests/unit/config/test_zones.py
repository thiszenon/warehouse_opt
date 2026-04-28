
import pytest
from warehouse_opt.config.zones import ZoneSpec

def test_valid_start_zone():
      zone = ZoneSpec(
            zone_type="start",
            name="Picking start"
      )
      zone.validate()

def test_valid_end_zone():
      zone = ZoneSpec(
            zone_type="end"
      )
      zone.validate()

def test_valid_storage_zone():
      zone = ZoneSpec(zone_type="storage")
      zone.validate()

def test_valid_penalty_zone():
      zone = ZoneSpec(
            zone_type = "penalty",
            penalty_factor=1.5
      )
      zone.validate()

def test_no_penalty_zone_with_factor_is_invalid():
      zone = ZoneSpec(
            zone_type = "storage",
            penalty_factor=1.3
      )
      with pytest.raises(AssertionError):
            zone.validate()

def test_penalty_factor_must_be_greater_than_one():
      zone = ZoneSpec(
            zone_type = "penalty",
            penalty_factor =  1.0
      )
      with pytest.raises(AssertionError):
            zone.validate()

def test_invalid_zone_type():
      zone = ZoneSpec(
            zone_type = "campus"
      )
      with pytest.raises(AssertionError):
            zone.validate()
      