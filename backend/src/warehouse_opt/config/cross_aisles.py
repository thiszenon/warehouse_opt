
from dataclasses import dataclass
from typing import Literal

CrossAisleType = Literal["entry","middle","exit"]
Direction = Literal["both","forward","backward"]

@dataclass(frozen=True)
class CrossAisleSpec:
      """
      Specification of a cross-aisle.

      A cross-aisle connects longitudinal or transverse aisles and
      allows switching between them. 
      """
      position: float 
      aisle_type : CrossAisleType
      direction : Direction = "both"

      def validate(self) -> None:
            assert self.position >= 0, "cross-aisle position must be non-negative"
            assert self.aisle_type in ("entry", "middle","exit"),("Invalid cross-aisle type")
            assert self.direction in ("both","forward","backward"), ("Invalid cross-aisle direction")
      #end validate
#end CrossAisleSpec

