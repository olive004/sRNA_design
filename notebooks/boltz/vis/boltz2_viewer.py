from pathlib import Path
import argparse
from html import escape as hescape
import json

NUC_NAMES = {"A","U","G","C","DA","DT","DG","DC","I","DI","5MC","PSU"}
AA3 = {"ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE","LEU","LYS","MET","PHE","PRO","SER","THR","TRP","TYR","VAL"}

def parse_args():
    ap = argparse.ArgumentParser(description="Generate an interactive 3D viewer HTML for Boltz-2 PDB outputs (protein–RNA).")
    ap.add_argument("--pdb", action="append", required=True, help="Path to a PDB file. Repeat for multiple models.")
    ap.add_argument("--out", default="boltz2_view.html", help="Output HTML file path.")
    ap.add_argument("--title", default="Boltz-2 Protein–RNA Viewer", help="Title shown in the HTML.")
    return ap.parse_args()

def analyze_pdb(pdb_text):
    chains = {}
    for line in pdb_text.splitlines():
        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue
        if len(line) < 22:
            continue
        resname = line[17:20].strip().upper()
        chain = line[21:22]
        d = chains.setdefault(chain, {"aa":0, "nucl":0, "resnames":set()})
        d["resnames"].add(resname)
        if resname in AA3:
            d["aa"] += 1
        if resname in NUC_NAMES:
            d["nucl"] += 1
    chain_types = {}
    for c, d in chains.items():
        if d["nucl"] > d["aa"]:
            chain_types[c] = "RNA"
        elif d["aa"] > 0:
            chain_types[c] = "Protein"
        else:
            chain_types[c] = "Other"
    return {"chains": list(chains.keys()), "chain_types": chain_types}

def build_html(models, title):
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
    payload_json = json.dumps(models)
    html_text = f"""<!DOCTYPE html>
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
    <button id="downloadPDB">Download PDB</button>
  </div>
</header>
<div id="viewer"></div>
<script>
const MODELS = {payload_json};

let viewer = null;
let currentModelId = null;
let modelObj = null;

function initViewer() {{
  viewer = $3Dmol.createViewer("viewer", {{ backgroundColor: "#111827", antialias: true }});
  const sel = document.getElementById('modelSelect');
  MODELS.forEach(m => {{
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = m.name;
    sel.appendChild(opt);
  }});
  sel.addEventListener('change', () => loadModel(sel.value));
  loadModel(MODELS[0].id);
  document.getElementById('resetCamera').onclick = () => {{ viewer.zoomTo(); viewer.render(); }};
  document.getElementById('applyColor').onclick = applyColor;
  document.getElementById('highlightInterface').onclick = highlightInterface;
  document.getElementById('snapshotBtn').onclick = snapshotPNG;
  document.getElementById('downloadPDB').onclick = downloadPDB;
}}

function loadModel(id) {{
  currentModelId = id;
  const m = MODELS.find(x => x.id == id);
  viewer.clear();
  modelObj = viewer.addModel(m.pdb, "pdb");
  viewer.setStyle({{resn:['A','U','G','C','DA','DT','DG','DC','I','DI','5MC','PSU']}}, {{stick:{{}}}});
  viewer.setStyle({{not: {{resn:['A','U','G','C','DA','DT','DG','DC','I','DI','5MC','PSU']}}}}, {{cartoon:{{}}}});
  applyColor();
  buildChainUI(m);
  viewer.zoomTo();
  viewer.render();
}}

function buildChainUI(m) {{
  const div = document.getElementById('chainToggles');
  div.innerHTML = '';
  const fromSel = document.getElementById('ifaceFrom');
  const toSel = document.getElementById('ifaceTo');
  fromSel.innerHTML = '';
  toSel.innerHTML = '';
  const info = document.getElementById('chainInfo');
  const labels = m.chains.map(c => c + ":" + (m.chain_types[c]||'Unknown'));
  info.textContent = labels.join('  ');
  m.chains.forEach(c => {{
    const lbl = document.createElement('label');
    lbl.className='pill';
    const cb = document.createElement('input');
    cb.type='checkbox'; cb.checked = true; cb.dataset.chain=c;
    cb.onchange = () => toggleChain(c, cb.checked);
    lbl.appendChild(cb);
    lbl.appendChild(document.createTextNode(' Chain ' + c + ' ('+(m.chain_types[c]||'')+')'));
    div.appendChild(lbl);
    const opt1 = document.createElement('option'); opt1.value=c; opt1.text=c;
    const opt2 = document.createElement('option'); opt2.value=c; opt2.text=c;
    fromSel.appendChild(opt1); toSel.appendChild(opt2);
  }});
  if (m.chains.length>=2) {{ toSel.selectedIndex = 1; }}
}}

function toggleChain(chain, visible) {{
  if (!modelObj) return;
  if (visible) {{
    viewer.setStyle({{chain: chain, resn:['A','U','G','C','DA','DT','DG','DC','I','DI','5MC','PSU']}}, {{stick:{{}}}});
    viewer.setStyle({{chain: chain, not:{{resn:['A','U','G','C','DA','DT','DG','DC','I','DI','5MC','PSU']}}}}, {{cartoon:{{}}}});
  }} else {{
    viewer.setStyle({{chain: chain}}, {{}});
  }}
  viewer.render();
}}

function applyColor() {{
  const scheme = document.getElementById('colorScheme').value;
  if (!modelObj) return;
  viewer.setStyle({{}}, {{}});
  viewer.setStyle({{resn:['A','U','G','C','DA','DT','DG','DC','I','DI','5MC','PSU']}}, {{stick:{{}}}});
  let styleProtein = {{"cartoon":{{}}}};
  if (scheme === 'chain') {{
    styleProtein = {{"cartoon":{{colorscheme:'chain'}}}};
  }} else if (scheme === 'ss') {{
    styleProtein = {{"cartoon":{{colorscheme:'ssPyMOL'}}}};
  }} else if (scheme === 'bfactor') {{
    styleProtein = {{"cartoon":{{colorscheme:{{prop:'b',gradient:'roygb'}}}}}};
  }}
  viewer.setStyle({{not: {{resn:['A','U','G','C','DA','DT','DG','DC','I','DI','5MC','PSU']}}}}, styleProtein);
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
  a.download = 'boltz2_view.png';
  a.click();
}}

function downloadPDB() {{
  const m = MODELS.find(x => x.id == currentModelId);
  if (!m) return;
  const blob = new Blob([m.pdb], {{type:'chemical/x-pdb'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = (m.name || 'model') + '.pdb';
  a.click();
  setTimeout(()=> URL.revokeObjectURL(url), 1000);
}}

document.addEventListener('DOMContentLoaded', initViewer);
</script>
</body>
</html>
"""
    return html_text

def main():
    args = parse_args()
    models = []
    for i, pth in enumerate(args.pdb):
        p = Path(pth)
        if not p.exists():
            raise SystemExit(f"PDB not found: {p}")
        pdb_text = p.read_text()
        meta = analyze_pdb(pdb_text)
        models.append({
            "id": i,
            "name": p.name,
            "pdb": pdb_text,
            "chains": meta["chains"],
            "chain_types": meta["chain_types"]
        })
    html_text = build_html(models, args.title)
    out = Path(args.out)
    out.write_text(html_text, encoding="utf-8")
    print(f"Wrote {out.resolve()}")

if __name__ == "__main__":
    main()
