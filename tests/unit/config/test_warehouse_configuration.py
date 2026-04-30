
import pytest

from warehouse_opt.config.dimensions import Dimensions
from warehouse_opt.config.aisles import AisleSpec
from warehouse_opt.config.cross_aisles import CrossAisleSpec
from warehouse_opt.config.zones import ZoneSpec
from warehouse_opt.config.warehouse import WarehouseConfiguration

# --------------------------------------------
### Helpers baseline objects
# --------------------------------------------

def valid_dimensions():
      return Dimensions(width=60, length=90, unit="meter")

#end valid_dimensions

def valid_aisles():
      return [
            AisleSpec(
                  count=10,
                  length=35,
                  spacing=3,
                  orientation="longitudinal",
                  direction = "both"
            )
      ]
#end valid_aisles
def valid_cross_aisles():
      return [
            CrossAisleSpec(position=0, aisle_type="entry"),
            CrossAisleSpec(position=45,aisle_type="middle"),
            CrossAisleSpec(position=90,aisle_type="exit")
      ]
#end valid_cross_aisles

def valid_zones():
      return [
            ZoneSpec(zone_type="start", name="Start A"),
            ZoneSpec(zone_type="end", name="End A"),
            ZoneSpec(zone_type="storage")
      ]
#end valid_zones------

# ------------------------------------------------------
# Category 1 - Baseline valid configuration
# ------------------------------------------------------

def test_valid_warehouse_configuration():
      config = WarehouseConfiguration(
            dimensions = valid_dimensions(),
            aisles = valid_aisles(),
            cross_aisles = valid_cross_aisles(),
            zones = valid_zones()
      )
      config.validate() 

# ------------------------------------------------------
# Category 2 - Structural invariants
# ------------------------------------------------------

def test_warehouse_without_aisles_is_invalid():
      config = WarehouseConfiguration(
            dimensions = valid_dimensions(),
            aisles = [],
            cross_aisles = valid_cross_aisles(),
            zones = valid_zones()
      )
      with pytest.raises(AssertionError):
            config.validate()

def test_invalid_dimensions_propagate_to_warehouse():
      bad_dimensions = Dimensions(width=0,length=90, unit="meter")
      
      config = WarehouseConfiguration(
            dimensions = bad_dimensions,
            aisles = valid_aisles(),
            cross_aisles = valid_cross_aisles(),
            zones = valid_zones()
      )
      with pytest.raises(AssertionError):
            config.validate()

# ------------------------------------------------------
# Category 3 - Functional invariants
# ------------------------------------------------------

def test_warehouse_without_start_zone_is_invalid():
      zones = [
            ZoneSpec(zone_type = "end"),
            ZoneSpec(zone_type = "storage")
      ]

      config = WarehouseConfiguration(
            dimensions = valid_dimensions(),
            aisles = valid_aisles(),
            cross_aisles = valid_cross_aisles(),
            zones = zones,
      )
      with pytest.raises(AssertionError):
            config.validate()

def test_warehouse_without_end_zone_is_invalid():
      zones = [
            ZoneSpec(zone_type = "start"),
            ZoneSpec(zone_type = "storage")
      ]
      config = WarehouseConfiguration(
            dimensions = valid_dimensions(),
            aisles = valid_aisles(),
            cross_aisles = valid_cross_aisles(),
            zones = zones
      )
      with pytest.raises(AssertionError):
            config.validate()


def test_multiple_start_and_end_zones_are_allowed():
      zones = [
            ZoneSpec(zone_type="start", name="Start A"),
            ZoneSpec(zone_type="start", name="Start B"),
            ZoneSpec(zone_type="end", name="End A"),
            ZoneSpec(zone_type="end", name="End B"),
            ZoneSpec(zone_type="storage")
      ]
      config = WarehouseConfiguration(
            dimensions = valid_dimensions(),
            aisles = valid_aisles(),
            cross_aisles = valid_cross_aisles(),
            zones = zones,
      )
      config.validate()

# ------------------------------------------------------
# Category 4 - Cross-aisle spatial invariants
# ------------------------------------------------------

def test_cross_aisle_out_of_bounds_is_invalid():
      cross_aisles = [
            CrossAisleSpec(position=95, aisle_type="exit") # > length
      ]
      config = WarehouseConfiguration(
            dimensions = valid_dimensions(),
            aisles = valid_aisles(),
            cross_aisles = cross_aisles,
            zones = valid_zones()
      )
      with pytest.raises(AssertionError):
            config.validate()

def test_cross_aisle_at_boundary_is_valid():
      cross_aisles = [
            CrossAisleSpec(position=90, aisle_type="exit") # == length
      ]

      config = WarehouseConfiguration(
            dimensions = valid_dimensions(),
            aisles = valid_aisles(),
            cross_aisles = cross_aisles,
            zones = valid_zones()
      )
      config.validate()


# ------------------------------------------------------
# Category 5 - Propagation of sub_component errors
# ------------------------------------------------------

def test_invalid_aisle_propagates_to_warehouse():
      aisles = [
            AisleSpec(
                  count=0,
                  length=30,
                  spacing=3,
                  orientation = "longitudinal"
            )
      ]

      config = WarehouseConfiguration(
            dimensions = valid_dimensions(),
            aisles = aisles,
            cross_aisles = valid_cross_aisles(),
            zones = valid_zones()
      )

      with pytest.raises(AssertionError):
            config.validate()

def test_invalid_zone_propagates_to_warehouse():
      zones = [
            ZoneSpec(zone_type="start"),
            ZoneSpec(zone_type="end"),
            ZoneSpec(zone_type = "penalty")
      ]
      config = WarehouseConfiguration(
            dimensions = valid_dimensions(),
            aisles = valid_aisles(),
            cross_aisles = valid_cross_aisles(),
            zones = zones,
      )
      with pytest.raises(AssertionError):
            config.validate()





