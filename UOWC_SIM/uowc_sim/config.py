
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class PipeTIRConfig:
    enabled: bool = False
    radius_m: float = 0.02
    wall_reflectivity: float = 0.95
    water_refractive_index: float = 1.333
    wall_refractive_index: float = 1.0
    incidence_axis_deg: Optional[float] = None
    coupling_efficiency: float = 0.85
    max_guiding_gain: float = 50.0

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
    tia_gain: float = 1.0
    baseline_offset_V: float = 0.0
    comparator_low_V: float = 0.0
    comparator_high_V: float = 3.3
    psoc_logic_high_threshold_V: float = 1.65

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
    d_min_m: float = 0.2
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
    pipe_tir: PipeTIRConfig = field(default_factory=PipeTIRConfig)
    tx_type: str = "led"

    @staticmethod
    def from_yaml(path: str) -> "SimulationConfig":
        cfg_path = Path(path)
        if not cfg_path.exists():
            module_root = Path(__file__).resolve().parents[1]
            project_root_candidate = module_root.parent
            path_options = [
                module_root / path,
                project_root_candidate / path,
                module_root / "configs" / cfg_path.name,
                project_root_candidate / "UOWC_SIM" / "configs" / cfg_path.name,
            ]
            cfg_path = next((p for p in path_options if p.exists()), cfg_path)
        with open(cfg_path, "r", encoding="utf-8") as f:
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
        pipe_tir = ld(PipeTIRConfig, data, "pipe_tir", PipeTIRConfig())
        w = data.get("water", {})
        water = WaterConfig(**w)
        tx_type = data.get("tx_type", "led")
        return SimulationConfig(tx, rx, water, turb, noise, grid, pipe_tir, tx_type)
