
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import yaml

@dataclass
class ReceiverConfig:
    eta_r: float = 0.9
    area_m2: float = 1e-6
    responsivity_A_per_W: float = 0.5
    fov_deg: float = 30.0
    n_lens: float = 1.5
    T: float = 300.0
    R_load: float = 50.0
    Idark_A: float = 1e-9
    bandwidth_Hz: float = 1e6

@dataclass
class TransmitterConfig:
    eta_t: float = 0.9
    power_W: float = 1.0
    wavelength_nm: float = 520.0
    led_theta_half_deg: float = 60.0
    led_divergence_deg: float = 30.0
    ld_divergence_deg: float = 9.0
    g_tx: float = 1.0

@dataclass
class WaterConfig:
    name: str
    alpha_m_inv: float
    beta_m_inv: float

    @property
    def c_m_inv(self) -> float:
        return self.alpha_m_inv + self.beta_m_inv

@dataclass
class TurbulenceConfig:
    model: str = "lognormal"
    scint_index: float = 0.1
    gg_alpha: float = 1.0
    gg_beta: float = 2.0
    gg_nu: float = 1.0
    wb_k: float = 1.2
    wb_lambda: float = 1.0

@dataclass
class NoiseConfig:
    rin: float = 0.0

@dataclass
class SimulationGrid:
    d_min_m: float = 1.0
    d_max_m: float = 100.0
    d_step_m: float = 1.0
    mc_realizations: int = 1
    seed: Optional[int] = 12345

@dataclass
class SimulationConfig:
    transmitter: TransmitterConfig
    receiver: ReceiverConfig
    water: WaterConfig
    turb: TurbulenceConfig
    noise: NoiseConfig
    grid: SimulationGrid
    tx_type: str = "led"

    @staticmethod
    def from_yaml(path: str) -> "SimulationConfig":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        def ld(cls, src, key, defaults):
            d = src.get(key, {}) if src else {}
            merged = {**asdict(defaults), **d}
            return cls(**merged)
        tx = ld(TransmitterConfig, data, "transmitter", TransmitterConfig())
        rx = ld(ReceiverConfig, data, "receiver", ReceiverConfig())
        grid = ld(SimulationGrid, data, "grid", SimulationGrid())
        turb = ld(TurbulenceConfig, data, "turbulence", TurbulenceConfig())
        noise = ld(NoiseConfig, data, "noise", NoiseConfig())
        w = data.get("water", {})
        water = WaterConfig(**w)
        tx_type = data.get("tx_type", "led")
        return SimulationConfig(tx, rx, water, turb, noise, grid, tx_type)
