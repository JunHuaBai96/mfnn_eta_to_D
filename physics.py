# -*- coding: utf-8 -*-
"""
physics.py
Chen et al. (Phil. Mag., 2014) / Tang et al. (CALPHAD, 2015) formulas:
1. Temperature-dependent effective hard-sphere radius r_i(T)
2. Kaptay pure-metal viscosity
3. Kozlov alloy viscosity
4. Modified Sutherland / Stokes-Einstein with beta boundary criterion
Numeric values are literature constants or order-of-magnitude helpers for
the analytic LF prior; they are not experimental measurements.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Union
import numpy as np
import torch

K_BOLTZMANN: float = 1.380649e-23  # J/K
N_AVOGADRO: float = 6.02214076e23  # 1/mol
R_GAS: float = 8.314462618         # J/(mol·K)
PACKING_FRACTION_F: float = 0.45   # Chen 2014 Eq. (8)

KAPTAY_C1: float = 1.80e-8         # (J K^-1 mol^-1/3)^0.5 scale
KAPTAY_C2: float = 2.34            # dimensionless in Kaptay form

# Approximate molar volumes / melting points (SI units)
# V_m in m^3/mol, T_m in K, M in kg/mol — order-of-magnitude for Al-based melts.
ELEMENT_PROPS: Dict[str, Dict[str, float]] = {
    "Al": {"V_m": 1.13e-5, "T_m": 933.0, "M": 0.02698, "r0": 1.43e-10},
    "Cu": {"V_m": 7.94e-6, "T_m": 1358.0, "M": 0.06355, "r0": 1.28e-10},
    "Ce": {"V_m": 2.10e-5, "T_m": 1071.0, "M": 0.14012, "r0": 1.82e-10},
    "Ni": {"V_m": 7.30e-6, "T_m": 1728.0, "M": 0.05869, "r0": 1.24e-10},
    "Ag": {"V_m": 1.15e-5, "T_m": 1235.0, "M": 0.10787, "r0": 1.44e-10},
    "Mg": {"V_m": 1.48e-5, "T_m": 923.0, "M": 0.02431, "r0": 1.60e-10},
    "Si": {"V_m": 1.20e-5, "T_m": 1687.0, "M": 0.02809, "r0": 1.32e-10},
}


def effective_radius_ri(T: float, species: str, f: float = PACKING_FRACTION_F) -> float:
    """Effective hard-sphere radius r_i(T) ~ Chen 2014 Eq. (8) / Tang 2015 Eq. (6).

    r_i(T) = (3 V_m / (4 pi N_A))^(1/3) * (f * T_m / T)^(1/3)
    following Chen et al., Phil. Mag. 94, 1552 (2014), Eq. (8).
    """
    props = ELEMENT_PROPS.get(species, ELEMENT_PROPS["Al"])
    V_m = props["V_m"]
    T_m = props["T_m"]
    base = (3.0 * V_m / (4.0 * np.pi * N_AVOGADRO)) ** (1.0 / 3.0)
    return float(base * ((f * T_m / max(T, 1.0)) ** (1.0 / 3.0)))


# Assael et al., J. Phys. Chem. Ref. Data 35, 285–300 (2006), DOI:10.1063/1.2149380
# Recommended reference correlation for liquid Al viscosity:
#   log10(η / mPa·s) = -0.7324 + 803.49 / T   (T in K)
# Validity cited ~933–1270 K (NIST summary often lists 950–1200 K); ±~14% absolute.
# Constants also quoted in Chen et al. Phil. Mag. 2014 Eq.(1) citing Assael [24].
ASSAEL_AL_A1: float = 0.7324
ASSAEL_AL_A2: float = 803.49  # K
ASSAEL_AL_T_MIN: float = 933.0
ASSAEL_AL_T_MAX: float = 1270.0


def assael_pure_al_viscosity(T: float) -> float:
    """Assael 2006 recommended liquid Al viscosity in Pa·s.

    Returns η [Pa·s]. Does not invent alloy viscosities — pure Al only.
    Outside [933, 1270] K the same formula is an extrapolation; callers should tag it.
    """
    T = float(T)
    if T <= 0:
        raise ValueError(f"T must be positive, got {T}")
    log10_mPa = -ASSAEL_AL_A1 + ASSAEL_AL_A2 / T
    return float((10.0 ** log10_mPa) * 1e-3)


def kaptay_pure_viscosity(T: float, species: str) -> float:
    """Kaptay pure liquid metal viscosity — Chen 2014 Eq. (2a) schematic.

    eta = C1 * M^(1/2) / V_m^(2/3) * T^(1/2) * exp(C2 * T_m / T)
    """
    props = ELEMENT_PROPS.get(species, ELEMENT_PROPS["Al"])
    M, V_m, T_m = props["M"], props["V_m"], props["T_m"]
    pre = KAPTAY_C1 * (M ** 0.5) / (V_m ** (2.0 / 3.0))
    return float(pre * (T ** 0.5) * np.exp(KAPTAY_C2 * T_m / max(T, 1.0)))


def kozlov_alloy_viscosity(
    T: float,
    mole_fractions: Dict[str, float],
    DeltaH_mix: float = 0.0,
) -> float:
    """Kozlov alloy viscosity — Chen 2014 Eq. (17) schematic.

    ln(eta) = sum x_i ln(eta_i) - DeltaH_mix / (3 R T)
    """
    xs = {k: v for k, v in mole_fractions.items() if v > 0}
    if not xs:
        return kaptay_pure_viscosity(T, "Al")
    s = sum(xs.values())
    xs = {k: v / s for k, v in xs.items()}
    ln_eta = 0.0
    for el, x in xs.items():
        ln_eta += x * np.log(max(kaptay_pure_viscosity(T, el), 1e-12))
    ln_eta -= DeltaH_mix / (3.0 * R_GAS * max(T, 1.0))
    return float(np.exp(ln_eta))


def beta_from_size_ratio(r_diff: float, r_solv: float) -> float:
    """Sliding friction coefficient beta boundary helper (Chen 2014 Eqs. 3-7).

    If diffuser radius >> solvent: stick-like (beta large); else slip-like.
    Returns a finite beta (Pa·s·m) scale for the correction term.
    """
    ratio = r_diff / max(r_solv, 1e-15)
    # Map ratio to beta: larger ratio -> larger beta (more stick)
    # Scale chosen so 3*eta/(beta*r) is O(0.1-1) for eta~1e-3, r~1e-10
    beta = 1.0e7 * (0.2 + 0.8 * min(ratio, 2.0))  # Pa·s / m  (order-of-magnitude)
    return float(beta)


def sutherland_diffusivity(
    T: float,
    eta: float,
    r: float,
    beta: Optional[float] = None,
    r_solvent: Optional[float] = None,
) -> float:
    """Modified Sutherland / Stokes-Einstein:
    D = kT / (6 pi eta r) * (1 + 3 eta / (beta r))
    following Chen et al. (2014) Eqs. (3)-(7) and Tang et al., CALPHAD (2015).
    """
    eta = max(float(eta), 1e-12)
    r = max(float(r), 1e-15)
    if beta is None:
        r_s = r_solvent if r_solvent is not None else r
        beta = beta_from_size_ratio(r, r_s)
    beta = max(float(beta), 1e-30)
    stick = K_BOLTZMANN * T / (6.0 * np.pi * eta * r)
    corr = 1.0 + 3.0 * eta / (beta * r)
    return float(stick * corr)


def sutherland_log10_D(
    T: Union[float, np.ndarray, torch.Tensor],
    eta: Union[float, np.ndarray, torch.Tensor],
    r: Union[float, np.ndarray, torch.Tensor],
    beta: Union[float, np.ndarray, torch.Tensor],
) -> Union[float, np.ndarray, torch.Tensor]:
    """log10(D) for physics residual; supports numpy or torch."""
    if isinstance(T, torch.Tensor) or isinstance(eta, torch.Tensor):
        T_t = T if isinstance(T, torch.Tensor) else torch.as_tensor(T, dtype=torch.float32)
        eta_t = eta if isinstance(eta, torch.Tensor) else torch.as_tensor(eta, dtype=torch.float32)
        r_t = r if isinstance(r, torch.Tensor) else torch.as_tensor(r, dtype=torch.float32)
        b_t = beta if isinstance(beta, torch.Tensor) else torch.as_tensor(beta, dtype=torch.float32)
        eta_t = torch.clamp(eta_t, min=1e-12)
        r_t = torch.clamp(r_t, min=1e-15)
        b_t = torch.clamp(b_t, min=1e-30)
        D = (K_BOLTZMANN * T_t) / (6.0 * np.pi * eta_t * r_t) * (1.0 + 3.0 * eta_t / (b_t * r_t))
        return torch.log10(torch.clamp(D, min=1e-30))
    T_a = np.asarray(T, dtype=float)
    eta_a = np.clip(np.asarray(eta, dtype=float), 1e-12, None)
    r_a = np.clip(np.asarray(r, dtype=float), 1e-15, None)
    b_a = np.clip(np.asarray(beta, dtype=float), 1e-30, None)
    D = (K_BOLTZMANN * T_a) / (6.0 * np.pi * eta_a * r_a) * (1.0 + 3.0 * eta_a / (b_a * r_a))
    return np.log10(np.clip(D, 1e-30, None))


@dataclass
class PhysicsSample:
    T: float
    eta: float
    r_diff: float
    r_solv: float
    beta: float
    D_phys: float
    log10_D_phys: float


def physics_from_row(
    T: float,
    eta: float,
    diff_species: str,
    solvent_species: str = "Al",
) -> PhysicsSample:
    r_d = effective_radius_ri(T, diff_species)
    r_s = effective_radius_ri(T, solvent_species)
    beta = beta_from_size_ratio(r_d, r_s)
    D = sutherland_diffusivity(T, eta, r_d, beta=beta, r_solvent=r_s)
    return PhysicsSample(
        T=T, eta=eta, r_diff=r_d, r_solv=r_s, beta=beta,
        D_phys=D, log10_D_phys=float(np.log10(max(D, 1e-30))),
    )
