
const BULK = DATA.coho, SCN = DATA.scl, GENES = DATA.genes;
function fmt(v, d){ if(v==null) return '<span style="color:#aaa">—</span>'; return Number(v).toFixed(d); }
function badge(f){ if(f==null) return ''; if(f<0.05) return '<span class="badge sig">FDR<0.05</span>'; return '<span class="badge nonsig">ns</span>'; }
function searchGene(g0){
  let q = (g0 || document.getElementById('q').value || '').trim().toUpperCase();
  const box = document.getElementById('result');
  if(!q){ box.innerHTML = '<p>请输入基因符号。</p>'; return; }
  let key = Object.keys(GENES).find(k => k.toUpperCase() === q);
  if(!key){ // prefix suggestions
    let cand = Object.keys(GENES).filter(k => k.toUpperCase().startsWith(q)).slice(0,20);
    box.innerHTML = '<p>未找到 <b>'+q+'</b>。' + (cand.length? '可能：'+cand.map(c=>`<a href="#" onclick="searchGene('${c}');return false;">${c}</a>`).join('、') : '无相似符号。') + '</p>';
    return;
  }
  document.getElementById('q').value = key;
  const r = GENES[key];
  let html = '<div class="card"><h3>'+key+'</h3>';
  // bulk table + chart
  html += '<h3>Bulk：16 队列（主对比）</h3><table><tr><th>队列</th><th>logFC</th><th>FDR</th><th></th></tr>';
  const vals = [];
  if(r.b){
    BULK.forEach((c,i)=>{
      const e = r.b[i]; vals.push(e?e[0]:null);
      html += '<tr><td>'+c.id+'<br><span style="font-size:12px;color:#666">'+c.n+'</span>'
        + (c.caveat? '<br><span class="badge warn">⚠ 限制见下</span>' : '') + '</td>'
        + '<td>'+fmt(e?e[0]:null,3)+'</td><td>'+fmt(e?e[1]:null,4)+'</td><td>'+badge(e?e[1]:null)+'</td></tr>';
    });
  } else html += '<tr><td colspan="4">该基因不在 bulk 证据矩阵中（未测得）。</td></tr>';
  html += '</table>';
  const caveats = BULK.filter(c=>c.caveat && r.b && BULK.indexOf(c)<r.b.length && r.b[BULK.indexOf(c)]);
  const shown = [...new Set(caveats.map(c=>'<div class="caveat"><b>⚠ '+c.id+' 限制：</b>'+c.caveat+'</div>'))];
  if(shown.length) html += shown.join('');
  html += '<h3>Bulk logFC 条形图</h3><canvas id="cv" width="900" height="340"></canvas></div>';
  // sc table
  html += '<div class="card"><h3>单细胞：细胞类型级对比</h3>';
  if(r.s){
    html += '<table><tr><th>对比（数据集 · 细胞类型 · 设计）</th><th>logFC</th><th>FDR</th><th></th></tr>';
    Object.keys(r.s).forEach(i=>{
      const e = r.s[i];
      html += '<tr><td>'+SCN[+i]+'</td><td>'+fmt(e[0],3)+'</td><td>'+fmt(e[1],4)+'</td><td>'+badge(e[1])+'</td></tr>';
    });
    html += '</table>';
  } else html += '<p>该基因不在单细胞证据矩阵中（未测得）。</p>';
  html += '</div>';
  // spatial
  html += '<div class="card"><h3>空间（GeoMx，GSE235714）</h3>';
  if(r.sp){
    html += '<table><tr><th>区室</th><th>logFC（供体级描述值）</th><th>FDR</th></tr>'
      + '<tr><td>CD45+ 免疫区室</td><td>'+fmt(r.sp[0],3)+'</td><td>'+fmt(r.sp[1],4)+'</td></tr>'
      + '<tr><td>PanCK+ 上皮区室</td><td>'+fmt(r.sp[2],3)+'</td><td>'+fmt(r.sp[3],4)+'</td></tr></table>'
      + '<div class="caveat"><b>⚠ 空间层限制：</b>两区室供体级 FDR&lt;0.05 均为 0（6v4 供体），此为描述性值，非独立证据；'
      + '且疾病与组织完全混杂（CRSwNP=息肉组织 vs 对照=筛窦组织）。</div>';
  } else html += '<p>该基因<b>不在 GeoMx CTA panel（1,480 基因）中</b>——无空间数据，非缺失值。</p>';
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
