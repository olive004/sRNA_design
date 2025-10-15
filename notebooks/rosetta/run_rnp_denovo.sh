#!/usr/bin/env bash
set -euo pipefail

# --- Usage -------------------------------------------------------------------
# ./run_rnp_denovo.sh \
#   --rosetta /path/to/rosetta   \
#   --protein_cif protein_multimer.cif \
#   --rna_seq ACGU...            \
#   --rna_secstruct "(((....))).((...))..." \
#   --nstruct 500                \
#   --seed 1234567               \
#   --outdir rnp_run
# ./run_rnp_denovo.sh \
#   --rosetta ~/rosetta/rosetta.binary.ubuntu.release-408/main/source   \
#   --protein_pdb /home/hslab/Olive/Kode/sRNA_design/notebooks/boltz/results/boltz_results_bzjob_2_hfq_hex/predictions/bzjob_2_hfq_hex/bzjob_2_hfq_hex_model_0_renamed.pdb \
#   --rna_seq AUGAGCAAAGGCGAAGAACUGUUUACCGGCGUGGUGCCGAUUCUGGUGGAACUGGAUGGCGAUGUGAACGGCCAUAAAUUUAGCGUGAGCGGCGAAGGCGAAGGCGAUGCGACCUAUGGCAAACUGACCCUGAAAUUUAUUUGCACCACCGGCAAACUGCCGGUGCCGUGGCCGACCCUGGUGACCACCUUUAGCUAUGGCGUGCAGUGCUUUAGCCGCUAUCCGGAUCAUAUGAAACAGCAUGAUUUUUUUAAAAGCGCGAUGCCGGAAGGCUAUGUGCAGGAACGCACCAUUUUUUUUAAAGAUGAUGGCAACUAUAAAACCCGCGCGGAAGUGAAAUUUGAAGGCGAUACCCUGGUGAACCGCAUUGAACUGAAAGGCAUUGAUUUUAAAGAAGAUGGCAACAUUCUGGGCCAUAAACUGGAAUAUAACUAUAACAGCCAUAACGUGUAUAUUAUGGCGGAUAAACAGAAAAACGGCAUUAAAGUGAACUUUAAAAUUCGCCAUAACAUUGAAGAUGGCAGCGUGCAGCUGGCGGAUCAUUAUCAGCAGAACACCCCGAUUGGCGAUGGCCCGGUGCUGCUGCCGGAUAACCAUUAUCUGAGCACCCAGAGCGCGCUGAGCAAAGAUCCGAACGAAAAACGCGAUCAUAUGGUGCUGCUGGAAUUUGUGACCGCGGCGGGCAUUACCCAUGGCAUGGAUGAACUGUAUAAA            \
#   --rna_secstruct ".........((((((.....((((((.....((((((((.(((((..........(((((..........))))).......((((.((((((.((((((..((((.(((........)))...)).))...........((((((.(((((((...)))))))((((((((.((...(((...)))...)).)))))))))))))))))))).))))))....(((((((.((...))..)))))))........(((((..(((....)))..)))))....)))).(((((((((((((((.(((((.(..((.((((...(((......)))...)))).))(((.(((....)))...)))............).))))).)))))))))))))))....(((((((........)))))))............(((((((........))))))).......)))))...))))))))..)))))).......))))))....((((.(..((((....((((.((((.(((.((((..(((((((..((((......(((....)))((((((.((((((((((((...))))))).))......)))))))))......((((((.........)).))))....))))))))))).....)))))))))))..))))...))))....).))))..........." \
#   --rna_helixpdb "/home/hslab/Olive/Kode/sRNA_design/notebooks/boltz/results/boltz_results_bzjob_6_gfpmut3/predictions/bzjob_6_gfpmut3/bzjob_6_gfpmut3_model_0.pdb" \
#   --nstruct 500                \
#   --seed 1               \
#   --outdir rnp_run
#
# Notes:
#  - --rosetta should point at the Rosetta *source or install* root containing bin/ and database/
#  - If you already have a protein PDB instead of CIF, pass it via --protein_pdb and skip --protein_cif
#  - Secondary structure must be dot-bracket; protein part will be auto-filled with dots (rigid body)
#  - Requires: Ubuntu/Debian-like system (apt), Python3; installs gemmi+biopython for convenience.

# --- Parse args --------------------------------------------------------------
ROSETTA=""
PROT_CIF=""
PROT_PDB=""
RNA_SEQ=""
RNA_SS=""
RNA_HELIXPDB=""
NSTRUCT=100
SEED=1111111
OUTDIR="rnp_run"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rosetta) ROSETTA="$2"; shift 2;;
    --protein_cif) PROT_CIF="$2"; shift 2;;
    --protein_pdb) PROT_PDB="$2"; shift 2;;
    --rna_seq) RNA_SEQ="$2"; shift 2;;
    --rna_secstruct) RNA_SS="$2"; shift 2;;
    --rna_helixpdb) RNA_HELIXPDB="$2"; shift 2;;
    --nstruct) NSTRUCT="$2"; shift 2;;
    --seed) SEED="$2"; shift 2;;
    --outdir) OUTDIR="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ -z "$ROSETTA" || -z "$RNA_SEQ" || -z "$RNA_SS" || ( -z "$PROT_CIF" && -z "$PROT_PDB" ) ]]; then
  echo "Required: --rosetta --rna_seq --rna_secstruct and one of --protein_cif/--protein_pdb"
  exit 1
fi
if [[ ! -d "$ROSETTA" ]]; then
  echo "Rosetta folder not found: $ROSETTA"
  echo "Download/build Rosetta (needs bin/ and database/). Build instructions: docs use scons: ./scons.py -j 16 mode=release bin"
  exit 1
fi

mkdir -p "$OUTDIR"/{inputs,work,logs}

# --- Minimal deps (Ubuntu/Debian) -------------------------------------------
# echo "[*] Installing gemmi + biopython (for CIF->PDB & sequence extraction)..."
# if command -v apt-get >/dev/null 2>&1; then
#   sudo apt-get update -y
#   sudo apt-get install -y python3-pip
# fi
# python3 -m pip install --upgrade gemmi biopython

ROSETTAMAIN="$(dirname "$ROSETTA")"

# --- Convert CIF -> PDB if needed -------------------------------------------
if [[ -n "$PROT_CIF" ]]; then
  echo "[*] Converting CIF to PDB with gemmi..."
  python3 - <<'PY'
import sys, gemmi
import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--inp", required=True)
ap.add_argument("--out", required=True)
ns = ap.parse_args(sys.argv[1:])
st = gemmi.read_structure(ns.inp)
st.remove_waters()  # optional: drop waters
st.remove_hydrogens()  # optional: unify; rna_denovo handles hydrogens later
st.make_minimum_image()  # tidy up if needed
st.export_minimal_pdb(ns.out)
PY
  python3 - <<PY
import sys
from argparse import ArgumentParser
ap = ArgumentParser()
ap.add_argument('--inp', required=True)
ap.add_argument('--out', required=True)
ns = ap.parse_args(['--inp', '$PROT_CIF', '--out', '$OUTDIR/inputs/protein.pdb'])
# run the converter embedded above
PY
  PROT_PDB="$OUTDIR/inputs/protein.pdb"
else
  cp "$PROT_PDB" "$OUTDIR/inputs/protein.pdb"
  PROT_PDB="$OUTDIR/inputs/protein.pdb"
fi

# --- Extract protein sequence from PDB (concatenate all protein chains) ------
echo "[*] Extracting protein sequence from PDB with gemmi..."
python3 - <<PY
import sys, gemmi, re
from pathlib import Path
pdb = Path('$PROT_PDB') # Path(sys.argv[1])
out_fa = Path('$OUTDIR/inputs/protein.fasta') # Path(sys.argv[2])
st = gemmi.read_structure(str(pdb))
aa_lookup = {'GLY': 'G',
'ALA': 'A',
'VAL': 'V',
'LEU': 'L',
'ILE': 'I',
'THR': 'T',
'SER': 'S',
'MET': 'M',
'CYS': 'C',
'PRO': 'P',
'PHE': 'F',
'TYR': 'Y',
'TRP': 'W',
'HIS': 'H',
'LYS': 'K',
'ARG': 'R',
'ASP': 'D',
'GLU': 'E',
'ASN': 'N',
'GLN': 'Q'}
seq=''
for ch in st[0]:
    if ch.get_polymer().check_polymer_type() == gemmi.PolymerType.PeptideL:
        seq_list = ch.get_polymer().extract_sequence()
        seq_list = [aa_lookup.get(res, 'X') for res in seq_list]  # map to one-letter, unknowns to X
        seq += ''.join(seq_list)  # one-letter AA per chain, concatenated
# sanity
seq = re.sub(r'[^ACDEFGHIKLMNPQRSTVWY]', '', seq)
if not seq:
    raise SystemExit("No protein sequence found in PDB.")
out_fa.write_text(f">protein\n{seq}\n")
with open(out_fa, 'w') as f: 
    f.write(f">protein\n{seq}\n")
print(len(seq))
PY
# PROT_LEN=$(python3 - "$PROT_PDB" "$OUTDIR/inputs/protein.fasta" 2>/dev/null | tail -n1)
PROT_LEN=$(awk '/^>/ { if (seqlen) {
              print seqlen
              }
            # print

            seqtotal+=seqlen
            seqlen=0
            seq+=1
            next
            }
    {
    seqlen += length($0)
    }     
    END{print seqlen
    }' "$OUTDIR/inputs/protein.fasta")

# --- Build combined FASTA and secondary structure ---------------------------
echo "[*] Writing complex FASTA + secstruct..."
echo ">complex" > "$OUTDIR/inputs/fasta.txt"
cat "$OUTDIR/inputs/protein.fasta" | awk 'NR==2{printf $0}' >> "$OUTDIR/inputs/fasta.txt"
# printf "%s\n" "$RNA_SEQ" >> "$OUTDIR/inputs/fasta.txt"
printf "%s\n" "${RNA_SEQ,,}" >> "$OUTDIR/inputs/fasta.txt"

python3 - <<PY
prot_len = int("$PROT_LEN")
rna_ss = "$RNA_SS".strip()
sec = "."*prot_len + rna_ss
open("$OUTDIR/inputs/secstruct.txt","w").write(sec+"\n")
print(f"Total length: {len(sec)} (protein {prot_len} + RNA {len(rna_ss)})")
PY

# # --- Make an (optional) tiny A-form helix seed for RNA (3-nt) ----------------
# # Rosetta demo uses a short RNA helix as a rigid seed; this is optional.
# # If you skip it, rna_denovo will still fold the RNA de novo.
# echo "[*] Creating a minimal 3-nt A-form RNA helix seed (optional)..."
# python3 - <<PY
# from pathlib import Path
# pdb = Path("$OUTDIR/inputs/RNA_helix_3nt.pdb")
# pdb.write_text("""\
# ATOM      1  P    G A   1       0.000   0.000   0.000  1.00 20.00           P
# TER
# END
# """)
# PY

# --- Flags for fold-and-dock (protein rigid, RNA moves) ----------------------
cat > "$OUTDIR/inputs/flags_fold_and_dock" <<FLAGS
# Required inputs
-fasta $OUTDIR/inputs/fasta.txt
-secstruct_file $OUTDIR/inputs/secstruct.txt
# -s $PROT_PDB $OUTDIR/inputs/RNA_helix_3nt.pdb
-s $PROT_PDB $RNA_HELIXPDB

# Strongly recommended for RNA-protein modeling
-new_fold_tree_initializer true

# Docking on (RNA moves vs rigid protein)
-rna_protein_docking true
-docking_move_size 1.0
-ramp_rnp_vdw true
-FA_low_res_rnp_scoring true
-convert_protein_CEN false

# Low-res only or enable RNA minimization later; start simple:
-minimize_rna false

# Output
-nstruct $NSTRUCT
-out:file:silent $OUTDIR/work/fold_and_dock.out

# Reproducible RNG
-run:constant_seed
-run:jran $SEED
FLAGS

# --- Flags for NO-DOCK variant (fix initial orientation; protein rigid) ------
cat > "$OUTDIR/inputs/flags_no_dock" <<FLAGS
-fasta $OUTDIR/inputs/fasta.txt
-secstruct_file $OUTDIR/inputs/secstruct.txt
# Put protein and RNA helix in one file to *fix* their relative orientation
# -s $PROT_PDB $OUTDIR/inputs/RNA_helix_3nt.pdb
-s $PROT_PDB $RNA_HELIXPDB
-new_fold_tree_initializer true
-rna_protein_docking false
-minimize_rna false
-nstruct $NSTRUCT
-out:file:silent $OUTDIR/work/fix_rigid.out
-run:constant_seed
-run:jran $SEED
FLAGS

# --- Run ---------------------------------------------------------------------
EXE="$ROSETTA/bin/rna_denovo.default.$(uname -s | tr '[:upper:]' '[:lower:]')$(uname -m | sed 's/x86_64/linuxgccrelease/;s/aarch64/linuxclangrelease/')"
if [[ ! -x "$EXE" ]]; then
  # Fallback: try a common build name
  EXE="$ROSETTA/bin/rna_denovo.default.linuxgccrelease"
fi
[[ -x "$EXE" ]] || { echo "Cannot find Rosetta rna_denovo executable in $ROSETTA/bin"; exit 1; }

echo "[*] Running fold-and-dock (protein rigid, RNA docks)..."
"$EXE" @"$OUTDIR/inputs/flags_fold_and_dock" -database "$ROSETTAMAIN/database" > "$OUTDIR/logs/fold_and_dock.log" 2>&1

echo "[*] Done. Silent file: $OUTDIR/work/fold_and_dock.out"
echo "Tip: extract top models with Rosetta's extract_lowscore_decoys.py (in Rosetta tools)."
