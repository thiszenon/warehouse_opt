
import pytest 
from warehouse_opt.config.cross_aisles import CrossAisleSpec


def test_valid_cross_aisle():
      crossAisle = CrossAisleSpec(
            position=20.0,
            aisle_type = "middle",
            direction="both"
      )
      crossAisle.validate()

def test_negative_position_is_invalid():
      crossAisle = CrossAisleSpec(
            position=-20.0,
            aisle_type = "entry"
      )
      with pytest.raises(AssertionError):
            crossAisle.validate()

def test_invalid_type():
      crossAisle = CrossAisleSpec(
            position=-20.0, # should fail
            aisle_type = "central"
      )
      with pytest.raises(AssertionError):
            crossAisle.validate()

def test_invalid_direction():
      crossAisle = CrossAisleSpec(
            position= 0.0,
            aisle_type = "exit",
            direction="upstream"
      )
      with pytest.raises(AssertionError):
            crossAisle.validate()