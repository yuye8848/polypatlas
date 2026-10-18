
const BULK = DATA.coho, SCN = DATA.scl, GENES = DATA.genes;
const GS = {"g_empty":{"en":"Please enter a gene symbol.","zh":"请输入基因符号。"},"g_notfound":{"en":"No match for","zh":"未找到"},"g_suggest":{"en":"Did you mean:","zh":"可能："},"g_nosim":{"en":"No similar symbols.","zh":"无相似符号。"},"g_bulk_t":{"en":"Bulk: 16 cohorts (primary contrasts)","zh":"Bulk：16 队列（主对比）"},"g_th_cohort":{"en":"Cohort","zh":"队列"},"g_th_contrast":{"en":"Contrast (dataset · cell type · design)","zh":"对比（数据集 · 细胞类型 · 设计）"},"g_th_comp":{"en":"Compartment","zh":"区室"},"g_th_desc":{"en":"logFC (donor-level, descriptive)","zh":"logFC（供体级描述值）"},"g_limit_badge":{"en":"⚠ limit below","zh":"⚠ 限制见下"},"g_bulk_chart":{"en":"Bulk logFC bar chart","zh":"Bulk logFC 条形图"},"g_sc_t":{"en":"Single-cell: cell-type-level contrasts","zh":"单细胞：细胞类型级对比"},"g_bulk_nm":{"en":"This gene is not in the bulk evidence matrix (not measured).","zh":"该基因不在 bulk 证据矩阵中（未测得）。"},"g_sc_nm":{"en":"This gene is not in the single-cell evidence matrix (not measured).","zh":"该基因不在单细胞证据矩阵中（未测得）。"},"g_sp_t":{"en":"Spatial (GeoMx, GSE235714)","zh":"空间（GeoMx，GSE235714）"},"g_cd45":{"en":"CD45+ immune compartment","zh":"CD45+ 免疫区室"},"g_panck":{"en":"PanCK+ epithelial compartment","zh":"PanCK+ 上皮区室"},"g_sp_cav":{"en":"⚠ Spatial layer limits: donor-level FDR&lt;0.05 is zero in both compartments (6 vs 4 donors); these are descriptive values, not independent evidence; disease and tissue are fully confounded (CRSwNP = polyp tissue vs controls = ethmoid tissue).","zh":"⚠ 空间层限制：两区室供体级 FDR&lt;0.05 均为 0（6v4 供体），此为描述性值，非独立证据；且疾病与组织完全混杂（CRSwNP=息肉组织 vs 对照=筛窦组织）。"},"g_notpanel":{"en":"This gene is <b>not in the GeoMx CTA panel (1,480 genes)</b> — no spatial data, not a missing value.","zh":"该基因<b>不在 GeoMx CTA panel（1,480 基因）中</b>——无空间数据，非缺失值。"},"g_lim_colon":{"en":"limitation:","zh":"限制："},"gpw_t":{"en":"Pathways &amp; consensus","zh":"通路与共识"},"gpw_path":{"en":"Pathways containing this gene, enriched (FDR&lt;0.05) in ≥2 contrasts","zh":"含该基因且在 ≥2 个对比中富集（FDR&lt;0.05）的通路"},"gpw_cons":{"en":"Consensus list","zh":"共识基因清单"},"gpw_cons_up":{"en":"consensus UP (one of 825 genes up-regulated across cohorts)","zh":"共识上调（跨队列上调 825 基因之一）"},"gpw_cons_down":{"en":"consensus DOWN (one of 196 genes down-regulated across cohorts)","zh":"共识下调（跨队列下调 196 基因之一）"},"gpw_cons_no":{"en":"Not in the consensus list.","zh":"不在共识基因清单中。"},"gpw_target":{"en":"Known drug target","zh":"已知药物靶点"},"gpw_ncol":{"en":"contrasts","zh":"对比数"},"path_th_term":{"en":"Pathway term","zh":"通路"},"path_th_db":{"en":"Database / collection","zh":"数据库/集合"},"g_f1_t":{"en":"Cross-cohort meta-analysis","zh":"跨队列 Meta 分析"},"g_f1_combined":{"en":"Combined logFC (random effects)","zh":"合并 logFC（随机效应）"},"g_f1_ci":{"en":"95% CI","zh":"95% 置信区间"},"g_f1_p":{"en":"Combined p","zh":"合并 p 值"},"g_f1_i2":{"en":"Heterogeneity I²","zh":"异质性 I²"},"g_f1_k":{"en":"cohorts","zh":"队列数"},"g_f1_method":{"en":"Random-effects meta-analysis (DerSimonian–Laird) over the primary case–control contrasts of 10 bulk cohorts; per-cohort SE from lfcSE or |logFC/t|. Shown only when ≥3 cohorts measured the gene.","zh":"10 个 bulk 队列主病例-对照对比的随机效应 Meta 分析（DerSimonian–Laird）；各队列标准误取自 lfcSE 或 |logFC/t|。基因在 ≥3 个队列中测得时才展示。"},"g_f1_forest":{"en":"Per-cohort forest plot (±1.96 SE) + meta-analysis diamond","zh":"各队列森林图（±1.96 SE）+ Meta 分析菱形"},"g_f4_t":{"en":"Top co-expressed genes","zh":"高共表达基因"},"g_f4_method":{"en":"Spearman correlation across samples within each bulk cohort, Fisher-z averaged across ≥3 cohorts; top-10 positive partners restricted to evidence-matrix genes.","zh":"各 bulk 队列内样本间 Spearman 相关，经 ≥3 队列 Fisher-z 合并；仅展示证据矩阵基因中的前 10 正相关伙伴。"},"g_f4_th_g":{"en":"Gene","zh":"基因"},"g_f4_th_r":{"en":"Mean r","zh":"平均 r"},"g_f4_th_k":{"en":"cohorts","zh":"队列数"},"g_f3_t":{"en":"Genetic support","zh":"遗传支持"},"g_f3_gwas":{"en":"GWAS Catalog (genome-wide significant, p≤5e-8)","zh":"GWAS Catalog（全基因组显著，p≤5e-8）"},"g_f3_trait":{"en":"Trait","zh":"性状"},"g_f3_bestp":{"en":"Strongest p","zh":"最强 p 值"},"g_f3_n":{"en":"associations","zh":"关联数"},"g_f3_eqtl":{"en":"GTEx v8 single-tissue eQTL presence","zh":"GTEx v8 单组织 eQTL 存在性"},"g_f3_proxy":{"en":"⚠ GTEx has no nasal tissue data; Whole Blood / Lung / Skin are proxy tissues.","zh":"⚠ GTEx 无鼻组织数据；全血 / 肺 / 皮肤为代理组织。"},"g_f3_method":{"en":"GWAS Catalog REST v2 queried for in-scope traits (CRSwNP, nasal polyps, chronic rhinosinusitis, asthma, allergic rhinitis, eosinophil counts); GTEx v8 checked for significant single-tissue eQTL presence.","zh":"用 GWAS Catalog REST v2 查询范围内性状（CRSwNP、鼻息肉、慢性鼻窦炎、哮喘、过敏性鼻炎、嗜酸粒细胞计数）；GTEx v8 检查显著单组织 eQTL 存在性。"},"g_f6_t":{"en":"Literature support","zh":"文献支持"},"g_f6_method":{"en":"Gene-level claims extracted verbatim from linked PubMed abstracts of the original papers and tested against our reanalysis; audited genes only (no extrapolation).","zh":"基因水平声称逐字摘自原文关联 PubMed 摘要并用我们的重分析检验；仅限已审计基因（不外推）。"},"g_f6_claims":{"en":"published claims tested","zh":"已发表声称已检验"},"g_f6_rep":{"en":"reproduced","zh":"复现"},"g_f6_dir":{"en":"direction-consistent only","zh":"仅方向一致"},"g_f6_not":{"en":"not reproduced","zh":"未复现"}}, CAV = {"cav_GSE198950":{"en":"Tissue confounding: cases are ethmoid tissue, controls are inferior turbinate — the significant reversal of IL33/POSTN may stem from this; must be stated when used.","zh":"组织混杂：病例为筛窦组织、对照为下鼻甲组织——IL33/POSTN 显著反向可能源于此，使用时必须注明。"},"cav_GSE189690":{"en":"No healthy controls: disease-subtype contrast only; excluded from case–control directional priors.","zh":"无健康对照：仅疾病亚型对比，不参与病例-对照方向先验。"},"cav_GSE330761":{"en":"No healthy controls; sorted mast-cell subset atlas (3v3).","zh":"无健康对照；分选肥大细胞亚群图谱型（3v3）。"},"cav_GSE69093":{"en":"Primary cultured cells: zero transcriptome-wide significant genes but p-values enriched at the small-p end — judged a genuine weak signal (not a technical error). Series platform was mislabeled at registration (Affymetrix); corrected to Illumina HumanHT-12 v4 annotation.","zh":"原代培养细胞：全转录组 0 显著但 p 值富集于小 p 端，判为真实弱信号（非技术错误）。系列注册平台误标（Affymetrix），已按 Illumina HumanHT-12 v4 注释修正。"}};
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
  // v1.3 added-value layers (F1/F4/F3/F6): render only when data exist for the gene
  html += f1Block(key) + f4Block(key) + f3Block(key) + f6Block(key);
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
  drawF1Forest(key);
}
// ---- v1.3: added-value layers (F1 cross-cohort meta, F4 co-expression, F3 genetic, F6 literature) ----
function fmtP(p){ if(p==null) return '<span style="color:#aaa">—</span>'; if(p<1e-4) return Number(p).toExponential(1); return Number(p).toFixed(4); }
function f1Block(key){
  const m = (typeof F1META!=='undefined') ? F1META[key] : null;
  if(!m) return '';
  let html = '<div class="card"><h3>'+gs('g_f1_t')+'</h3>';
  html += '<p><b>'+gs('g_f1_combined')+':</b> '+fmt(m.lfc,3)+' &nbsp; <b>'+gs('g_f1_ci')+':</b> ['+fmt(m.lo,3)+', '+fmt(m.hi,3)+'] &nbsp; <b>'+gs('g_f1_p')+':</b> '+fmtP(m.p)+' &nbsp; <b>'+gs('g_f1_i2')+':</b> '+fmt(m.i2,1)+'% &nbsp; <b>'+gs('g_f1_k')+':</b> '+m.k+'</p>';
  html += '<h4>'+gs('g_f1_forest')+'</h4><canvas id="cv_f1" width="900" height="360"></canvas>';
  html += '<p style="font-size:12px;color:#666">'+gs('g_f1_method')+'</p></div>';
  return html;
}
function drawF1Forest(key){
  const cv = document.getElementById('cv_f1'); if(!cv) return;
  const rows = (typeof F1COHORTS!=='undefined' && typeof F1COHORT_ORDER!=='undefined') ? F1COHORTS[key] : null;
  const m = (typeof F1META!=='undefined') ? F1META[key] : null;
  if(!rows || !m) return;
  const ctx = cv.getContext('2d');
  const present = F1COHORT_ORDER.map(function(c,i){ return {c:c, v:rows[i]}; }).filter(function(x){ return x.v; });
  const n = present.length; if(!n) return;
  cv.height = 60 + n*26 + 64;
  const W = cv.width, H = cv.height;
  const all = [];
  present.forEach(function(x){ all.push(x.v[0]-1.96*x.v[1], x.v[0]+1.96*x.v[1]); });
  all.push(m.lo, m.hi, 0);
  let mn = Math.min.apply(null, all), mx = Math.max.apply(null, all);
  const pad = (mx-mn)*0.1 || 0.5; mn -= pad; mx += pad;
  const X = function(v){ return 190 + (v-mn)/(mx-mn)*(W-210); };
  const rowY = function(i){ return 44 + i*26; };
  ctx.clearRect(0,0,W,H);
  ctx.font = '12px sans-serif';
  ctx.strokeStyle = '#999'; ctx.beginPath(); ctx.moveTo(X(0),24); ctx.lineTo(X(0),H-44); ctx.stroke();
  present.forEach(function(x,i){
    const y = rowY(i), lfc = x.v[0], se = x.v[1];
    ctx.fillStyle = '#333'; ctx.fillText(x.c, 8, y+4);
    ctx.strokeStyle = '#5a8fd4'; ctx.beginPath(); ctx.moveTo(X(lfc-1.96*se),y); ctx.lineTo(X(lfc+1.96*se),y); ctx.stroke();
    ctx.fillStyle = '#1f5fa8'; ctx.fillRect(X(lfc)-4, y-4, 8, 8);
    ctx.fillStyle = '#666'; ctx.fillText(lfc.toFixed(2), W-64, y+4);
  });
  const dy = 44 + n*26 + 22;
  ctx.fillStyle = '#333'; ctx.fillText('META (RE)', 8, dy+4);
  ctx.fillStyle = '#b33';
  ctx.beginPath();
  ctx.moveTo(X(m.lo),dy); ctx.lineTo(X(m.lfc),dy-9); ctx.lineTo(X(m.hi),dy); ctx.lineTo(X(m.lfc),dy+9);
  ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#666'; ctx.fillText(m.lfc.toFixed(2)+' ['+m.lo.toFixed(2)+', '+m.hi.toFixed(2)+']', W-64, dy+4);
}
function f4Block(key){
  const rows = (typeof F4COEXPR!=='undefined') ? F4COEXPR[key] : null;
  if(!rows || !rows.length) return '';
  let html = '<div class="card"><h3>'+gs('g_f4_t')+'</h3><table><tr><th>'+gs('g_f4_th_g')+'</th><th>'+gs('g_f4_th_r')+'</th><th>'+gs('g_f4_th_k')+'</th></tr>';
  rows.forEach(function(r){
    html += '<tr><td><a href="#" onclick="searchGene(\''+r[0]+'\');return false;">'+r[0]+'</a></td><td>'+r[1].toFixed(3)+'</td><td>'+r[2]+'</td></tr>';
  });
  html += '</table><p style="font-size:12px;color:#666">'+gs('g_f4_method')+'</p></div>';
  return html;
}
function f3Block(key){
  const rows = (typeof F3GENETIC!=='undefined') ? F3GENETIC[key] : null;
  if(!rows || !rows.length) return '';
  const gwas = rows.filter(function(r){ return r.source==='GwasCatalog'; });
  const eqtl = rows.filter(function(r){ return r.source==='GTEx'; });
  let html = '<div class="card"><h3>'+gs('g_f3_t')+'</h3>';
  if(gwas.length){
    html += '<p><b>'+gs('g_f3_gwas')+'</b></p><table><tr><th>'+gs('g_f3_trait')+'</th><th>'+gs('g_f3_bestp')+'</th></tr>';
    gwas.forEach(function(r){ html += '<tr><td>'+r.trait+'</td><td>'+fmtP(r.bestp)+'</td></tr>'; });
    html += '</table>';
  }
  if(eqtl.length){
    html += '<p><b>'+gs('g_f3_eqtl')+':</b> '+eqtl.map(function(r){ return r.trait; }).join(' \u00b7 ')+'</p>';
    html += '<div class="caveat">'+gs('g_f3_proxy')+'</div>';
  }
  html += '<p style="font-size:12px;color:#666">'+gs('g_f3_method')+'</p></div>';
  return html;
}
function f6Block(key){
  const r = (typeof F6LIT!=='undefined') ? F6LIT[key] : null;
  if(!r) return '';
  let html = '<div class="card"><h3>'+gs('g_f6_t')+'</h3>';
  html += '<p><b>'+r.t+'</b> '+gs('g_f6_claims')+': <span class="badge sig">'+r.r+' '+gs('g_f6_rep')+'</span> <span class="badge">'+r.d+' '+gs('g_f6_dir')+'</span>'
    + (r.n ? ' <span class="badge warn">'+r.n+' '+gs('g_f6_not')+'</span>' : '') + '</p>';
  html += '<p style="font-size:12px;color:#666">'+gs('g_f6_method')+'</p></div>';
  return html;
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
