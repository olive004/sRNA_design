# Boltz-2 3D viewers

You have **two** drop-in options to visualize Boltz-2 PDB outputs (protein–RNA complexes).

---

## A) Notebook viewer (py3Dmol + ipywidgets)

**Files:** `boltz2_notebook_viewer.py`  
**Use in Jupyter:**
```python
!pip install py3Dmol ipywidgets
from boltz2_notebook_viewer import view_boltz2
view_boltz2(["pred_0.pdb","pred_1.pdb"], title="Boltz-2 run")
```
Features:
- Model selector, chain toggles, color schemes (chain/secondary/B-factor),
- Interface highlight within N Å between two chains,
- Reset camera.

---

## B) Static HTML generator (3Dmol.js)

**File:** `boltz2_viewer.py`  
**Build a single HTML file you can share internally:**
```bash
python boltz2_viewer.py --pdb pred_0.pdb --pdb pred_1.pdb --out boltz2_view.html --title "Boltz-2 complex"
```
Open `boltz2_view.html` in a browser (needs internet to load 3Dmol.js CDN).  
Features:
- Multiple-model dropdown, chain visibility toggles,
- Color by chain/secondary/B-factor,
- Interface highlight, PNG snapshot, PDB download.

Tip: glob all PDBs in your predictions folder:
```bash
python - <<'PY'
import glob, subprocess
pdbs = sorted(glob.glob("predictions/**/*.pdb", recursive=True))
cmd = ["python","boltz2_viewer.py"] + sum([["--pdb",p] for p in pdbs], []) + ["--out","boltz2_view.html"]
subprocess.run(cmd, check=True)
PY
```