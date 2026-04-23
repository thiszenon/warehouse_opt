import pytest 
from warehouse_opt.config.dimensions import Dimensions 

def test_dimensions_valid():
      dims = Dimensions(width=50,length =90,unit="meter")
      dims.validate()

def test_width_must_be_positive():
      dims = Dimensions(width=0, length=50)
      with pytest.raises(AssertionError):
            dims.validate()

def test_length_must_be_positive():
      dims = Dimensions(width=50,length =-10)
      with pytest.raises(AssertionError):
            dims.validate()

def test_invalid_unit():
      dims = Dimensions(width=50, length =30,unit="km")
      with pytest.raises(AssertionError):
            dims.validate()

