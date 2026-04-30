
from dataclasses import dataclass
from typing import List

from warehouse_opt.config.dimensions import Dimensions
from warehouse_opt.config.aisles import AisleSpec
from warehouse_opt.config.cross_aisles import CrossAisleSpec
from warehouse_opt.config.zones import ZoneSpec

@dataclass(frozen=True)
class WarehouseConfiguration:
      """
      This class aggregates all structural components of the warehouse 
      end ensures their global consistency
      """

      dimensions : Dimensions
      aisles : List[AisleSpec]
      cross_aisles: List[CrossAisleSpec]
      zones : List[ZoneSpec]

      def validate(self) -> None:
            """
            - All sub-components must be valid
            - At least one start_zone must exist
            -  At least one end_zone must exist
            - Cross-aisle positions must lie within warehouse length.
            """
            # Let validate each component

            #Validate dimensions
            self.dimensions.validate()

            assert len(self.aisles) > 0 , "warehouse must define at least one aisle group"

            # Aisles validation
            for aisle in self.aisles:
                  aisle.validate()

            #Cross Aisles validation
            for cross in self.cross_aisles:
                  cross.validate()
                  assert cross.position <= self.dimensions.length, ("cross-aisle position exceeds warehouse length")
            
            # Zone validation
            for zone in self.zones:
                  zone.validate()

            # Functional invariants
            start_zones = [zone for zone in self.zones if zone.zone_type=="start" ]
            end_zones = [zone for zone in self.zones if zone.zone_type == "end"]

            assert len(start_zones) >=1 , "at least one start zone is required"
            assert len(end_zones) >= 1 , "at least one end zone is required"
