

from typing import Sequence, Optional, Union
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from varnaapi import Structure


def show_rna_structure(rna_structure, seq, resolution=3, algorithm='radiate', annotate: bool = False, highlight_kwrgs: dict = None):
    try:
        v = Structure(structure=rna_structure, sequence=seq)
        v._params['resolution'] = resolution
        v._params['algorithm'] = algorithm
        if annotate:
            v._params['autoHelices'] = True
            v._params['autoInteriorLoops'] = True
            v._params['autoTerminalLoops'] = True
        if highlight_kwrgs:
            v.add_highlight_region(**highlight_kwrgs)
        v.show()
        # v.savefig("example.png", show=True)
    except FileNotFoundError:
        print('No Java found, could not visualise')
        pass
    
    
def approx_to_nearest_mapval(values: np.ndarray, *, map: np.ndarray) -> np.ndarray:
    """
    For each value in `values`, find the nearest value in `map` and return an array of these.

    Args
    ----
    values: Iterable of float values to map.
    map:    Iterable of float "map" values to approximate to.

    Returns
    -------
    np.ndarray of same shape as `values`, with each entry replaced by nearest entry from `map`.
    """
    values = np.asarray(values, dtype=float)
    map = np.asarray(map, dtype=float)
    mapped_vals = np.empty_like(values)
    for i, v in enumerate(values):
        idx = np.abs(map - v).argmin()
        mapped_vals[i] = map[idx]
    return mapped_vals


def draw_rna_nucolor_varna(
    dot_bracket: str,
    sequence: str,
    nuc_color: np.ndarray,
    *,
    out_file: Optional[str] = None,
    caption: str = "pLDDT (higher = better)",
    algorithm: str = "naview",
    resolution: Union[int, float] = 10,
    annotate: bool = False,
    palette: str = 'viridis',
    vMin: float = 0.0,
    vMax: float = 1.0,
    autonorm: bool = True
) -> Structure:
    """
    Visualise RNA secondary structure with VARNA (via varnaapi) and color nucleotides by nuc_color using 'viridis'.

    Args
    ----
    dot_bracket: RNA structure in dot-bracket notation.
    sequence:    RNA sequence (same length as dot_bracket).
    plddt:       Iterable of nuc_color values (0..100 or 0..1); len must equal sequence length.
    out_file:    If given, save to this path (.png or .svg). Otherwise display with v.show().
    caption:     Title for the colorbar/legend.
    algorithm:   VARNA drawing algorithm ('naview', 'radiate', 'circular', 'line').

    Returns
    -------
    Structure object (so you can tweak or re-save if you want).
    """
    # --- basic checks
    n = len(sequence)
    if len(dot_bracket) != n:
        raise ValueError(
            f"sequence and dot_bracket must match in length (got {n} vs {len(dot_bracket)})")
    nuc_color = np.asarray(nuc_color, dtype=float)
    if nuc_color.shape[0] != n:
        raise ValueError(
            f"plDDT length must equal sequence length (expected {n}, got {nuc_color.shape[0]})")

    if autonorm:
        norm_vals = np.interp(nuc_color, (nuc_color.min(), nuc_color.max()), (0.0, 1.0))
    else:
        norm_vals = nuc_color.copy()

    # --- build a custom viridis style mapping for VARNA
    # VARNA API allows a custom color map via a dict {value: color}; we provide a dense 256-step mapping.
    # Keys must be on the same numeric scale as vMin/vMax passed to add_colormap.
        
    keys = np.linspace(vMin, vMax, 256)
    samples = keys / vMax
    value_list_for_varna = approx_to_nearest_mapval(norm_vals, map=keys).tolist()

    vir = cm.get_cmap(palette)
    hex_colors = [mcolors.to_hex(vir(x), keep_alpha=False) for x in samples]
    style_dict = {float(k): c for k, c in zip(keys, hex_colors)}

    # --- make the drawing
    v = Structure(structure=dot_bracket, sequence=sequence)
    v.set_algorithm(algorithm)                 # e.g. 'naview'
    v.add_colormap(value_list_for_varna,       # one value per base
                   vMin=vMin, vMax=vMax,
                   caption=caption,
                   style=style_dict)
    # Optional aesthetic tweaks:
    # keep base outlines crisp over the colormap
    v.update(fillBases=True, baseInner="#FFFFFF", bpStyle="lw")
    v._params['resolution'] = resolution
    if annotate:
        v._params['autoHelices'] = True
        v._params['autoInteriorLoops'] = True
        v._params['autoTerminalLoops'] = True

    # --- render
    if out_file:
        v.savefig(out_file)   # .png or .svg
    # else:
    # v.show()
    return v
