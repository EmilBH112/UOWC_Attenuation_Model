
import math, random

def rng(seed=None):
    r = random.Random()
    if seed is not None:
        r.seed(seed)
    return r

def sample_lognormal(scint_index: float, mean_I: float, r: random.Random) -> float:
    # Sample log-normal turbulence factor Fturb so that E[I]=mean_I; use scintillation index to set variance.
    sigma_I2 = max(0.0, scint_index)
    sigma_X2 = math.log(1.0 + sigma_I2)
    mu_x = math.log(max(1e-30, mean_I)) - 0.5 * sigma_X2
    x = r.gauss(mu_x, math.sqrt(sigma_X2))
    return math.exp(x) / max(1e-30, mean_I)

def sample_gengamma(alpha: float, beta: float, nu: float, r: random.Random) -> float:
    # Sample from generalized-gamma (scale alpha, shape beta, exponent nu). Return multiplicative factor Fturb.
    k = beta / max(1e-12, nu)
    theta = (alpha ** nu)
    Y = r.gammavariate(k, theta)
    I = (Y ** (1.0 / max(1e-12, nu)))
    # Approximate normalization using gamma-moment.
    p = 1.0 / max(1e-12, nu)
    E_Yp = (theta ** p) * math.gamma(k + p) / math.gamma(k)
    E_I = (E_Yp) ** (1.0 / max(1e-12, nu))
    return I / max(1e-30, E_I)

def sample_weibull(k: float, lam: float, r: random.Random) -> float:
    # Sample Weibull(k, lambda) and normalize by its mean to get Fturb with E=1.
    U = max(1e-12, min(1-1e-12, r.random()))
    I = lam * ((-math.log(1.0 - U)) ** (1.0 / max(1e-12, k)))
    mean = lam * math.gamma(1.0 + 1.0 / max(1e-12, k))
    return I / max(1e-30, mean)

def draw_fturb(model: str, params: dict, r: random.Random) -> float:
    m = model.lower()
    if m == "lognormal":
        return sample_lognormal(params.get("scint_index", 0.1), mean_I=1.0, r=r)
    if m == "gengamma":
        return sample_gengamma(params.get("gg_alpha",1.0), params.get("gg_beta",2.0), params.get("gg_nu",1.0), r)
    if m == "weibull":
        return sample_weibull(params.get("wb_k",1.2), params.get("wb_lambda",1.0), r)
    return 1.0
