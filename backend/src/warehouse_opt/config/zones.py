
from dataclasses import dataclass
from typing import Literal, Optional

ZoneType = Literal[
      "start",
      "end",
      "storage",
      "forbidden",
      "penalty",
      "service",
]

@dataclass(frozen=True)
class ZoneSpec:
      """
      Functional zone specification within a warehouse.
      This class represents a functional constraint applied to a portion
      of the warehouse space.
      """
      zone_type : ZoneType
      name: Optional[str] = None
      penalty_factor: Optional[float] = None 

      def validate(self) -> None:
            assert self.zone_type in (
                  "start",
                  "end",
                  "storage",
                  "forbidden",
                  "penalty",
                  "service",
            ), "Invalid zone type"

            if self.zone_type == "penalty":
                  assert self.penalty_factor is not None, ("penalty zone must define a penalty_factor")
                  assert self.penalty_factor > 1.0, ("penalty_factor must be strictly greater thant 1")
            else:
                  assert self.penalty_factor is None , ("penalty_factor is only allowed for penalty zones")

