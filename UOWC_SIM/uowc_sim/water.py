
from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class WaterMedium:
    name: str
    alpha_m_inv: float
    beta_m_inv: float

    @property
    def c_m_inv(self) -> float:
        return self.alpha_m_inv + self.beta_m_inv

# Table 3 at lambda = 520 nm
PRESETS_520NM: Dict[str, WaterMedium] = {
    "pure_sea": WaterMedium("pure_sea", alpha_m_inv=0.04418,  beta_m_inv=0.0009092),
    "clear_ocean": WaterMedium("clear_ocean", alpha_m_inv=0.08642, beta_m_inv=0.01226),
    "coastal_ocean": WaterMedium("coastal_ocean", alpha_m_inv=0.2179,  beta_m_inv=0.09966),
    "turbid_harbor": WaterMedium("turbid_harbor", alpha_m_inv=1.112,   beta_m_inv=0.5266),
}
