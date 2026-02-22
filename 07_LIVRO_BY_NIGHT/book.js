const state = {
  data: null,
  filters: {
    sect: new Set(),
    clan: new Set(),
    kind: new Set(),
    coterie: new Set(),
    q: '',
  }
};

// Injected at build time (may be empty string).
const PDF_NAME = "Sao_Paulo_by_Night.pdf";
const CANON_COTERIE_IDS = new Set([
  "coterie_ferrugem_mooca",
  "coterie_leste_de_aco",
  "coterie_matilha_do_sul",
]);
const COTERIE_ALIAS_TO_ID = {
  ferrugem: "coterie_ferrugem_mooca",
  "coterie ferrugem mooca tatuape": "coterie_ferrugem_mooca",
  "coterie ferrugem mooca/tatuape": "coterie_ferrugem_mooca",
  "leste de aco": "coterie_leste_de_aco",
  "coterie leste de aco itaquera/extremo leste": "coterie_leste_de_aco",
  "matilha do sul": "coterie_matilha_do_sul",
  "coterie matilha do sul capao/grajau": "coterie_matilha_do_sul",
};
const SECTION_META = [
  ["sec-macro-map", "Mapa macro"],
  ["sec-overview", "Visao geral"],
  ["sec-gallery", "Banco de imagens"],
  ["sec-faccoes", "Faccoes"],
  ["sec-clas", "Clas"],
  ["sec-coteries", "Coteries canonicas"],
  ["sec-npcs", "NPCs e servos"],
  ["sec-antagonistas", "Antagonistas"],
  ["sec-files-jogadores", "Arquivos jogadores"],
  ["sec-files-narrador", "Arquivos narrador"],
];
const SECTION_IDS = new Set(SECTION_META.map(x => x[0]));

function el(id){ return document.getElementById(id); }

function uniq(arr){ return Array.from(new Set(arr)); }

function norm(s){
  return String(s||'').toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu,'');
}

function canonicalCoterieId(v){
  const raw = String(v || '').trim();
  if(!raw) return null;
  if(CANON_COTERIE_IDS.has(raw)) return raw;
  const k = norm(raw).replace(/[^a-z0-9]+/g, ' ').trim();
  return COTERIE_ALIAS_TO_ID[k] || null;
}

function canonicalCoterieName(cid){
  const c = (state.data?.coteries || []).find(x => x && x.id === cid);
  if(c && c.name) return c.name;
  if(cid === "coterie_ferrugem_mooca") return "Coterie Ferrugem (Mooca/Tatuape)";
  if(cid === "coterie_leste_de_aco") return "Leste de Aco (Itaquera/Extremo Leste)";
  if(cid === "coterie_matilha_do_sul") return "Matilha do Sul (Capao/Grajau)";
  return cid;
}

function canonicalSectName(v){
  const n = norm(v);
  if(!n) return '';
  if(n.includes('camar')) return 'Camarilla';
  if(n.includes('anarch')) return 'Anarch';
  if(n.includes('indep') || n.includes('autarqu') || n.includes('zona')) return 'Independentes';
  if(n.includes('segunda') || n.includes('inquis')) return 'Segunda Inquisição';
  if(n.includes('mortal')) return 'Mortal';
  return String(v || '').trim();
}

function canonicalClanName(v, kind){
  const raw = String(v || '').trim();
  if(!raw) return '';
  const n = norm(raw);
  if(n === 'thin blood' || n === 'thin-blood') return 'Thin-Blood';
  if(kind !== 'kindred' && n === 'mortal') return '';
  return raw;
}

function extractCanonCoteries(e){
  const raw = [
    ...(Array.isArray(e?.coteries_all) ? e.coteries_all : []),
    ...(Array.isArray(e?.coteries) ? e.coteries : []),
  ];
  const out = [];
  raw.forEach(v => {
    const cid = canonicalCoterieId(v);
    if(cid && !out.includes(cid)) out.push(cid);
  });
  return out;
}

function normalizeEntityCanon(e){
  if(!e || typeof e !== 'object') return e;
  const canonCs = extractCanonCoteries(e);
  const kind = e.kind || 'kindred';
  const sect = canonicalSectName(e.sect_norm || e.sect || '');
  const clan = canonicalClanName(e.clan, kind);
  const servesClans = Array.isArray(e.serves_clans)
    ? e.serves_clans.map(v => canonicalClanName(v, 'kindred')).filter(Boolean)
    : [];
  return {
    ...e,
    sect,
    sect_norm: sect,
    clan,
    serves_clans: servesClans,
    coteries_all: canonCs,
    coteries: canonCs,
  };
}

function sanitizeNpcTextCanon(text, entity){
  if(!text) return text;
  const lines = String(text).split(/\r?\n/);
  const out = [];
  let skippingOldCoterieBullets = false;
  const canonList = extractCanonCoteries(entity).map(canonicalCoterieName);
  for(const line of lines){
    const n = norm(line);
    if(n.includes('coterie') || n.includes('associaco')){
      if(canonList.length){
        out.push('Coteries canonicas: ' + canonList.join(', '));
      } else {
        out.push('Coteries canonicas: -');
      }
      skippingOldCoterieBullets = true;
      continue;
    }
    if(skippingOldCoterieBullets){
      if(!line.trim()){
        skippingOldCoterieBullets = false;
        out.push(line);
        continue;
      }
      if(/^\s*-\s+/.test(line)) continue;
      skippingOldCoterieBullets = false;
    }
    out.push(line);
  }
  return out.join('\n');
}

function getJsonPayload(id){
  const tag = document.getElementById(id);
  if(!tag || !tag.textContent || !tag.textContent.trim()) return null;
  try { return JSON.parse(tag.textContent); } catch(e) { return null; }
}

function portraitCandidates(stem){
  if(!stem) return [];
  const base = (state.data?.paths?.portraits_base || '../assets/portraits/');
  // In the "Option 1" repo layout, portraits may only exist under docs/assets.
  // This keeps the source book (07_LIVRO_BY_NIGHT/index.html) working even if 05_ASSETS is absent.
  const p = String(location.pathname||'').replace(/\\/g,'/');
  const altBase = p.includes('/docs/') ? '../assets/portraits/' : '../docs/assets/portraits/';
  const v = (window.__PORTRAIT_V || Date.now());
  const bases = (altBase && altBase !== base) ? [base, altBase] : [base];
  const out = [];
  bases.forEach(b => {
    out.push(b + stem + '.jpg?v=' + v);
    out.push(b + stem + '.jpeg?v=' + v);
    out.push(b + stem + '.png?v=' + v);
    out.push(b + stem + '.webp?v=' + v);
  });
  return out;
}
function setImgWithFallback(img, stem){
  const c = portraitCandidates(stem);
  if(!c.length){
    img.src='';
    img.style.display = 'none';
    return;
  }
  let i = 0;
  img.onload = () => {
    img.style.display = 'block';
  };
  img.onerror = () => {
    i++;
    if(i < c.length) {
      img.src = c[i];
    } else {
      img.style.display = 'none';
    }
  };
  img.src = c[0];
}

function buildChips(id, values, labelFn){
  const box = el(id);
  box.innerHTML = '';
  values.forEach(v => {
    const lab = document.createElement('label');
    lab.className = 'chip';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.value = v;
    cb.addEventListener('change', () => {
      const set = state.filters[id === 'chipsSect' ? 'sect' : id === 'chipsClan' ? 'clan' : id === 'chipsCoterie' ? 'coterie' : 'kind'];
      if(cb.checked) set.add(v); else set.delete(v);
      renderNpcCards();
    });
    const sp = document.createElement('span');
    sp.textContent = labelFn ? labelFn(v) : v;
    lab.appendChild(cb);
    lab.appendChild(sp);
    box.appendChild(lab);
  });
}

function matchesFilters(e){
  const f = state.filters;
  if(f.kind.size && !f.kind.has(e.kind || 'kindred')) return false;
  if(f.sect.size && !f.sect.has(e.sect_norm || e.sect || '')) return false;
  if(f.clan.size){
    if((e.kind||'kindred') === 'kindred'){
      if(!f.clan.has(e.clan || '')) return false;
    } else if((e.kind||'') === 'ghoul'){
      const sc = Array.isArray(e.serves_clans) ? e.serves_clans : [];
      if(!sc.some(x => f.clan.has(x))) return false;
    } else {
      // mortals without a clan are excluded when clan filter is active
      return false;
    }
  }
  if(f.coterie.size){
    const cs = extractCanonCoteries(e);
    if(!cs.some(x => f.coterie.has(x))) return false;
  }
  const q = norm(f.q);
  if(q){
    const hay = norm([e.display_name, e.role, e.domain, e.sect, e.clan, e.signature_style].filter(Boolean).join(' '));
    if(!hay.includes(q)) return false;
  }
  return true;
}

function openModalForEntity(e){
  const wrap = el('modalWrap');
  wrap.style.display = 'flex';
  el('modalTitle').textContent = (e.display_name || e.id || 'NPC');

  const img = el('modalImg');
  img.style.display = 'block';
  img.alt = e.display_name || '';
  setImgWithFallback(img, e.file_stem);

  const metaLines = [];
  metaLines.push((e.kind || 'kindred') + (e.clan ? ' · ' + e.clan : '') + (e.sect ? ' · ' + e.sect : ''));
  if(e.role) metaLines.push('Papel: ' + e.role);
  if(e.domain) metaLines.push('Domínio/Área: ' + e.domain);
  if(e.tier) metaLines.push('Tier: ' + e.tier);
  if(e.appearance_explicit) metaLines.push('Aparência: ' + e.appearance_explicit);
  const cs = extractCanonCoteries(e);
  if(cs.length){
    metaLines.push('Coteries: ' + cs.map(canonicalCoterieName).join(', '));
  }
  el('modalMeta').textContent = metaLines.join('\n');

  el('modalPrompt').textContent = (e.portrait_prompt || '(sem prompt)');

  const docs = (e.docs && e.docs.files) ? e.docs.files : {};
  el('modalResumo').textContent = sanitizeNpcTextCanon(docs.ficha_resumida || '(sem ficha resumida)', e);
  el('modalHistoria').textContent = sanitizeNpcTextCanon(docs.historia || '(sem história)', e);
  el('modalCompleta').textContent = docs.ficha_completa || '(sem ficha completa em arquivo)';

  const fs = e.full_sheet || null;
  el('modalFullSheet').textContent = fs ? JSON.stringify(fs, null, 2) : '(sem ficha completa estruturada)';

  const paths = (e.docs && e.docs.paths) ? e.docs.paths : {};
  const lines = [];
  Object.entries(paths).forEach(([k,v]) => lines.push(k + ': ' + v));
  el('modalPaths').textContent = lines.length ? lines.join('\n') : '(sem caminhos)';
}

function closeModal(){
  el('modalWrap').style.display = 'none';
}

function applyCoterieFilter(cid){
  // Mark the chip and update state.
  const box = el('chipsCoterie');
  if(!box) return;
  // Clear other coteries for clarity.
  state.filters.coterie.clear();
  box.querySelectorAll('input[type=checkbox]').forEach(cb => {
    cb.checked = (cb.value === cid);
    if(cb.checked) state.filters.coterie.add(cid);
  });
  setActiveSection('sec-npcs');
  // Scroll to NPC section as a convenience.
  try { document.getElementById('sec-npcs')?.scrollIntoView({behavior:'smooth', block:'start'}); } catch(e) {}
  renderNpcCards();
}

function cardText(e){
  const lines = [];
  if(e.kind === 'kindred'){
    if(e.sect) lines.push('Seita: ' + e.sect);
    if(e.clan) lines.push('Clã: ' + e.clan);
    if(e.role) lines.push('Papel: ' + e.role);
    if(e.domain) lines.push('Domínio: ' + e.domain);
    if(e.tier) lines.push('Tier: ' + e.tier);
    if(e.sire) lines.push('Sire: ' + e.sire);
    if(Array.isArray(e.childer) && e.childer.length) lines.push('Cria: ' + e.childer.join(', '));
  } else {
    if(e.sect) lines.push('Vínculo: ' + e.sect);
    if(e.role) lines.push('Papel: ' + e.role);
    if(e.domain) lines.push('Área: ' + e.domain);
  }
  return lines.join('\n');
}

function renderNpcCards(){
  const box = el('npcCards');
  const ents = (state.data?.entities || []).filter(matchesFilters);

  // stable sort: Kindred first, then by sect, then clan, then name
  ents.sort((a,b)=>{
    const ak = a.kind==='kindred' ? 0 : a.kind==='ghoul' ? 1 : 2;
    const bk = b.kind==='kindred' ? 0 : b.kind==='ghoul' ? 1 : 2;
    if(ak !== bk) return ak-bk;
    const as = String(a.sect_norm||a.sect||'');
    const bs = String(b.sect_norm||b.sect||'');
    if(as !== bs) return as.localeCompare(bs);
    const ac = String(a.clan||'');
    const bc = String(b.clan||'');
    if(ac !== bc) return ac.localeCompare(bc);
    return String(a.display_name||'').localeCompare(String(b.display_name||''));
  });

  box.innerHTML = '';
  const max = 240; // keep it snappy
  const list = ents.slice(0, max);
  list.forEach(e=>{
    const card = document.createElement('div');
    card.className = 'card';
    const head = document.createElement('div');
    head.className = 'cardHead';
    const p = document.createElement('div');
    p.className = 'portrait';
    const img = document.createElement('img');
    img.loading = 'lazy';
    img.alt = e.display_name || '';
    setImgWithFallback(img, e.file_stem);
    p.appendChild(img);
    const meta = document.createElement('div');
    const t = document.createElement('div');
    t.className = 'cardTitle';
    t.textContent = e.display_name || e.id;
    const m = document.createElement('div');
    m.className = 'cardMeta';
    m.textContent = (e.kind || 'kindred') + (e.clan ? ' · ' + e.clan : '') + (e.sect ? ' · ' + e.sect : '');
    meta.appendChild(t);
    meta.appendChild(m);
    head.appendChild(p);
    head.appendChild(meta);
    const body = document.createElement('div');
    body.className = 'cardBody mono';
    body.textContent = cardText(e);
    card.appendChild(head);
    card.appendChild(body);
    card.addEventListener('click', ()=> openModalForEntity(e));
    box.appendChild(card);
  });

  el('npcCount').textContent = `${ents.length} entidades (mostrando ${list.length}${ents.length>max ? ' / '+max : ''})`;
}

function mountMdSection(containerId, files, startsWith){
  const host = el(containerId);
  const keys = Object.keys(files).filter(k => k.startsWith(startsWith));
  keys.sort((a,b)=>a.localeCompare(b));
  host.innerHTML = '';
  keys.forEach(k=>{
    const sec = document.createElement('section');
    sec.className = 'sec md';
    sec.id = 'file-' + k.replace(/[^a-z0-9]+/gi,'-');
    const h2 = document.createElement('h2');
    h2.textContent = k;
    const div = document.createElement('div');
    div.innerHTML = files[k] || '';
    sec.appendChild(h2);
    sec.appendChild(div);
    host.appendChild(sec);
  });
}

function setActiveSection(targetId){
  if(!SECTION_IDS.has(targetId)) return;
  SECTION_META.forEach(([id]) => {
    const sec = el(id);
    if(!sec) return;
    sec.classList.toggle('is-active', id === targetId);
  });
  document.querySelectorAll('.toc button[data-target]').forEach(btn => {
    btn.classList.toggle('is-active', btn.dataset.target === targetId);
  });
}

function buildToc(){
  const toc = el('toc');
  toc.innerHTML = '';
  SECTION_META.forEach(([id, label]) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.dataset.target = id;
    b.textContent = label;
    b.addEventListener('click', () => {
      setActiveSection(id);
      try { document.getElementById(id)?.scrollIntoView({behavior:'smooth', block:'start'}); } catch(e) {}
    });
    toc.appendChild(b);
  });
}

async function main(){
  function renderGallery(data){
    const host = el('galleryWrap');
    if(!host) return;
    const ch = getJsonPayload('galleryChapterJson') || {};
    const rp = getJsonPayload('galleryPortraitJson') || {};
    const chapterBase = (ch.base || 'chapter_images/').replace(/^\//,'');
    const chapterMap = ch.chapters || {};
    const portraitStems = Array.isArray(rp.stems) ? rp.stems : [];
    const byStem = new Map((data.entities || []).filter(Boolean).map(e => [String(e.file_stem || ''), e]));

    const out = [];
    Object.keys(chapterMap).sort((a,b)=>Number(a)-Number(b)).forEach(cid => {
      const imgs = Array.isArray(chapterMap[cid]) ? chapterMap[cid] : [];
      imgs.forEach(fn => {
        out.push({
          kind: 'chapter',
          label: 'Capitulo ' + cid,
          src: chapterBase + fn,
        });
      });
    });

    portraitStems.forEach(stem => {
      const e = byStem.get(stem) || null;
      out.push({
        kind: 'portrait',
        label: e ? (e.display_name || stem) : stem,
        stem: stem,
      });
    });

    host.innerHTML = '';
    out.forEach(it => {
      const card = document.createElement('div');
      card.className = 'gItem';
      const img = document.createElement('img');
      img.loading = 'lazy';
      img.alt = it.label || '';
      if(it.kind === 'chapter'){
        img.src = it.src;
      } else {
        setImgWithFallback(img, it.stem);
      }
      img.addEventListener('click', () => window.open(img.src, '_blank'));
      const cap = document.createElement('div');
      cap.className = 'gCap';
      cap.textContent = it.label || '';
      card.appendChild(img);
      card.appendChild(cap);
      host.appendChild(card);
    });

    const btn = el('btnGallery');
    if(btn){
      btn.addEventListener('click', () => {
        setActiveSection('sec-gallery');
        try { document.getElementById('sec-gallery')?.scrollIntoView({behavior:'smooth', block:'start'}); } catch(e) {}
      });
    }
  }

  // Prefer inline data when opened via file:// (fetch is often blocked by CORS).
  let data = null;
  if (window.BOOK_DATA) {
    data = window.BOOK_DATA;
  } else {
    const elJson = document.getElementById('bookDataJson');
    if (elJson && elJson.textContent && elJson.textContent.trim()) {
      try {
        data = JSON.parse(elJson.textContent);
      } catch (err) {
        console.error('bookDataJson invalido, usando fallback book_data.json', err);
      }
    }
    if (!data) {
      const res = await fetch('book_data.json', { cache: 'no-store' });
      data = await res.json();
    }
  }
  data.entities = (data.entities || []).map(normalizeEntityCanon);
  data.coteries = (data.coteries || []).filter(c => CANON_COTERIE_IDS.has(String(c.id || '')));
  if(data.coteries_by_id){
    const next = {};
    Object.entries(data.coteries_by_id).forEach(([k,v]) => {
      if(CANON_COTERIE_IDS.has(k)) next[k] = v;
    });
    data.coteries_by_id = next;
  }

  state.data = data;
  window.__PORTRAIT_V = Date.now();

  buildToc();
  renderGallery(data);
  el('kCounts').textContent = `Kindred: ${data.counts.kindred} · Ghouls: ${data.counts.ghouls} · Mortais: ${data.counts.mortals}`;

  // Render macro map
  if (window.MACRO_MAP_SVG) {
    el('macroMap').innerHTML = window.MACRO_MAP_SVG;
  } else {
    const elSvg = document.getElementById('macroMapSvg');
    const tpl = (elSvg && elSvg.content) ? elSvg.content : null;
    const markup = tpl ? (tpl.firstElementChild ? tpl.firstElementChild.outerHTML : '') : (elSvg ? elSvg.innerHTML : '');
    if (markup && markup.trim()) {
      el('macroMap').innerHTML = markup;
    } else {
      const svg = await fetch('mapa_macro_faccoes.svg', { cache:'no-store' }).then(r=>r.text());
      el('macroMap').innerHTML = svg;
    }
  }

  // Mount MD sections (converted server-side).
  mountMdSection('filesJogadores', data.files_html || {}, 'jogadores/');
  mountMdSection('filesNarrador', data.files_html || {}, 'narrador/');
  mountMdSection('filesFaccoes', data.files_html || {}, 'narrador/faccoes/');
  mountMdSection('filesAntagonistas', data.files_html || {}, 'antagonistas/');
  mountMdSection('filesClas', data.files_html || {}, 'clas/');
  setActiveSection('sec-macro-map');
  document.querySelectorAll('a[href^="#sec-"]').forEach(a => {
    a.addEventListener('click', (ev) => {
      const raw = String(a.getAttribute('href') || '');
      const id = raw.replace(/^#/, '');
      if(!SECTION_IDS.has(id)) return;
      ev.preventDefault();
      setActiveSection(id);
      try { document.getElementById(id)?.scrollIntoView({behavior:'smooth', block:'start'}); } catch(e) {}
    });
  });

  // Coteries cards
  const cwrap = el('coteriesCards');
  const cots = Array.isArray(data.coteries) ? data.coteries : [];
  const byId = data.coteries_by_id || {};
  const byEntId = new Map((data.entities||[]).filter(Boolean).map(e => [e.id, e]));
  function entName(eid){
    const ent = byEntId.get(eid);
    return ent ? (ent.display_name || eid) : eid;
  }
  function entById(eid){ return byEntId.get(eid) || null; }
  if(cwrap){
    cwrap.innerHTML = '';
    cots.slice().sort((a,b)=>String(a.name||'').localeCompare(String(b.name||''))).forEach(c=>{
      const cid = c.id;
      const exp = (byId[cid] && Array.isArray(byId[cid].members_expanded)) ? byId[cid].members_expanded : (c.members||[]);
      const card = document.createElement('div');
      card.className = 'card';
      const head = document.createElement('div');
      head.className = 'cardHead';
      const meta = document.createElement('div');
      const t = document.createElement('div');
      t.className = 'cardTitle';
      t.textContent = c.name || cid;
      const m = document.createElement('div');
      m.className = 'cardMeta';
      m.textContent = (c.faction || '-') + (c.base ? (' · Base: ' + c.base) : '') + ' · Membros: ' + exp.length;
      meta.appendChild(t);
      meta.appendChild(m);
      head.appendChild(meta);

      const body = document.createElement('div');
      body.className = 'cardBody';
      const lines = [];
      if(c.notes) lines.push(c.notes);
      lines.push('');
      lines.push('Membros (inclui servos relevantes):');
      const shown = exp.slice(0, 28);
      shown.forEach(eid => lines.push('- ' + entName(eid)));
      if(exp.length > shown.length) lines.push('- ...');
      body.textContent = lines.join('\n');

      card.appendChild(head);
      card.appendChild(body);

      // Click card: apply coterie filter
      card.addEventListener('click', ()=> applyCoterieFilter(cid));

      // Click member names: open modal (requires hit-test)
      card.addEventListener('dblclick', (ev)=>{
        // As a simple UX: double-click opens first member (or no-op). This keeps single click as filter.
        if(!shown.length) return;
        const ent = entById(shown[0]);
        if(ent) openModalForEntity(ent);
      });

      // Add lightweight member chips row (clickable) for the first few.
      const chips = document.createElement('div');
      chips.className = 'chips';
      chips.style.margin = '10px';
      exp.slice(0,10).forEach(eid=>{
        const ent = entById(eid);
        const a = document.createElement('a');
        a.href = '#';
        a.textContent = entName(eid);
        a.className = 'chip';
        a.addEventListener('click', (ev)=>{ ev.preventDefault(); ev.stopPropagation(); if(ent) openModalForEntity(ent); });
        chips.appendChild(a);
      });
      if(exp.length > 10){
        const more = document.createElement('span');
        more.className = 'chip';
        more.textContent = '+' + (exp.length - 10) + ' outros';
        chips.appendChild(more);
      }
      card.appendChild(chips);

      cwrap.appendChild(card);
    });
  }

  // Filters
  const sects = uniq((data.entities||[]).map(e=>e.sect_norm||macroKey(e.sect||'')).filter(Boolean)).sort((a,b)=>a.localeCompare(b));
  const clans = uniq((data.entities||[]).filter(e=>e.kind==='kindred').map(e=>e.clan).filter(Boolean)).sort((a,b)=>a.localeCompare(b));
  const kinds = ['kindred','ghoul','mortal'];
  buildChips('chipsSect', sects);
  buildChips('chipsClan', clans);
  buildChips('chipsKind', kinds, v => v==='kindred' ? 'kindred (vampiro)' : v);
  const coteries = (data.coteries || []).map(c => ({id:c.id, name:c.name})).filter(c => c.id && c.name).sort((a,b)=>a.name.localeCompare(b.name));
  buildChips('chipsCoterie', coteries.map(x=>x.id), (id) => {
    const m = coteries.find(x=>x.id===id);
    return m ? m.name : id;
  });

  el('q').addEventListener('input', (ev)=>{ state.filters.q = ev.target.value || ''; renderNpcCards(); });
  el('btnClear').addEventListener('click', ()=>{
    state.filters.q='';
    el('q').value='';
    ['chipsSect','chipsClan','chipsKind','chipsCoterie'].forEach(id=>{
      el(id).querySelectorAll('input[type=checkbox]').forEach(cb=>cb.checked=false);
    });
    state.filters.sect.clear(); state.filters.clan.clear(); state.filters.kind.clear(); state.filters.coterie.clear();
    renderNpcCards();
  });

  // Links
  if(el('lnkMap')) el('lnkMap').href = data.paths.map_html;
  if(el('lnkTeia')) el('lnkTeia').href = data.paths.teia_html;
  if(el('lnkMapTop')) el('lnkMapTop').href = data.paths.map_html;
  if(el('lnkTeiaTop')) el('lnkTeiaTop').href = data.paths.teia_html;

  // Macro map tooltip (explicit; file:// often ignores <title> tooltips in embedded SVG).
  const tip = el('mapTip');
  const macroHost = el('macroMap');
  function showTip(x,y,html){
    tip.style.display = 'block';
    tip.innerHTML = html;
    const r = macroHost.getBoundingClientRect();
    const maxX = r.width - 20;
    const maxY = r.height - 20;
    const left = Math.min(maxX, Math.max(10, x));
    const top = Math.min(maxY, Math.max(10, y));
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }
  function hideTip(){ tip.style.display = 'none'; }
  const svgEl = macroHost.querySelector('svg');
  if(svgEl){
    svgEl.querySelectorAll('path[data-district]').forEach(p=>{
      p.addEventListener('mousemove', (ev)=>{
        const name = p.getAttribute('data-district') || '';
        const dom = p.getAttribute('data-dominant') || '';
        const html = `<div class="t">${name}</div><div>Dominante: ${dom || '-'}</div>`;
        const r = macroHost.getBoundingClientRect();
        showTip(ev.clientX - r.left + 12, ev.clientY - r.top + 12, html);
      });
      p.addEventListener('mouseleave', hideTip);
    });
    svgEl.addEventListener('mouseleave', hideTip);
  }

  el('modalClose').addEventListener('click', closeModal);
  el('modalWrap').addEventListener('click', (ev)=>{ if(ev.target && ev.target.id==='modalWrap') closeModal(); });
  document.addEventListener('keydown', (ev)=>{ if(ev.key==='Escape') closeModal(); });

  // Optional PDF link. On Pages/docs it lives one level above /book/. When opening the
  // generator output directly (07_LIVRO_BY_NIGHT/index.html), we also support ../docs/.
  const pdfName = PDF_NAME;
  const pdfEls = [el('lnkPdf'), el('lnkPdfTop')].filter(Boolean);
  if(pdfEls.length && pdfName && pdfName !== '')
  {
    const p = String(location.pathname||'').replace(/\\/g,'/');
    const isBook = p.includes('/book/');
    const href = (isBook ? ('../' + pdfName) : ('../docs/' + pdfName));
    pdfEls.forEach(pdfEl => {
      pdfEl.href = href;
      pdfEl.style.display = 'inline-block';
    });
  }

  renderNpcCards();
}

function macroKey(s){
  s = String(s||'').toLowerCase();
  if(s.includes('camar')) return 'Camarilla';
  if(s.includes('anarch')) return 'Anarch';
  if(s.includes('indep') || s.includes('autarqu') || s.includes('zona')) return 'Independentes';
  if(s.includes('segunda') || s.includes('inquis')) return 'Segunda Inquisição';
  if(s.includes('mortal')) return 'Mortal';
  return (s||'').trim();
}

main().catch(err => {
  console.error(err);
  const e = document.createElement('pre');
  e.textContent = String(err && err.stack ? err.stack : err);
  document.body.appendChild(e);
});
