
const BULK = DATA.coho, SCN = DATA.scl, GENES = DATA.genes;
const GS = {"g_empty":{"en":"Please enter a gene symbol.","zh":"请输入基因符号。"},"g_notfound":{"en":"No match for","zh":"未找到"},"g_suggest":{"en":"Did you mean:","zh":"可能："},"g_nosim":{"en":"No similar symbols.","zh":"无相似符号。"},"g_bulk_t":{"en":"Bulk: 16 cohorts (primary contrasts)","zh":"Bulk：16 队列（主对比）"},"g_th_cohort":{"en":"Cohort","zh":"队列"},"g_th_contrast":{"en":"Contrast (dataset · cell type · design)","zh":"对比（数据集 · 细胞类型 · 设计）"},"g_th_comp":{"en":"Compartment","zh":"区室"},"g_th_desc":{"en":"logFC (donor-level, descriptive)","zh":"logFC（供体级描述值）"},"g_limit_badge":{"en":"⚠ limit below","zh":"⚠ 限制见下"},"g_bulk_chart":{"en":"Bulk logFC bar chart","zh":"Bulk logFC 条形图"},"g_sc_t":{"en":"Single-cell: cell-type-level contrasts","zh":"单细胞：细胞类型级对比"},"g_bulk_nm":{"en":"This gene is not in the bulk evidence matrix (not measured).","zh":"该基因不在 bulk 证据矩阵中（未测得）。"},"g_sc_nm":{"en":"This gene is not in the single-cell evidence matrix (not measured).","zh":"该基因不在单细胞证据矩阵中（未测得）。"},"g_sp_t":{"en":"Spatial (GeoMx, GSE235714)","zh":"空间（GeoMx，GSE235714）"},"g_cd45":{"en":"CD45+ immune compartment","zh":"CD45+ 免疫区室"},"g_panck":{"en":"PanCK+ epithelial compartment","zh":"PanCK+ 上皮区室"},"g_sp_cav":{"en":"⚠ Spatial layer limits: donor-level FDR&lt;0.05 is zero in both compartments (6 vs 4 donors); these are descriptive values, not independent evidence; disease and tissue are fully confounded (CRSwNP = polyp tissue vs controls = ethmoid tissue).","zh":"⚠ 空间层限制：两区室供体级 FDR&lt;0.05 均为 0（6v4 供体），此为描述性值，非独立证据；且疾病与组织完全混杂（CRSwNP=息肉组织 vs 对照=筛窦组织）。"},"g_notpanel":{"en":"This gene is <b>not in the GeoMx CTA panel (1,480 genes)</b> — no spatial data, not a missing value.","zh":"该基因<b>不在 GeoMx CTA panel（1,480 基因）中</b>——无空间数据，非缺失值。"},"g_lim_colon":{"en":"limitation:","zh":"限制："},"gpw_t":{"en":"Pathways &amp; consensus","zh":"通路与共识"},"gpw_path":{"en":"Pathways containing this gene, enriched (FDR&lt;0.05) in ≥2 contrasts","zh":"含该基因且在 ≥2 个对比中富集（FDR&lt;0.05）的通路"},"gpw_cons":{"en":"Consensus list","zh":"共识基因清单"},"gpw_cons_up":{"en":"consensus UP (one of 825 genes up-regulated across cohorts)","zh":"共识上调（跨队列上调 825 基因之一）"},"gpw_cons_down":{"en":"consensus DOWN (one of 196 genes down-regulated across cohorts)","zh":"共识下调（跨队列下调 196 基因之一）"},"gpw_cons_no":{"en":"Not in the consensus list.","zh":"不在共识基因清单中。"},"gpw_target":{"en":"Known drug target","zh":"已知药物靶点"},"gpw_ncol":{"en":"contrasts","zh":"对比数"},"path_th_term":{"en":"Pathway term","zh":"通路"},"path_th_db":{"en":"Database / collection","zh":"数据库/集合"}}, CAV = {"cav_GSE198950":{"en":"Tissue confounding: cases are ethmoid tissue, controls are inferior turbinate — the significant reversal of IL33/POSTN may stem from this; must be stated when used.","zh":"组织混杂：病例为筛窦组织、对照为下鼻甲组织——IL33/POSTN 显著反向可能源于此，使用时必须注明。"},"cav_GSE189690":{"en":"No healthy controls: disease-subtype contrast only; excluded from case–control directional priors.","zh":"无健康对照：仅疾病亚型对比，不参与病例-对照方向先验。"},"cav_GSE330761":{"en":"No healthy controls; sorted mast-cell subset atlas (3v3).","zh":"无健康对照；分选肥大细胞亚群图谱型（3v3）。"},"cav_GSE69093":{"en":"Primary cultured cells: zero transcriptome-wide significant genes but p-values enriched at the small-p end — judged a genuine weak signal (not a technical error). Series platform was mislabeled at registration (Affymetrix); corrected to Illumina HumanHT-12 v4 annotation.","zh":"原代培养细胞：全转录组 0 显著但 p 值富集于小 p 端，判为真实弱信号（非技术错误）。系列注册平台误标（Affymetrix），已按 Illumina HumanHT-12 v4 注释修正。"}};
function pa_lang(){ try{ return localStorage.getItem('pa_lang') || 'en'; }catch(e){ return 'en'; } }
function gs(k){ const l = pa_lang(); const d = GS[k]; return d ? (d[l]!==undefined ? d[l] : d.en) : k; }
function cavtxt(id){ const l = pa_lang(); const d = CAV['cav_'+id]; return d ? d[l] : ''; }
function fmt(v, d){ if(v==null) return '<span style="color:#aaa">—</span>'; return Number(v).toFixed(d); }
function badge(f){ if(f==null) return ''; if(f<0.05) return '<span class="badge sig">FDR<0.05</span>'; return '<span class="badge nonsig">ns</span>'; }
function searchGene(g0){
  let q = (g0 || document.getElementById('q').value || '').trim().toUpperCase();
  const box = document.getElementById('result');
  if(!q){ box.innerHTML = '<p>'+gs('g_empty')+'</p>'; window._lastGene = null; return; }
  let key = Object.keys(GENES).find(k => k.toUpperCase() === q);
  if(!key){ // prefix suggestions
    let cand = Object.keys(GENES).filter(k => k.toUpperCase().startsWith(q)).slice(0,20);
    box.innerHTML = '<p>'+gs('g_notfound')+' <b>'+q+'</b>.' + (cand.length? ' '+gs('g_suggest')+' '+cand.map(c=>`<a href="#" onclick="searchGene('${c}');return false;">${c}</a>`).join('、') : ' '+gs('g_nosim')) + '</p>';
    window._lastGene = null; return;
  }
  window._lastGene = key;
  document.getElementById('q').value = key;
  const r = GENES[key];
  let html = '<div class="card"><h3>'+key+'</h3>';
  // bulk table + chart
  html += '<h3>'+gs('g_bulk_t')+'</h3><table><tr><th>'+gs('g_th_cohort')+'</th><th>logFC</th><th>FDR</th><th></th></tr>';
  const vals = [];
  if(r.b){
    BULK.forEach((c,i)=>{
      const e = r.b[i]; vals.push(e?e[0]:null);
      const ntxt = c['n_'+pa_lang()] || c.n_en || c.n_zh;
      html += '<tr><td>'+c.id+'<br><span style="font-size:12px;color:#666">'+ntxt+'</span>'
        + (c.caveat? '<br><span class="badge warn">'+gs('g_limit_badge')+'</span>' : '') + '</td>'
        + '<td>'+fmt(e?e[0]:null,3)+'</td><td>'+fmt(e?e[1]:null,4)+'</td><td>'+badge(e?e[1]:null)+'</td></tr>';
    });
  } else html += '<tr><td colspan="4">'+gs('g_bulk_nm')+'</td></tr>';
  html += '</table>';
  const caveats = BULK.filter(c=>c.caveat && r.b && BULK.indexOf(c)<r.b.length && r.b[BULK.indexOf(c)]);
  const shown = [...new Set(caveats.map(c=>'<div class="caveat">'+cavtxt(c.id)+'</div>'))];
  if(shown.length) html += shown.join('');
  html += '<h3>'+gs('g_bulk_chart')+'</h3><canvas id="cv" width="900" height="340"></canvas></div>';
  // pathways & consensus block
  html += '<div class="card"><h3>'+gs('gpw_t')+'</h3>';
  const pw = (typeof GENEPW!=='undefined') ? GENEPW[key] : null;
  if(pw && pw.length){
    html += '<p><b>'+gs('gpw_path')+'</b></p><table><tr><th>'+gs('path_th_term')+'</th><th>'+gs('path_th_db')+'</th><th>'+gs('gpw_ncol')+'</th></tr>';
    pw.forEach(function(p){ html += '<tr><td>'+p[0]+'</td><td>'+p[1]+'</td><td>'+p[3]+'</td></tr>'; });
    html += '</table>';
  } else html += '<p style="color:#888">—</p>';
  const cs = (typeof CONS!=='undefined') ? CONS[key] : null;
  html += '<p><b>'+gs('gpw_cons')+':</b> ';
  if(cs){ html += (cs.d==='up' ? gs('gpw_cons_up') : gs('gpw_cons_down'));
    if(cs.t) html += ' · <span class="badge sig">'+gs('gpw_target')+': '+cs.t+'</span>';
  } else html += gs('gpw_cons_no');
  html += '</p></div>';
  // sc table
  html += '<div class="card"><h3>'+gs('g_sc_t')+'</h3>';
  if(r.s){
    html += '<table><tr><th>'+gs('g_th_contrast')+'</th><th>logFC</th><th>FDR</th><th></th></tr>';
    Object.keys(r.s).forEach(i=>{
      const e = r.s[i];
      html += '<tr><td>'+SCN[+i]+'</td><td>'+fmt(e[0],3)+'</td><td>'+fmt(e[1],4)+'</td><td>'+badge(e[1])+'</td></tr>';
    });
    html += '</table>';
  } else html += '<p>'+gs('g_sc_nm')+'</p>';
  html += '</div>';
  // spatial
  html += '<div class="card"><h3>'+gs('g_sp_t')+'</h3>';
  if(r.sp){
    html += '<table><tr><th>'+gs('g_th_comp')+'</th><th>'+gs('g_th_desc')+'</th><th>FDR</th></tr>'
      + '<tr><td>'+gs('g_cd45')+'</td><td>'+fmt(r.sp[0],3)+'</td><td>'+fmt(r.sp[1],4)+'</td></tr>'
      + '<tr><td>'+gs('g_panck')+'</td><td>'+fmt(r.sp[2],3)+'</td><td>'+fmt(r.sp[3],4)+'</td></tr></table>'
      + '<div class="caveat">'+gs('g_sp_cav')+'</div>';
  } else html += '<p>'+gs('g_notpanel')+'</p>';
  html += '</div>';
  box.innerHTML = html;
  drawChart(vals);
}
function drawChart(vals){
  const cv = document.getElementById('cv'); if(!cv) return;
  const ctx = cv.getContext('2d');
  const W = cv.width, H = cv.height;
  const maxA = Math.max(0.5, ...vals.filter(v=>v!=null).map(Math.abs));
  const bw = W / BULK.length;
  ctx.clearRect(0,0,W,H);
  ctx.fillStyle = '#666'; ctx.font = '11px sans-serif';
  const zero = H/2;
  ctx.strokeStyle = '#999'; ctx.beginPath(); ctx.moveTo(0,zero); ctx.lineTo(W,zero); ctx.stroke();
  BULK.forEach((c,i)=>{
    const v = vals[i]; if(v==null) return;
    const h = (v/maxA)*(H/2-24);
    ctx.fillStyle = v>0 ? '#d45a5a' : '#5a8fd4';
    ctx.fillRect(i*bw+4, v>0? zero-h : zero, bw-8, Math.abs(h));
    ctx.save(); ctx.translate(i*bw+bw/2, H-4); ctx.rotate(-0.5);
    ctx.fillStyle='#333'; ctx.fillText(c.id.split('_')[0], 0, 0); ctx.restore();
  });
}
document.getElementById('q').addEventListener('keydown', e=>{ if(e.key==='Enter') searchGene(); });
// re-render results when the page language changes (wired from the inline i18n script)
window.PA_langChanged = function(){ if(window._lastGene) searchGene(window._lastGene); };
