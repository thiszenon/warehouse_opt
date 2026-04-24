import pytest
from warehouse_opt.config.aisles import AisleSpec

def test_valid_aisles():
      aisles = AisleSpec(
            count = 10,
            length = 40.0,
            spacing = 5.0,
            orientation = "longitudinal"
      )
      aisles.validate()

def test_invalid_count():
      aisles = AisleSpec(
            count = 0,
            length = 40.0,
            spacing = 3.0,
            orientation = "longitudinal"
      )
      with pytest.raises(AssertionError):
            aisles.validate()

def test_invalid_spacing():
      aisles = AisleSpec(
            count = 5,
            length = 40.0,
            spacing = 0,
            orientation = "longitudinal"
      )
      with pytest.raises(AssertionError):
            aisles.validate()

def test_invalid_orientation():
      aisles = AisleSpec(
            count = 5,
            length=40.0,
            spacing =0,
            orientation = "diagonal"
      )
      with pytest.raises(AssertionError):
            aisles.validate()