# Create a robust CIF→PDB converter script using Biopython (no internet needed here).
# It supports:
# - Selecting a specific model or all models
# - Dropping hydrogens
# - Filtering to protein/RNA/DNA/ligand/water
# - Choosing best altloc by occupancy (default) or keep all
# - Optional residue renumbering (per chain)
# Usage examples are included in the header.

#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import argparse
from typing import List, Set, Tuple, Dict

# Requires: pip install biopython
from Bio.PDB import MMCIFParser, PDBIO, Select, is_aa

RNA_RESN = {"A","U","G","C","I","PSU","5MC"}
DNA_RESN = {"DA","DT","DG","DC","DI"}

def residue_kind(res):
    """Return one of: 'protein','rna','dna','water','ligand'."""
    het, resseq, icode = res.id
    name = res.get_resname().strip().upper()
    if het == 'W' or name in {"HOH","WAT"}:
        return "water"
    if is_aa(res, standard=False):
        return "protein"
    if name in RNA_RESN:
        return "rna"
    if name in DNA_RESN:
        return "dna"
    if het.strip() != "":
        return "ligand"
    # Fallbacks: many modified nucleotides present in CIFs; treat unknown HETNA* as ligand.
    return "ligand"

class AltlocBestByOcc(Select):
    """
    Selection that:
      - keeps only atoms whose altloc is the best (highest occupancy) per (residue, atom name)
      - optional: removes hydrogens
      - optional: filters entity kind
      - optional: restricts to a specific model id
    Also supports residue renumbering via in-place mutation (per chain).
    """
    def __init__(self, *, keep_h: bool, include_kinds: Set[str], model_id: int|None, renumber: bool, structure):
        self.keep_h = keep_h
        self.include_kinds = include_kinds
        self.model_id = model_id
        self.best_alt: Dict[Tuple, Tuple[str, float]] = {}  # key=(chain_id, res_id_tuple, atom_name) -> (altloc, occ)
        # Precompute best altlocs
        for model in structure:
            if model_id is not None and model.id != model_id:
                continue
            for chain in model:
                for res in chain:
                    kind = residue_kind(res)
                    if include_kinds and kind not in include_kinds:
                        continue
                    atoms = list(res.get_unpacked_list())
                    for atom in atoms:
                        alt = atom.get_altloc() or ' '
                        key = (chain.id, res.id, atom.get_name())
                        occ = atom.get_occupancy() or 0.0
                        # pick highest occupancy; tie-break prefer alt 'A' then blank
                        if key not in self.best_alt or occ > self.best_alt[key][1] or (occ == self.best_alt[key][1] and alt in ('A',' ')):
                            self.best_alt[key] = (alt, occ)
        # Renumber residues per chain if requested
        if renumber:
            for model in structure:
                if model_id is not None and model.id != model_id:
                    continue
                for chain in model:
                    i = 1
                    for res in list(chain):
                        kind = residue_kind(res)
                        if include_kinds and kind not in include_kinds:
                            continue
                        old_id = res.id
                        # Only renumber standard residues (hetflag ' ' or 'H_' etc keep same?)
                        new_id = (' ', i, ' ')
                        try:
                            res.id = new_id
                        except Exception:
                            pass
                        i += 1

    def accept_model(self, model):
        if self.model_id is None:
            return 1
        return 1 if model.id == self.model_id else 0

    def accept_chain(self, chain):
        return 1

    def accept_residue(self, residue):
        kind = residue_kind(residue)
        if self.include_kinds and kind not in self.include_kinds:
            return 0
        return 1

    def accept_atom(self, atom):
        # Hydrogens
        if not self.keep_h:
            name = atom.get_name().strip()
            # Biopython marks element separately but name starts with 'H' often
            if atom.element == 'H' or name.upper().startswith('H'):
                return 0
        # Altloc filter
        res = atom.get_parent()
        key = (res.get_parent().id, res.id, atom.get_name())
        best_alt, _ = self.best_alt.get(key, (' ', 0.0))
        atom_alt = atom.get_altloc() or ' '
        return 1 if atom_alt == best_alt else 0

def parse_args():
    p = argparse.ArgumentParser(description="Convert mmCIF to PDB with sensible defaults for protein–RNA from Boltz-2.")
    p.add_argument("inputs", nargs="+", help="Input .cif files (you can pass multiple)")
    p.add_argument("-o","--out", help="Output PDB file (only valid with a single input). If omitted, writes alongside input with .pdb extension.")
    p.add_argument("--model", type=int, default=None, help="Keep only this model id (0-based in Biopython). If omitted, all models are written.")
    p.add_argument("--all-models", action="store_true", help="When multiple models exist, write one PDB per model with suffix _modelN.pdb (ignored if --model is set).")
    p.add_argument("--no-h", action="store_true", help="Drop hydrogens.")
    p.add_argument("--only", default="", help="Comma list to include: protein,rna,dna,ligand,water. Empty=keep all.")
    p.add_argument("--keep-altloc", action="store_true", help="Keep all altlocs instead of selecting best by occupancy.")
    p.add_argument("--renumber", action="store_true", help="Renumber residues per chain starting at 1.")
    return p.parse_args()

def write_one(cif_path: Path, out_path: Path, *, model_id, all_models, keep_h, include_kinds, keep_altloc, renumber):
    parser = MMCIFParser(QUIET=True)
    structure_id = cif_path.stem[:10]
    structure = parser.get_structure(structure_id, str(cif_path))

    io = PDBIO()

    if keep_altloc:
        class KeepAll(Select):
            def __init__(self, keep_h, include_kinds, model_id, structure):
                self.keep_h=keep_h; self.include_kinds=include_kinds; self.model_id=model_id
            def accept_model(self, model): return 1 if (self.model_id is None or model.id==self.model_id) else 0
            def accept_residue(self, residue):
                if self.include_kinds and residue_kind(residue) not in self.include_kinds:
                    return 0
                return 1
            def accept_atom(self, atom):
                if not self.keep_h and (atom.element=='H' or atom.get_name().upper().startswith('H')):
                    return 0
                return 1
        selector = KeepAll(keep_h=keep_h, include_kinds=include_kinds, model_id=model_id, structure=structure)
    else:
        selector = AltlocBestByOcc(keep_h=keep_h, include_kinds=include_kinds, model_id=model_id, renumber=renumber, structure=structure)

    if model_id is None and all_models and len(structure) > 1:
        # write one file per model
        for m in structure:
            io.set_structure(structure)
            sel = selector
            # We'll override model filtering for this loop by wrapping accept_model
            class ThisModel(Select):
                def accept_model(self_inner, model): return 1 if model.id==m.id else 0
                def accept_chain(self_inner, chain): return sel.accept_chain(chain)
                def accept_residue(self_inner, residue): return sel.accept_residue(residue)
                def accept_atom(self_inner, atom): return sel.accept_atom(atom)
            out_m = out_path.with_name(out_path.stem + f"_model{m.id}" + out_path.suffix)
            io.save(str(out_m), select=ThisModel())
            print(f"Wrote {out_m}")
    else:
        io.set_structure(structure)
        io.save(str(out_path), select=selector)
        print(f"Wrote {out_path}")

def main():
    args = parse_args()
    inputs = [Path(x) for x in args.inputs]
    for p in inputs:
        if not p.exists():
            sys.exit(f"Input not found: {p}")
        if p.suffix.lower() not in (".cif",".mmcif"):
            print(f"[warn] {p.name} does not look like a CIF, continuing...", file=sys.stderr)

    if args.out and len(inputs) != 1:
        sys.exit("--out can only be used with a single input file.")

    include_kinds = set(filter(None, (s.strip().lower() for s in args.only.split(","))))
    unknown = include_kinds - {"protein","rna","dna","ligand","water"}
    if unknown:
        sys.exit(f"--only had unknown kinds: {sorted(unknown)}")

    for p in inputs:
        out = Path(args.out) if args.out else p.with_suffix(".pdb")
        write_one(
            p, out,
            model_id=args.model,
            all_models=args.all_models,
            keep_h=not args.no_h,
            include_kinds=include_kinds,
            keep_altloc=args.keep_altloc,
            renumber=args.renumber
        )

if __name__ == "__main__":
    main()