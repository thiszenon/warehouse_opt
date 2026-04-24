
from dataclasses import dataclass
from typing import Literal

Orientation = Literal["longitudinal","transverse"]
Direction = Literal["both","forward", "backward"]

@dataclass(frozen=True)
class AisleSpec:
      """
      Specification of warehouse aisles.

      This class describes a regular set of parallel aisles embedded in a 2D warehouse space.
      """
      count: int 
      length: float
      spacing: float
      orientation: Orientation
      direction: Direction = "forward"

      def validate(self) -> None:
            assert self.count > 0, "aisle count must be strictly positive"
            assert self.length > 0, "aisle length must be strictly positive"
            assert self.spacing > 0, "aisle spacing must be strictly positive"
            assert self.orientation in ("longitudinal","transverse"), ("invalid aisle orientation")
            assert self.direction in ("both", "forward", "backward"), ("invalid aisle direction")
      #end of validate 
#end of AisleSpec
