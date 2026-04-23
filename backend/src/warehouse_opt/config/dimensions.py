
from dataclasses import dataclass
from typing import Literal
Unit = Literal["meter","cell"]

@dataclass(frozen=True)
class Dimensions:
      """
      General dimensions of the warehouse (2D space).
      
      This class defines the ground-level spatial domain in witch
      all other warehouse elements (aisles, zones, nodes, paths) must be valid
      """

      width: float
      length: float
      unit:Unit = "meter"

      def validate(self) -> None:
            assert self.width > 0, "width must be strictly positive"
            assert self.length > 0, "length must be strictly positive"
            assert self.unit in ("meter", "cell"), "invalid unit"
      #end of validate
#end of class Dimensions


            