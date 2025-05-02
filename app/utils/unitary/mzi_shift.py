"""
mzi_shift.py
============

Helper module that
1. loads a saved *<MZI>_shift_spline.pkl* file
2. returns the phase-shift correction for any θ

The module can be:

• **imported** from other code::

      from mzi_shift import ps_rad
      dphi = ps_rad("H1", 1.234)

• **run as a CLI tool**::

      python mzi_shift.py --mzi H1 --theta 1.234
"""

from pathlib import Path
import argparse
import pickle
import numpy as np
import sys
from typing import Union

# --------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------
BASE_DIR = (Path(__file__).resolve().parent / "phase offset").resolve()

def set_base_dir(path: Union[str, Path]) -> None:
    """Change the folder in which spline pkl files are looked up."""
    global BASE_DIR
    BASE_DIR = Path(path)


# --------------------------------------------------------------------
# Core helpers (safe to import from other modules)
# --------------------------------------------------------------------
def _load_spline(mzi_tag: str):
    """Return the CubicSpline object for the chosen MZI (or raise FileNotFoundError)."""
    pkl_path = BASE_DIR / f"{mzi_tag.upper()}_shift_spline.pkl"
    if not pkl_path.exists():
        raise FileNotFoundError(pkl_path)
    with pkl_path.open("rb") as f:
        return pickle.load(f)


def ps_rad(mzi_tag: str, theta_rad):
    """
    Return the required phase correction *in radians* for θ supplied in radians.

    Parameters
    ----------
    mzi_tag : str
        Identifier (e.g. 'E1', 'F1', 'H1')
    theta_rad : float or np.ndarray
        Target angle(s) in radians.  Any value is OK; it’s wrapped to [0, 2π).

    Returns
    -------
    float or np.ndarray
        Phase shift in radians, same shape as `theta_rad`.
    """
    spline = _load_spline(mzi_tag)
    return spline(np.mod(theta_rad, 2 * np.pi))


def ps_pi(mzi_tag: str, theta_pi):
    """
    Same as `ps_rad` but all quantities are **π units**.

    Example: theta_pi = 0.5  →  θ = 0.5 π rad
    """
    print(mzi_tag)
    print(theta_pi)
    return ps_rad(mzi_tag, theta_pi * np.pi) / np.pi


# --------------------------------------------------------------------
# Command-line interface
# --------------------------------------------------------------------
def _cli() -> None:
    p = argparse.ArgumentParser(
        description="Return phase-shift (rad) for a target θ (rad)."
    )
    p.add_argument("-m", "--mzi", required=True, help="MZI tag, e.g. E1, F1, H1 …")
    p.add_argument(
        "-t",
        "--theta",
        type=float,
        help="Target θ in radians.  If omitted you will be prompted.",
    )
    p.add_argument(
        "--base_dir",
        help="Override the folder that contains *_shift_spline.pkl files.",
    )
    args = p.parse_args()

    if args.base_dir:
        set_base_dir(args.base_dir)

    if args.theta is None:
        try:
            args.theta = float(input("Enter θ (rad): "))
        except ValueError:
            sys.exit("No valid θ supplied.")

    try:
        dphi = ps_rad(args.mzi, args.theta)
    except FileNotFoundError as e:
        sys.exit(f"Spline file not found:\n  {e}")

    print(f"\nMZI          : {args.mzi.upper()}")
    print(f"θ (input)    : {args.theta:.10f} rad")
    print(f"phase shift  : {dphi:.10f} rad  ({dphi/np.pi:+.6f} π)\n")


# Only runs when you execute “python mzi_shift.py …”, never on import.
if __name__ == "__main__":
    _cli()
