#!/usr/bin/env python3
"""
cif_html_viewer.py — Build a self-contained HTML page to view one or more .cif/mmCIF structures.

Usage:
    python cif_html_viewer.py --cif model1.cif --cif model2.cif --out structures.html --title "Protein viewer"

What you get:
    - Model dropdown (one entry per input file)
    - Chain visibility toggles (auto-detected from the structure)
    - Color schemes: chain / secondary structure / B-factor
    - Interface highlighting: residues within N Å between two selected chains
    - PNG snapshot + download the current structure (as .cif)
"""
from pathlib import Path
import argparse
import json
from html import escape as hescape

def parse_args():
    ap = argparse.ArgumentParser(description="Generate an interactive HTML viewer for .cif protein structures (3Dmol.js).")
    ap.add_argument("--cif", dest="cifs", action="append", required=True, help="Path to a .cif/.mmcif file. Repeat for multiple.")
    ap.add_argument("--out", default="structures.html", help="Output HTML file path.")
    ap.add_argument("--title", default="Protein mmCIF Viewer", help="HTML page title.")
    return ap.parse_args()

def main():
    args = parse_args()
    models = []
    for i, pth in enumerate(args.cifs):
        p = Path(pth)
        if not p.exists():
            raise SystemExit(f"Input not found: {p}")
        if p.suffix.lower() not in (".cif", ".mmcif"):
            print(f"[warn] {p.name} does not look like a CIF.", flush=True)
        models.append({
            "id": i,
            "name": p.name,
            "format": "cif",
            "text": p.read_text(encoding="utf-8", errors="ignore"),
        })

    html = build_html(models, args.title)
    out = Path(args.out)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out.resolve()}")

def build_html(models, title):
    payload = json.dumps(models)
    css = """
    body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;background:#0b0f14;color:#e5e7eb}
    header{display:flex;align-items:center;gap:12px;padding:10px 14px;border-bottom:1px solid #1f2937;background:#0e141b;position:sticky;top:0;z-index:10}
    #viewer{width:100%;height:calc(100vh - 64px);background:#111827}
    .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
    .group{display:flex;gap:6px;align-items:center;background:#111827;border:1px solid #1f2937;border-radius:12px;padding:6px 10px}
    select, input[type=number]{background:#0b0f14;border:1px solid #1f2937;border-radius:10px;color:#e5e7eb;padding:6px 8px}
    button{background:#1f2937;border:1px solid #374151;border-radius:10px;color:#e5e7eb;padding:6px 10px;cursor:pointer}
    button:hover{filter:brightness(1.1)}
    label{font-size:12px;opacity:.9}
    .pill{background:#0b0f14;border:1px solid #1f2937;border-radius:999px;padding:4px 8px;font-size:12px}
    .badge{padding:2px 6px;border-radius:8px;border:1px solid #374151;background:#0b0f14;font-size:11px;opacity:.9}
    """
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{hescape(title)}</title>
<style>{css}</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.3.0/3Dmol-min.min.js"></script>
</head>
<body>
<header class="row">
  <div class="group">
    <strong style="font-size:14px">{hescape(title)}</strong>
    <span class="badge" id="chainInfo"></span>
  </div>
  <div class="group">
    <label>Model</label>
    <select id="modelSelect"></select>
    <button id="resetCamera">Reset view</button>
  </div>
  <div class="group" id="chainToggles"></div>
  <div class="group">
    <label>Color</label>
    <select id="colorScheme">
      <option value="chain">Chain</option>
      <option value="ss">Secondary structure</option>
      <option value="bfactor">B-factor</option>
    </select>
    <button id="applyColor">Apply</button>
  </div>
  <div class="group">
    <label>Interface Å</label>
    <input id="ifaceDist" type="number" min="2" max="12" step="0.5" value="5.0"/>
    <label>from</label>
    <select id="ifaceFrom"></select>
    <label>to</label>
    <select id="ifaceTo"></select>
    <button id="highlightInterface">Highlight</button>
  </div>
  <div class="group">
    <button id="snapshotBtn">Snapshot PNG</button>
    <button id="downloadBtn">Download CIF</button>
  </div>
</header>
<div id="viewer"></div>

<script>
const MODELS = {payload};

// Nucleotide residue names for simple protein/RNA styling
const NUC = new Set(['A','U','G','C','DA','DT','DG','DC','I','DI','5MC','PSU']);

let viewer = null;
let currentModelId = null;
let modelObj = null; // $3Dmol GLModel

function initViewer() {{
  viewer = $3Dmol.createViewer("viewer", {{ backgroundColor: "#111827", antialias: true }});
  const sel = document.getElementById('modelSelect');
  MODELS.forEach(m => {{
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = m.name;
    sel.appendChild(opt);
  }});
  sel.addEventListener('change', () => loadModel(parseInt(sel.value)));
  loadModel(MODELS[0].id);

  document.getElementById('resetCamera').onclick = () => {{ viewer.zoomTo(); viewer.render(); }};
  document.getElementById('applyColor').onclick = applyColor;
  document.getElementById('highlightInterface').onclick = highlightInterface;
  document.getElementById('snapshotBtn').onclick = snapshotPNG;
  document.getElementById('downloadBtn').onclick = downloadCIF;
}}

function loadModel(id) {{
  currentModelId = id;
  const m = MODELS.find(x => x.id === id);
  viewer.clear();
  modelObj = viewer.addModel(m.text, m.format); // 'cif'
  // Default styles: RNA sticks, protein cartoon
  viewer.setStyle({{resn: Array.from(NUC)}}, {{stick:{{}}}});
  viewer.setStyle({{not: {{resn: Array.from(NUC)}}}}, {{cartoon:{{}}}});
  // Build chain UI after we can inspect atoms
  buildChainUI(m);
  applyColor(); // apply selected scheme
  viewer.zoomTo();
  viewer.render();
}}

function getChains() {{
  // Grab chains from the loaded model by inspecting atoms
  const atoms = modelObj.selectedAtoms({{}});
  const chains = new Set();
  const counts = {{}};
  const aa = new Set(['ALA','ARG','ASN','ASP','CYS','GLN','GLU','GLY','HIS','ILE','LEU','LYS','MET','PHE','PRO','SER','THR','TRP','TYR','VAL']);
  atoms.forEach(a => {{
    if (!a.chain) return;
    chains.add(a.chain);
    const key = a.chain;
    const resn = (a.resn||'').toUpperCase();
    counts[key] = counts[key] || {{aa:0, nucl:0}};
    if (aa.has(resn)) counts[key].aa++;
    if (NUC.has(resn)) counts[key].nucl++;
  }});
  const list = Array.from(chains).sort();
  const types = {{}};
  list.forEach(c => {{
    const k = counts[c] || {{aa:0, nucl:0}};
    types[c] = (k.nucl > k.aa) ? 'RNA' : (k.aa>0 ? 'Protein' : 'Other');
  }});
  return {{list, types}};
}}

function buildChainUI(m) {{
  const {{list, types}} = getChains();
  const div = document.getElementById('chainToggles');
  div.innerHTML = '';
  const fromSel = document.getElementById('ifaceFrom');
  const toSel = document.getElementById('ifaceTo');
  fromSel.innerHTML = ''; toSel.innerHTML = '';
  const info = document.getElementById('chainInfo');
  info.textContent = list.map(c => c+':'+(types[c]||'')).join('  ');

  list.forEach(c => {{
    const lbl = document.createElement('label');
    lbl.className = 'pill';
    const cb = document.createElement('input');
    cb.type='checkbox'; cb.checked = true; cb.dataset.chain=c;
    cb.onchange = () => toggleChain(c, cb.checked);
    lbl.appendChild(cb);
    lbl.appendChild(document.createTextNode(' Chain '+c+' ('+(types[c]||'')+')'));
    div.appendChild(lbl);

    const opt1 = document.createElement('option'); opt1.value=c; opt1.text=c;
    const opt2 = document.createElement('option'); opt2.value=c; opt2.text=c;
    fromSel.appendChild(opt1); toSel.appendChild(opt2);
  }});
  if (list.length>=2) toSel.selectedIndex = 1;
}}

function toggleChain(chain, visible) {{
  if (!modelObj) return;
  if (visible) {{
    viewer.setStyle({{chain}}, {{}}); // reset
    viewer.setStyle({{chain, resn: Array.from(NUC)}}, {{stick:{{}}}});
    viewer.setStyle({{chain, not: {{resn: Array.from(NUC)}}}}, {{cartoon:{{}}}});
  }} else {{
    viewer.setStyle({{chain}}, {{}});
  }}
  viewer.render();
}}

function applyColor() {{
  const scheme = document.getElementById('colorScheme').value;
  if (!modelObj) return;
  // Clear and reapply default styles
  viewer.setStyle({{}}, {{}});
  viewer.setStyle({{resn: Array.from(NUC)}}, {{stick:{{}}}});
  let styleProtein = {{cartoon:{{}}}};
  if (scheme === 'chain') styleProtein = {{cartoon:{{colorscheme:'chain'}}}};
  else if (scheme === 'ss') styleProtein = {{cartoon:{{colorscheme:'ssPyMOL'}}}};
  else if (scheme === 'bfactor') styleProtein = {{cartoon:{{colorscheme:{{prop:'b',gradient:'roygb'}}}}}};
  viewer.setStyle({{not: {{resn: Array.from(NUC)}}}}, styleProtein);
  viewer.render();
}}

function highlightInterface() {{
  const dist = parseFloat(document.getElementById('ifaceDist').value || '5');
  const fromC = document.getElementById('ifaceFrom').value;
  const toC = document.getElementById('ifaceTo').value;
  if (!modelObj || !fromC || !toC || fromC===toC) return;
  applyColor();
  const selFromNear = {{within: dist, sel: {{chain: toC}}, chain: fromC}};
  const selToNear = {{within: dist, sel: {{chain: fromC}}, chain: toC}};
  viewer.setStyle(selFromNear, {{stick:{{radius:0.2}}}});
  viewer.setStyle(selToNear, {{stick:{{radius:0.2}}}});
  viewer.render();
}}

function snapshotPNG() {{
  if (!viewer) return;
  const data = viewer.pngURI();
  const a = document.createElement('a');
  a.href = data;
  a.download = 'structure.png';
  a.click();
}}

function downloadCIF() {{
  const m = MODELS.find(x => x.id === currentModelId);
  if (!m) return;
  const blob = new Blob([m.text], {{type:'chemical/x-cif'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = (m.name || 'structure') + '.cif';
  a.click();
  setTimeout(()=> URL.revokeObjectURL(url), 1000);
}}

document.addEventListener('DOMContentLoaded', initViewer);
</script>
</body>
</html>
"""
if __name__ == "__main__":
    main()
