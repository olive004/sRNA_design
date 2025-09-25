#!/usr/bin/env python3
"""
boltz2_struct_viewer.py — Build a shareable HTML to explore Boltz-2 outputs.

Inputs (files from a single run):
  - job.cif                        (structure)
  - confidence.json                (ptm, iptm, ligand_iptm, complex_plddt, etc.)
  - pae.npz  (key='pae',  [n,n])   (Predicted Aligned Error)
  - pde.npz  (key='pde',  [n,n])   (Predicted Distance Error)  [optional]
  - plddt.npz (key='plddt',(n,))   (per-residue pLDDT)         [optional]

Usage:
  python boltz2_struct_viewer.py \
    --cif job.cif --conf confidence.json \
    --pae pae.npz --pde pde.npz --plddt plddt.npz \
    --out viewer.html --title "Boltz-2 result"

The resulting HTML loads 3Dmol.js from a CDN.

python boltz2_struct_viewer.py \
  --cif /home/hslab/Olive/Kode/sRNA_design/notebooks/boltz/results/boltz_results_bzjob_1_hfq_hex_cyrfp1/predictions/bzjob_1_hfq_hex_cyrfp1/bzjob_1_hfq_hex_cyrfp1_model_0.cif \
  --conf /home/hslab/Olive/Kode/sRNA_design/notebooks/boltz/results/boltz_results_bzjob_1_hfq_hex_cyrfp1/predictions/bzjob_1_hfq_hex_cyrfp1/confidence_bzjob_1_hfq_hex_cyrfp1_model_0.json \
  --pae /home/hslab/Olive/Kode/sRNA_design/notebooks/boltz/results/boltz_results_bzjob_1_hfq_hex_cyrfp1/predictions/bzjob_1_hfq_hex_cyrfp1/pae_bzjob_1_hfq_hex_cyrfp1_model_0.npz \
  --pde /home/hslab/Olive/Kode/sRNA_design/notebooks/boltz/results/boltz_results_bzjob_1_hfq_hex_cyrfp1/predictions/bzjob_1_hfq_hex_cyrfp1/pde_bzjob_1_hfq_hex_cyrfp1_model_0.npz \
  --plddt /home/hslab/Olive/Kode/sRNA_design/notebooks/boltz/results/boltz_results_bzjob_1_hfq_hex_cyrfp1/predictions/bzjob_1_hfq_hex_cyrfp1/plddt_bzjob_1_hfq_hex_cyrfp1_model_0.npz \
  --out viewer.html \
  --title "Boltz-2 result"

"""

from pathlib import Path
import argparse
import json
import base64
import numpy as np

def f32_to_b64(a: np.ndarray) -> dict:
    a = np.asarray(a, dtype=np.float32)
    b = a.tobytes(order='C')
    s = base64.b64encode(b).decode('ascii')
    return {"shape": list(a.shape), "dtype": "f32", "b64": s}

def main():
    ap = argparse.ArgumentParser(description="Generate an interactive 3D HTML viewer for Boltz-2 outputs (with PAE/PDE/PLDDT).")
    ap.add_argument("--cif", required=True, help="Path to job.cif (structure)")
    ap.add_argument("--conf", required=False, help="Path to confidence.json")
    ap.add_argument("--pae", required=False, help="Path to pae.npz (key='pae')")
    ap.add_argument("--pde", required=False, help="Path to pde.npz (key='pde')")
    ap.add_argument("--plddt", required=False, help="Path to plddt.npz (key='plddt')")
    ap.add_argument("--out", default="boltz2_view.html", help="Output HTML file")
    ap.add_argument("--title", default="Boltz-2 Structure Viewer", help="Page title")
    args = ap.parse_args()

    cif_text = Path(args.cif).read_text(encoding='utf-8', errors='ignore')

    conf_data = {}
    if args.conf and Path(args.conf).exists():
        conf_data = json.loads(Path(args.conf).read_text(encoding='utf-8', errors='ignore'))

    pae_data = None
    if args.pae and Path(args.pae).exists():
        with np.load(args.pae) as z:
            if "pae" in z:
                pae_data = f32_to_b64(z["pae"])
            else:
                raise SystemExit("PAE npz missing key 'pae'")

    pde_data = None
    if args.pde and Path(args.pde).exists():
        with np.load(args.pde) as z:
            if "pde" in z:
                pde_data = f32_to_b64(z["pde"])
            else:
                raise SystemExit("PDE npz missing key 'pde'")

    plddt_vec = None
    if args.plddt and Path(args.plddt).exists():
        with np.load(args.plddt) as z:
            if "plddt" in z:
                plddt_vec = f32_to_b64(z["plddt"])
            else:
                raise SystemExit("PLDDT npz missing key 'plddt'")

    html = build_html(
        title=args.title,
        cif_text=cif_text,
        conf_data=conf_data,
        pae=pae_data,
        pde=pde_data,
        plddt=plddt_vec,
    )
    Path(args.out).write_text(html, encoding='utf-8')
    print(f"Wrote {Path(args.out).resolve()}")

def build_html(*, title, cif_text, conf_data, pae, pde, plddt):
    import html as _html
    def jsjson(x): 
        return json.dumps(x).replace("</", "<\\/")  # prevent </script> breaks

    css = """
    :root { --bg:#0b0f14; --panel:#0e141b; --card:#111827; --ink:#e5e7eb; --muted:#9ca3af; --border:#1f2937; }
    body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,sans-serif;background:var(--bg);color:var(--ink)}
    header{display:flex;align-items:center;gap:12px;padding:10px 14px;border-bottom:1px solid var(--border);background:var(--panel);position:sticky;top:0;z-index:10}
    #wrap{display:grid;grid-template-columns:340px 1fr; gap:12px; height:calc(100vh - 60px)}
    aside{padding:10px 12px;border-right:1px solid var(--border);overflow:auto;background:var(--panel)}
    main{position:relative}
    #viewer{position:absolute;inset:0;background:#101826}
    h2{font-size:14px;margin:10px 0 6px 0;color:var(--ink)}
    .group{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:8px;margin-bottom:10px}
    .row{display:flex; flex-wrap:wrap; gap:8px; align-items:center}
    .label{font-size:12px;color:var(--muted)}
    select,input[type=number],input[type=range]{background:var(--bg);border:1px solid var(--border);border-radius:10px;color:var(--ink);padding:6px 8px}
    button{background:var(--card);border:1px solid var(--border);border-radius:10px;color:var(--ink);padding:6px 10px;cursor:pointer}
    button:hover{filter:brightness(1.08)}
    table{width:100%;border-collapse:collapse;font-size:12px}
    td{border-top:1px solid var(--border);padding:4px 6px}
    canvas{image-rendering:pixelated;border:1px solid var(--border);border-radius:8px;background:#0b0f14}
    .legend{display:flex;gap:6px;align-items:center;font-size:12px;color:var(--muted)}
    .swatch{width:12px;height:12px;border-radius:3px;border:1px solid var(--border)}
    .small{font-size:11px;color:var(--muted)}
    """

    metrics_rows = ""
    if isinstance(conf_data, dict):
        for k,v in conf_data.items():
            if isinstance(v,(int,float)):
                metrics_rows += f"<tr><td>{_html.escape(str(k))}</td><td style='text-align:right'>{v:.4f}</td></tr>"
            else:
                metrics_rows += f"<tr><td>{_html.escape(str(k))}</td><td class='small'>{_html.escape(str(v))}</td></tr>"

    # Prepare payloads
    payload = {
        "title": title,
        "cif": {"name": "job.cif", "format": "cif", "text": cif_text},
        "conf": conf_data,
        "pae": pae,
        "pde": pde,
        "plddt": plddt,
    }

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{_html.escape(title)}</title>
<style>{css}</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.3.0/3Dmol-min.min.js"></script>
</head>
<body>
<header>
  <strong style="font-size:14px">{_html.escape(title)}</strong>
</header>
<div id="wrap">
  <aside>
    <div class="group">
      <h2>Coloring</h2>
      <div class="row">
        <span class="label">Mode</span>
        <select id="colorMode">
          <option value="chain">By chain</option>
          <option value="ss">Secondary structure</option>
          <option value="bfactor">B-factor</option>
          <option value="plddt">pLDDT</option>
          <option value="pae">PAE row</option>
          <option value="pde">PDE row</option>
        </select>
      </div>
      <div class="row" style="margin-top:8px">
        <span class="label">Residue index</span>
        <input type="range" id="resSlider" value="0" min="0" max="0" step="1" style="flex:1"/>
        <input type="number" id="resIdx" value="0" min="0" max="0" step="1" style="width:70px"/>
      </div>
      <div class="row small" id="resMappingInfo" style="margin-top:4px"></div>

      <div class="row" style="margin-top:8px">
        <button id="resetView">Reset view</button>
        <button id="downloadCIF">Download CIF</button>
        <button id="png">Snapshot PNG</button>
      </div>
    </div>

    <div class="group">
      <h2>pLDDT Legend</h2>
      <div class="legend"><div class="swatch" style="background:#8B0000"></div><span>0–50 (very low)</span></div>
      <div class="legend"><div class="swatch" style="background:#FFA500"></div><span>50–70 (low)</span></div>
      <div class="legend"><div class="swatch" style="background:#FFD700"></div><span>70–90 (confident)</span></div>
      <div class="legend"><div class="swatch" style="background:#1E90FF"></div><span>90–100 (very high)</span></div>
    </div>

    <div class="group">
      <h2>PAE/PDE Heatmap</h2>
      <div class="row">
        <select id="matrixKind">
          <option value="pae">PAE</option>
          <option value="pde">PDE</option>
        </select>
        <span class="small" id="matrixNote">Click a row to color by that residue</span>
      </div>
      <canvas id="hm" width="256" height="256" style="margin-top:6px"></canvas>
      <div class="row small" style="margin-top:6px">
        <span>Low</span>
        <div class="swatch" style="background:#00A651"></div>
        <div class="swatch" style="background:#FFD400"></div>
        <div class="swatch" style="background:#E4002B"></div>
        <span>High</span>
      </div>
      <div class="small" id="hmStatus" style="margin-top:4px;min-height:16px"></div>
    </div>

    <div class="group">
      <h2>Confidence metrics</h2>
      <table>
        <tbody>
          {metrics_rows or "<tr><td colspan='2' class='small'>No confidence.json provided</td></tr>"}
        </tbody>
      </table>
    </div>
  </aside>

  <main>
    <div id="viewer"></div>
  </main>
</div>

<script>
const PAYLOAD = {jsjson(payload)};

// ----------- helpers: Float32 decoding & colormaps -----------
function decodeF32(obj) {{
  if (!obj) return null;
  const bin = atob(obj.b64);
  const len = bin.length;
  const buf = new ArrayBuffer(len);
  const view = new Uint8Array(buf);
  for (let i=0;i<len;i++) view[i] = bin.charCodeAt(i);
  return {{shape: obj.shape, data: new Float32Array(buf)}};
}}

function clamp(x,a,b){{return Math.max(a, Math.min(b,x));}}

function rgb(r,g,b){{ return '#' + [r,g,b].map(v=>(('0'+v.toString(16)).slice(-2))).join(''); }}
function lerp(a,b,t){{ return a + (b-a)*t; }}
function lerp3(c1,c2,t){{ return [Math.round(lerp(c1[0],c2[0],t)), Math.round(lerp(c1[1],c2[1],t)), Math.round(lerp(c1[2],c2[2],t))]; }}

// AlphaFold-like pLDDT palette (simplified)
function colorPLDDT(v) {{
  if (v < 50) return '#8B0000';         // dark red
  if (v < 70) return '#FFA500';         // orange
  if (v < 90) return '#FFD700';         // gold
  return '#1E90FF';                     // dodger blue
}}

// PAE palette: 0->green, 15->yellow, 30->red
function colorPAE(v) {{
  const x = clamp(v, 0, 30) / 30.0;
  if (x < 0.5) {{
    const t = x/0.5;                    // green->yellow
    return rgb(...lerp3([0,166,81],[255,212,0],t));
  }} else {{
    const t = (x-0.5)/0.5;              // yellow->red
    return rgb(...lerp3([255,212,0],[228,0,43],t));
  }}
}}

// PDE palette: reuse PAE palette for now
function colorPDE(v) {{ return colorPAE(v); }}

// ----------- viewer state -----------
let viewer = null, model = null;
let residues = [];  // array of {{chain, resi, icode}}
let plddt = null;
let pae = null, pde = null;
let nRes = 0;
let selectedIdx = 0;

// ----------- init -----------
function init() {{
  pae = decodeF32(PAYLOAD.pae);
  pde = decodeF32(PAYLOAD.pde);
  plddt = decodeF32(PAYLOAD.plddt);

  // init viewer
  viewer = $3Dmol.createViewer("viewer", {{ backgroundColor: "#101826", antialias: true }});
  model = viewer.addModel(PAYLOAD.cif.text, PAYLOAD.cif.format);
  // default styling: nucleic sticks, protein cartoon
  const NUC = ['A','U','G','C','DA','DT','DG','DC','I','DI','5MC','PSU'];
  viewer.setStyle({{resn:NUC}}, {{stick:{{}}}});
  viewer.setStyle({{not: {{resn:NUC}}}}, {{cartoon:{{}}}});

  buildResidueIndex();
  setColorMode(document.getElementById('colorMode').value);
  viewer.zoomTo();
  viewer.render();

  // UI wiring
  const slider = document.getElementById('resSlider');
  const idxBox = document.getElementById('resIdx');
  const colorMode = document.getElementById('colorMode');
  const matrixKind = document.getElementById('matrixKind');

  slider.max = Math.max(0, nRes-1);
  idxBox.max = Math.max(0, nRes-1);

  slider.oninput = () => {{ idxBox.value = slider.value; onResidueChange(parseInt(slider.value)); }};
  idxBox.onchange = () => {{ const v = clamp(parseInt(idxBox.value)||0,0,nRes-1); slider.value = v; onResidueChange(v); }};
  colorMode.onchange = () => setColorMode(colorMode.value);

  document.getElementById('resetView').onclick = () => {{ viewer.zoomTo(); viewer.render(); }};
  document.getElementById('png').onclick = () => {{
    const a = document.createElement('a'); a.href = viewer.pngURI(); a.download = 'boltz2.png'; a.click();
  }};
  document.getElementById('downloadCIF').onclick = () => {{
    const blob = new Blob([PAYLOAD.cif.text], {{type:'chemical/x-cif'}});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href=url; a.download=PAYLOAD.cif.name; a.click();
    setTimeout(()=>URL.revokeObjectURL(url), 1000);
  }};

  drawHeatmap();
  matrixKind.onchange = drawHeatmap;
  const hm = document.getElementById('hm');
  hm.addEventListener('mousemove', onHmHover);
  hm.addEventListener('mouseleave', ()=> setHmStatus(''));
  hm.addEventListener('click', onHmClick);

  setMappingInfo();
}}

function setMappingInfo() {{
  const el = document.getElementById('resMappingInfo');
  el.textContent = "Residues mapped by (first-occur) unique (chain,resi,icode). Size n=" + nRes + (plddt? ", pLDDT n="+plddt.shape[0]:"") + (pae? ", PAE n="+pae.shape[0]:"");
}}

function buildResidueIndex() {{
  const atoms = model.selectedAtoms({{}});
  const seen = new Set();
  const list = [];
  for (const a of atoms) {{
    const key = (a.chain||'') + '|' + (a.resi||0) + '|' + (a.icode||'');
    if (!seen.has(key)) {{ seen.add(key); list.push({{chain:a.chain,resi:a.resi,icode:a.icode||''}}); }}
  }}
  residues = list;
  nRes = residues.length;
  document.getElementById('resSlider').max = Math.max(0, nRes-1);
  document.getElementById('resIdx').max = Math.max(0, nRes-1);
}}

// ----------- coloring modes -----------
function resetBaseStyles() {{
  const NUC = ['A','U','G','C','DA','DT','DG','DC','I','DI','5MC','PSU'];
  viewer.setStyle({{}}, {{}});
  viewer.setStyle({{resn:NUC}}, {{stick:{{}}}});
  viewer.setStyle({{not: {{resn:NUC}}}}, {{cartoon:{{}}}});
}}

function setColorMode(mode) {{
  resetBaseStyles();
  if (mode === 'chain') {{
    viewer.setStyle({{not: {{}}}}, {{cartoon:{{colorscheme:'chain'}}}});
  }} else if (mode === 'ss') {{
    viewer.setStyle({{not: {{}}}}, {{cartoon:{{colorscheme:'ssPyMOL'}}}});
  }} else if (mode === 'bfactor') {{
    viewer.setStyle({{not: {{}}}}, {{cartoon:{{colorscheme:{{prop:'b',gradient:'roygb'}}}}}});
  }} else if (mode === 'plddt') {{
    colorByPLDDT();
  }} else if (mode === 'pae' || mode === 'pde') {{
    colorByMatrixRow(selectedIdx, mode);
  }}
  viewer.render();
}}

function onResidueChange(i) {{
  selectedIdx = clamp(i,0,nRes-1);
  const mode = document.getElementById('colorMode').value;
  if (mode === 'pae' || mode === 'pde') {{
    colorByMatrixRow(selectedIdx, mode);
  }}
}}

function colorByPLDDT() {{
  if (!plddt || plddt.shape[0] !== nRes) return;
  resetBaseStyles();
  for (let j=0;j<nRes;j++) {{
    const sel = residues[j];
    const v = plddt.data[j];
    const c = colorPLDDT(v);
    viewer.setStyle({{chain: sel.chain, resi: sel.resi}}, {{cartoon:{{color:c}}, stick:{{colorscheme: c}}}});
  }}
  viewer.render();
}}

function colorByMatrixRow(i, kind) {{
  const obj = (kind==='pae'? pae : pde);
  if (!obj) return;
  const n = obj.shape[0];
  if (n !== nRes) {{
    setHmStatus(kind.toUpperCase()+" size ("+n+") does not match residue count ("+nRes+").");
    return;
  }}
  resetBaseStyles();
  const row = obj.data.subarray(i*n, (i+1)*n);
  for (let j=0;j<nRes;j++) {{
    const sel = residues[j];
    const v = row[j];
    const col = (kind==='pae'? colorPAE(v) : colorPDE(v));
    viewer.setStyle({{chain: sel.chain, resi: sel.resi}}, {{cartoon:{{color:col}}, stick:{{colorscheme: col}}}});
  }}
  viewer.render();
}}

// ----------- heatmap drawing -----------
function getActiveMatrix() {{
  const kind = document.getElementById('matrixKind').value;
  const obj = (kind==='pae'? pae : pde);
  return {{kind, obj}};
}}

function drawHeatmap() {{
  const canvas = document.getElementById('hm');
  const ctx = canvas.getContext('2d');
  const {{kind, obj}} = getActiveMatrix();
  ctx.clearRect(0,0,canvas.width,canvas.height);
  if (!obj) {{
    ctx.fillStyle = '#444';
    ctx.fillText('No '+kind.toUpperCase()+' data', 10, 20);
    return;
  }}
  const n = obj.shape[0];
  const img = ctx.createImageData(canvas.width, canvas.height);
  // Map matrix to canvas pixels
  for (let y=0; y<canvas.height; y++) {{
    const j = Math.floor(y * n / canvas.height);
    for (let x=0; x<canvas.width; x++) {{
      const i = Math.floor(x * n / canvas.width);
      const v = obj.data[j*n + i];
      const col = (kind==='pae'? colorPAE(v) : colorPDE(v));
      const r = parseInt(col.slice(1,3),16);
      const g = parseInt(col.slice(3,5),16);
      const b = parseInt(col.slice(5,7),16);
      const idx = (y*canvas.width + x)*4;
      img.data[idx+0]=r; img.data[idx+1]=g; img.data[idx+2]=b; img.data[idx+3]=255;
    }}
  }}
  ctx.putImageData(img,0,0);
  // Crosshair for selected index
  if (nRes>0) {{
    const x = Math.round(selectedIdx * canvas.width / nRes);
    const y = Math.round(selectedIdx * canvas.height / nRes);
    ctx.strokeStyle = '#ffffff99';
    ctx.beginPath();
    ctx.moveTo(x,0); ctx.lineTo(x,canvas.height);
    ctx.moveTo(0,y); ctx.lineTo(canvas.width,y);
    ctx.stroke();
  }}
}}

function setHmStatus(msg) {{
  document.getElementById('hmStatus').textContent = msg || '';
}}

function onHmHover(ev) {{
  const canvas = ev.target;
  const rect = canvas.getBoundingClientRect();
  const u = (ev.clientX - rect.left)/canvas.width;
  const v = (ev.clientY - rect.top)/canvas.height;
  const {{obj, kind}} = getActiveMatrix();
  if (!obj) return;
  const n = obj.shape[0];
  const i = Math.floor(u * n);
  const j = Math.floor(v * n);
  const val = obj.data[j*n + i];
  setHmStatus(kind.toUpperCase()+`[${{j}},${{i}}] = `+val.toFixed(2));
}}

function onHmClick(ev) {{
  const canvas = ev.target;
  const rect = canvas.getBoundingClientRect();
  const v = (ev.clientY - rect.top)/canvas.height;
  const {{obj}} = getActiveMatrix();
  if (!obj) return;
  const n = obj.shape[0];
  const row = Math.floor(v * n);
  const slider = document.getElementById('resSlider');
  const idxBox = document.getElementById('resIdx');
  const clamped = clamp(row,0,nRes-1);
  slider.value = clamped; idxBox.value = clamped;
  onResidueChange(clamped);
  drawHeatmap();
}}

// Kickoff
document.addEventListener('DOMContentLoaded', init);
</script>

</body>
</html>
"""
    return html

if __name__ == "__main__":
    main()
