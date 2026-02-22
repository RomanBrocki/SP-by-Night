    f = (f || '').toLowerCase();
    if (f.includes('camar')) return 'Camarilla';
    if (f.includes('anarch')) return 'Anarch';
    if (f.includes('indep')) return 'Independentes';
    if (f.includes('autarqu') || f.includes('zona')) return 'Independentes';
    return f;
  }

  const CLAIMS = (DATA.district_claims || {});
  const dominant = (CLAIMS.dominant || {});
  const disputes = (CLAIMS.disputes || {});
  const pressures = (CLAIMS.pressures || {});

  function districtDominant(name) { return dominant[dk(name)] || 'Camarilla'; }
  function districtDispute(name) { return disputes[dk(name)] || null; }
  function districtPressures(name) {
    const v = pressures[dk(name)];
    return Array.isArray(v) ? v : [];
  }

  // SVG renderer keeps pane z-index + hit-testing predictable for many overlapping polygons.
  const map = L.map('map', {
    zoomControl: false,
    preferCanvas: false,
    wheelDebounceTime: 20,
    wheelPxPerZoomLevel: 90,
  });
  map.setView([-23.5505, -46.6333], 11);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  map.createPane('paneDistrictOutlines'); map.getPane('paneDistrictOutlines').style.zIndex = 250;
  map.createPane('paneMacro'); map.getPane('paneMacro').style.zIndex = 320;
  map.createPane('paneContested'); map.getPane('paneContested').style.zIndex = 360;
  map.createPane('paneDomains'); map.getPane('paneDomains').style.zIndex = 380;
  map.createPane('panePins'); map.getPane('panePins').style.zIndex = 420;

  // One SVG renderer per pane to avoid "everything shares one canvas" ambiguity.
  const RENDERERS = {
    paneDistrictOutlines: L.svg({ pane: 'paneDistrictOutlines' }),
    paneMacro: L.svg({ pane: 'paneMacro' }),
    paneContested: L.svg({ pane: 'paneContested' }),
    paneDomains: L.svg({ pane: 'paneDomains' }),
    panePins: L.svg({ pane: 'panePins' }),
  };
  function rendererForPane(paneId) {
    return RENDERERS[paneId] || RENDERERS.paneMacro;
  }

  function layerFromDistricts(districts, paneId, styleFn, onClick) {
    const wanted = new Set((districts || []).map(dk));
    return L.geoJSON(DISTRICTS_GEOJSON, {
      pane: paneId || 'paneMacro',
      renderer: rendererForPane(paneId || 'paneMacro'),
      interactive: true,
      bubblingMouseEvents: false,
      filter: (feature) => {
        const name = feature && feature.properties ? feature.properties.ds_nome : '';
        return wanted.has(dk(name));
      },
      style: (feature) => {
        const name = feature && feature.properties ? feature.properties.ds_nome : '';
        return styleFn ? styleFn(name, feature) : {};
      },
      onEachFeature: (feature, layer) => {
        if (!onClick) return;
        layer.on('click', (ev) => {
          // Prevent district outlines (and other layers) from stealing the click.
          try {
            if (ev && ev.originalEvent) {
              ev.originalEvent._spbn_overlay_click = true;
              L.DomEvent.stop(ev.originalEvent);
            }
          } catch (e) {}
          onClick(feature, layer, ev);
        });
      },
    });
  }

  // Base district outlines (always visible, neutral)
  let lastDistrict = null;
  const districtOutlines = L.geoJSON(DISTRICTS_GEOJSON, {
    pane: 'paneDistrictOutlines',
    renderer: rendererForPane('paneDistrictOutlines'),
    style: () => ({
      color: COLORS.NeutralLine,
      weight: 1,
      fillOpacity: 0.0,
    }),
    onEachFeature: (feature, layer) => {
      const name = feature && feature.properties ? feature.properties.ds_nome : '';
      layer.bindTooltip(name, { sticky: true, opacity: 0.94 });
      layer.on('click', (ev) => {
        // If an overlay handled this click, do not overwrite the side panel with "Distrito".
        try {
          if (ev && ev.originalEvent && ev.originalEvent._spbn_overlay_click) return;
        } catch(e) {}
        if (lastDistrict) {
          try { districtOutlines.resetStyle(lastDistrict); } catch(e) {}
        }
        lastDistrict = layer;
        layer.setStyle({ color: '#ffffff', weight: 3 });
        const dom = districtDominant(name);
        const ds = districtDispute(name);
        const pr = districtPressures(name);
        const lines = [];
        lines.push('Distrito: ' + name);
        lines.push('Controle local (claims): ' + dom);
        if (ds) {
          lines.push('');
          lines.push('Disputa: ' + (ds.between || []).join(' vs '));
          if (ds.note) lines.push(ds.note);
        }
        if (pr && pr.length) {
          lines.push('');
          lines.push('Alertas:');
          pr.forEach(x => lines.push('- ' + x));
        }
        setTitle('Distrito: ' + name);
        setPortrait('', '');
        setDetails(lines);
      });
    },
  }).addTo(map);

  // POIs (pins)
  const poiGroup = L.layerGroup();
  function poiIcon(kind) {
    const k = (kind || 'poi').toLowerCase();
    const bg = '#111111';
    const ring = k === 'elysium' ? COLORS.Camarilla : (k === 'hecata' ? COLORS.Independentes : '#00c2ff');
    return L.divIcon({
      className: '',
      html: `<div style="width:14px;height:14px;border-radius:14px;background:${bg};border:3px solid ${ring};box-shadow:0 4px 14px rgba(0,0,0,0.45)"></div>`,
      iconSize:[14,14],
      iconAnchor:[7,7],
    });
  }
  (DATA.pois || []).forEach(p => {
    if (!Number.isFinite(p.lat) || !Number.isFinite(p.lon)) return;
    const m = L.marker([p.lat, p.lon], { pane: 'panePins', icon: poiIcon(p.kind) });
    m.on('click', () => {
      const lines = [];
      lines.push('Ponto: ' + p.name);
      lines.push('Tipo: ' + (p.kind || 'poi'));
      if (p.domain_id) lines.push('Relacionado a dominio: ' + p.domain_id);
      if (p.notes) {
        lines.push('');
        lines.push('Descricao:');
        lines.push(String(p.notes));
      }
      setTitle('Ponto: ' + p.name);
      setPortrait('', '');
      setDetails(lines);
      try { map.setView(m.getLatLng(), Math.max(map.getZoom(), 14), { animate:true }); } catch(e) {}
    });
    poiGroup.addLayer(m);
  });

  // Domains (district-polygons)
  const DOMAIN_DISTRICTS = (DATA.domain_districts || {});
  const domainMeta = new Map((DATA.domains || []).map(d => [d.id, d]));
  const domainOwners = (DATA.domain_owners || {});
  const domainLayers = new Map();
  Object.keys(DOMAIN_DISTRICTS || {}).forEach(did => {
    const ds = DOMAIN_DISTRICTS[did] || [];
    if (!Array.isArray(ds) || !ds.length) return;
    const d = domainMeta.get(did) || {};
    const col = (d.faction && macroKeyFromFactionName(d.faction) === 'Camarilla') ? COLORS.Camarilla : '#00c2ff';
    const layer = layerFromDistricts(ds, 'paneDomains', () => ({
      color: '#ffffff',
      weight: 2,
      dashArray: '4 8',
      fillColor: col,
      fillOpacity: 0.0,
    }));
    domainLayers.set(did, layer);
  });

  // Subdivisoes Camarilla (territorios expressivos) visiveis quando o checkbox Camarilla (macro) esta marcado.
  // Clique em um territorio aqui = selecionar automaticamente o dominio no dropdown (modo "lordes").
  const camarillaLordLayers = new Map();
  (DATA.domains || []).forEach(d => {
    if (macroKeyFromFactionName(d.faction) !== 'Camarilla') return;
    const owner = domainOwners[d.id];
    if (!owner || !(owner.label || owner.owner_entity_id)) return;
    const ds = DOMAIN_DISTRICTS[d.id] || [];
    if (!Array.isArray(ds) || !ds.length) return;
    const lay = layerFromDistricts(ds, 'paneDomains', () => ({
      color: '#111111',
      weight: 2,
      dashArray: '1 7',
      fillColor: COLORS.Camarilla,
      fillOpacity: 0.18,
    }), () => {
      const sel = el('selCamarillaDomain');
      sel.value = d.id;
      sel.dispatchEvent(new Event('change'));
    });
    camarillaLordLayers.set(d.id, lay);
  });

  let domainPin = null;
  function clearDomain() {
    domainLayers.forEach(l => { try { map.removeLayer(l); } catch(e) {} });
    if (domainPin) { try { map.removeLayer(domainPin); } catch(e) {} domainPin = null; }
  }

  function showDomain(did, emphasizeColor) {
    clearDomain();
    if (!did) return;
    const layer = domainLayers.get(did);
    if (layer) {
      layer.setStyle({
        pane: 'paneDomains',
        color: '#111111',
        weight: 4,
        dashArray: '0',
        fillColor: emphasizeColor || COLORS.Camarilla,
        fillOpacity: 0.34,
      });
      layer.addTo(map);
      try { map.fitBounds(layer.getBounds().pad(0.20), { animate:true, maxZoom: 14 }); } catch(e) {}
    }
    const d = domainMeta.get(did) || null;
    if (d && d.center && Number.isFinite(d.center.lat) && Number.isFinite(d.center.lon)) {
      domainPin = L.circleMarker([d.center.lat, d.center.lon], {
        pane: 'panePins',
        radius: 7,
        color: '#111111',
        weight: 3,
        fillColor: emphasizeColor || COLORS.Camarilla,
        fillOpacity: 0.9,
      }).addTo(map);
    }
  }

  // Macro territories
  const MT = (DATA.macro_territories || {});
  const camMacro = (MT.macro || [])[0] || null;
  const anarchBaronatos = (MT.anarch_baronatos || []);
  const independentes = (MT.independentes || []);
  const contested = (MT.contested || []);
  const alerts = (MT.alerts || []);

  const kindredList = (DATA.kindred || []);
  let allMembers = kindredList.map(k => ({ ...k, kind: 'kindred' }));

  function memberTypeLabel(k) {
    const kind = String((k && k.kind) || '').toLowerCase();
    if (kind === 'ghoul') return 'Ghoul';
    if (kind === 'mortal') return 'Mortal';
    const clan = String(k && k.clan ? k.clan : '').toLowerCase();
    if (clan.includes('ghoul')) return 'Ghoul';
    if (clan.includes('mortal')) return 'Mortal';
    return 'Vampiro';
  }

  function factionColorForMember(k) {
    const sect = macroKeyFromFactionName(k && k.sect ? k.sect : '');
    if (sect === 'Anarch') return COLORS.Anarch;
    if (sect === 'Independentes') return COLORS.Independentes;
    return COLORS.Camarilla;
  }

  function approximateCoordsForMember(k) {
    const did = ((k && k.map_domains) || [])[0] || '';
    if (did) {
      const d = domainMeta.get(did);
      if (d && d.center && Number.isFinite(d.center.lat) && Number.isFinite(d.center.lon)) {
        return { lat: d.center.lat, lon: d.center.lon };
      }
    }
    const resid = String((k && k.residence_id) || '');
    const byResid = {
      baronato_mooca: { lat: -23.5587, lon: -46.5966 },
      baronato_sul: { lat: -23.6496, lon: -46.7724 },
      baronato_leste: { lat: -23.5405, lon: -46.4701 },
      indep_centro_velho: { lat: -23.5475, lon: -46.6361 },
      indep_cemiterios: { lat: -23.5563, lon: -46.6618 },
      indep_corredores: { lat: -23.5308, lon: -46.7112 }
    };
    if (byResid[resid]) return byResid[resid];

    const sect = macroKeyFromFactionName(k && k.sect ? k.sect : '');
    if (sect === 'Anarch') return { lat: -23.5606808, lon: -46.5971924 };
    if (sect === 'Independentes') return { lat: -23.5503898, lon: -46.633081 };
    return { lat: -23.5560945, lon: -46.6622655 };
  }

  function setMacroInfo(meta, titlePrefix) {
    const lines = [];
    lines.push((titlePrefix || 'Territorio') + ': ' + (meta.label || meta.id || ''));
    lines.push('Faccao/camada: ' + (meta.faction || '-'));
    if (meta.leader_label) lines.push('Responsavel: ' + meta.leader_label);
    if (Array.isArray(meta.districts) && meta.districts.length) lines.push('Distritos: ' + meta.districts.join(', '));
    if (Array.isArray(meta.between) && meta.between.length) lines.push('Disputa: ' + meta.between.join(' vs '));

    // Macro totals (coherent with "o que existe no projeto", nao com a cidade inteira real).
    const sectKey = macroKeyFromFactionName(meta.faction || '');
    if ((meta.id || '') === 'camarilla_macro') {
      const camTotal = kindredList.filter(k => macroKeyFromFactionName(k.sect) === 'Camarilla').length;
      const prince = kindredList.find(k => (k.role || '').toLowerCase().includes('principe'));
      const sheriff = kindredList.find(k => (k.role || '').toLowerCase().includes('xerife'));
      const seneschal = kindredList.find(k => (k.role || '').toLowerCase().includes('senescal'));
      const harpies = kindredList.filter(k => (k.role || '').toLowerCase().includes('harpia'));
      lines.push('Camarilla reconhecida no projeto (total): ' + camTotal);
      if (prince) lines.push('Principe: ' + prince.name);
      if (seneschal) lines.push('Senescal: ' + seneschal.name);
      if (sheriff) lines.push('Xerife: ' + sheriff.name);
      if (harpies.length) lines.push('Harpias: ' + harpies.map(h => h.name).join(', '));
    } else if (sectKey === 'Anarch') {
      const aTotal = kindredList.filter(k => macroKeyFromFactionName(k.sect) === 'Anarch').length;
      lines.push('Anarch no projeto (total): ' + aTotal);
    } else if (sectKey === 'Independentes') {
      const iTotal = kindredList.filter(k => macroKeyFromFactionName(k.sect) === 'Independentes').length;
      lines.push('Independentes no projeto (total): ' + iTotal);
    }

    const wanted = new Set((meta.districts || []).map(dk));
    const operatives = kindredList.filter(k => {
      const dids = (k.map_domains || []);
      for (const did of dids) {
        const dd = DOMAIN_DISTRICTS[did] || [];
        for (const d of dd) if (wanted.has(dk(d))) return true;
      }
      return false;
    });

    const residents = kindredList.filter(k => (k.residence_id || '') === (meta.id || ''));

    lines.push('Cainitas residentes conhecidos (cronica): ' + residents.length);
    lines.push('Cainitas que operam aqui (por dominio/presenca no mapa): ' + operatives.length);

    if (residents.length) {
      lines.push('');
      lines.push('Residentes:');
      residents
        .slice()
        .sort((a,b)=>String(a.name||'').localeCompare(String(b.name||'')))
        .slice(0, 24)
        .forEach(k => lines.push('- ' + k.name + ' (' + k.clan + '; ' + (k.role || '-') + ')'));
      if (residents.length > 24) lines.push('- ...');
    }
    if (operatives.length) {
      lines.push('');
      lines.push('Operam aqui:');
      operatives
        .slice()
        .sort((a,b)=>String(a.name||'').localeCompare(String(b.name||'')))
        .slice(0, 24)
        .forEach(k => lines.push('- ' + k.name + ' (' + k.clan + '; ' + (k.role || '-') + ')'));
      if (operatives.length > 24) lines.push('- ...');
    }

    if (meta.notes) {
      lines.push('');
      lines.push('Descricao:');
      lines.push(String(meta.notes));
    }
    setPortrait('', '');
    setDetails(lines);
  }

  const layerCamarilla = camMacro ? layerFromDistricts(camMacro.districts, 'paneMacro', () => ({
    pane: 'paneMacro',
    color: '#111111',
    weight: 2,
    fillColor: COLORS.Camarilla,
    fillOpacity: 0.12,
  }), () => {
    setTitle('Camarilla (macro)');
    setMacroInfo(camMacro, 'Macro');
  }) : null;

  const anarchLayers = new Map();
  anarchBaronatos.forEach(b => {
    const lay = layerFromDistricts(b.districts, 'paneMacro', () => ({
      pane: 'paneMacro',
      color: '#111111',
      weight: 3,
      fillColor: COLORS.Anarch,
      fillOpacity: 0.34,
    }), () => {
      setTitle(b.label || 'Baronato');
      setMacroInfo(b, 'Baronato');
    });
    anarchLayers.set(b.id, lay);
  });

  const indepLayers = new Map();
  independentes.forEach(b => {
    const lay = layerFromDistricts(b.districts, 'paneMacro', () => ({
      pane: 'paneMacro',
      color: '#111111',
      weight: 3,
      fillColor: COLORS.Independentes,
      fillOpacity: 0.34,
    }), () => {
      setTitle(b.label || 'Independentes');
      setMacroInfo(b, 'Bloco');
    });
    indepLayers.set(b.id, lay);
  });

  let lupDistricts = [];
  alerts.forEach(a => { if ((a.id || '') === 'risco_lupino') lupDistricts = a.districts || []; });
  const layerLupino = layerFromDistricts(lupDistricts, 'paneMacro', () => ({
    pane: 'paneMacro',
    color: '#111111',
    weight: 3,
    dashArray: '2 8',
    fillColor: COLORS.Lupino,
    fillOpacity: 0.20,
  }), () => {
    const a = alerts.find(x => (x.id || '') === 'risco_lupino') || { label:'Risco lupino', faction:'Risco lupino', districts:lupDistricts };
    setTitle('Risco lupino (alerta)');
    setMacroInfo(a, 'Alerta');
  });

  const contestedLayers = [];
  contested.forEach(c => {
    const lay = layerFromDistricts(c.districts, 'paneContested', () => ({
      pane: 'paneContested',
      color: '#111111',
      weight: 4,
      dashArray: '8 6',
      fillColor: COLORS.Contestado,
      fillOpacity: 0.30,
    }), () => {
      setTitle(c.label || 'Territorio contestado');
      setMacroInfo(c, 'Contestado');
    });
    contestedLayers.push({ meta: c, layer: lay });
  });

  function clearMacroLayers() {
    if (layerCamarilla) map.removeLayer(layerCamarilla);
    camarillaLordLayers.forEach(l => map.removeLayer(l));
    anarchLayers.forEach(l => map.removeLayer(l));
    indepLayers.forEach(l => map.removeLayer(l));
    map.removeLayer(layerLupino);
    contestedLayers.forEach(x => map.removeLayer(x.layer));
  }

  function anySideChecked(between) {
    between = Array.isArray(between) ? between : [];
    const a = macroKeyFromFactionName(between[0] || '');
    const b = macroKeyFromFactionName(between[1] || '');
    const checked = {
      Camarilla: el('cbCamarilla').checked,
      Anarch: el('cbAnarch').checked,
      Independentes: el('cbIndep').checked,
    };
    return !!(checked[a] || checked[b]);
  }

  function applyMacroVisibility() {
    if (el('selCamarillaDomain').value) return;

    clearMacroLayers();
    if (el('cbCamarilla').checked && layerCamarilla) {
      layerCamarilla.addTo(map);
      // Show Camarilla subdivisions (lordes) inside the macro watermark.
      camarillaLordLayers.forEach(l => l.addTo(map));
    }
    if (el('cbAnarch').checked) anarchLayers.forEach(l => l.addTo(map));
    if (el('cbIndep').checked) indepLayers.forEach(l => l.addTo(map));
    if (el('cbLupino').checked) layerLupino.addTo(map);
    contestedLayers.forEach(x => { if (anySideChecked(x.meta.between)) x.layer.addTo(map); });
  }

  function fillSelect(select, items, placeholder) {
    select.innerHTML = '';
    const opt0 = document.createElement('option');
    opt0.value = '';
    opt0.textContent = placeholder;
    select.appendChild(opt0);
    items.forEach(it => {
      const opt = document.createElement('option');
      opt.value = it.value;
      opt.textContent = it.label;
      select.appendChild(opt);
    });
  }

  const districtNames = (DISTRICTS_GEOJSON.features || [])
    .map(ft => ft && ft.properties ? ft.properties.ds_nome : '')
    .filter(Boolean)
    .sort((a,b)=>a.localeCompare(b));
  fillSelect(el('selDistrict'), districtNames.map(n => ({ value:n, label:n })), 'Selecione um distrito');

  fillSelect(el('selKindred'), allMembers.map(k => ({ value:k.id, label: `${k.name} (${k.clan}; ${k.sect || '-'})` })), 'Selecione um membro');

  const camDomainItems = (DATA.domains || [])
    .filter(d => macroKeyFromFactionName(d.faction) === 'Camarilla')
    .filter(d => (domainOwners[d.id] && (domainOwners[d.id].label || domainOwners[d.id].owner_entity_id)))
    .map(d => {
      const o = domainOwners[d.id] || {};
      const ownerLabel = o.label ? ` - ${o.label}` : '';
      return { value: d.id, label: `${d.name}${ownerLabel}` };
    });
  fillSelect(el('selCamarillaDomain'), camDomainItems, 'Selecione um territorio Camarilla');

  el('selDistrict').addEventListener('change', () => {
    const v = el('selDistrict').value;
    if (!v) return;
    districtOutlines.eachLayer(l => {
      const n = (l.feature && l.feature.properties) ? l.feature.properties.ds_nome : '';
      if (dk(n) === dk(v)) {
        l.fire('click');
        try { map.fitBounds(l.getBounds().pad(0.25), { animate:true, maxZoom: 14 }); } catch(e) {}
      }
    });
  });

  el('selCamarillaDomain').addEventListener('change', () => {
    const did = el('selCamarillaDomain').value;
    if (!did) {
      clearDomain();
      applyMacroVisibility();
      return;
    }

    el('cbCamarilla').checked = false;
    el('cbAnarch').checked = false;
    el('cbIndep').checked = false;
    el('cbLupino').checked = false;
    clearMacroLayers();

    showDomain(did, COLORS.Camarilla);
    const d = domainMeta.get(did) || {};
    const o = domainOwners[did] || null;
    const lines = [];
    lines.push('Territorio Camarilla: ' + (d.name || did));
    if (o && o.label) lines.push('Dono visivel: ' + o.label);
    const ds = DOMAIN_DISTRICTS[did] || [];
    if (ds.length) lines.push('Distritos: ' + ds.join(', '));
    const inHere = kindredList.filter(k => (k.map_domains || []).includes(did));
    lines.push('Cainitas do projeto associados a este territorio: ' + inHere.length);
    if (inHere.length) {
      lines.push('');
      lines.push('Nomes:');
      inHere.slice(0, 18).forEach(k => lines.push('- ' + k.name + ' (' + k.clan + '; ' + (k.role || '-') + ')'));
      if (inHere.length > 18) lines.push('- ...');
    }
    setTitle('Territorio: ' + (d.name || did));
    setPortrait('', '');
    setDetails(lines);
  });

  let kindredPin = null;
  function setKindredPin(lat, lon, color) {
    if (kindredPin) { try { map.removeLayer(kindredPin); } catch(e) {} kindredPin = null; }
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
    kindredPin = L.circleMarker([lat, lon], {
      pane: 'panePins',
      radius: 8,
      color: '#111111',
      weight: 3,
      fillColor: color || '#00c2ff',
      fillOpacity: 0.95,
    }).addTo(map);
  }

  const membersGroup = L.layerGroup();
  function memberIcon(k) {
    const ring = factionColorForMember(k);
    return L.divIcon({
      className: '',
      html: `<div style="width:12px;height:12px;border-radius:12px;background:#121212;border:2px solid ${ring};box-shadow:0 3px 10px rgba(0,0,0,0.38)"></div>`,
      iconSize:[12,12],
      iconAnchor:[6,6],
    });
  }

  function seedFromText(txt) {
    let h = 2166136261 >>> 0;
    const s = String(txt || '');
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  function mulberry32(seed) {
    let t = seed >>> 0;
    return function() {
      t += 0x6D2B79F5;
      let r = Math.imul(t ^ (t >>> 15), 1 | t);
      r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
      return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
    };
  }

  function organicSpread(baseLat, baseLon, members) {
    if (!Number.isFinite(baseLat) || !Number.isFinite(baseLon)) return [];
    const cosLat = Math.max(0.25, Math.cos((baseLat * Math.PI) / 180));
    const count = members.length;
    if (count <= 1) return [{ lat: baseLat, lon: baseLon }];

    const out = members.map((m, idx) => {
      const rng = mulberry32(seedFromText((m && m.k && m.k.id) || String(idx)));
      const u1 = rng();
      const u2 = rng();
      const maxR = 0.00010 + Math.min(0.00034, count * 0.000012); // ~11m a ~38m
      const r = maxR * Math.sqrt(u1);
      const angle = 2 * Math.PI * u2;
      return {
        x: r * Math.cos(angle),
        y: r * Math.sin(angle),
      };
    });

    // Relaxacao leve para evitar sobreposicao sem formar anel.
    const minDist = 0.000065;
    for (let pass = 0; pass < 3; pass++) {
      for (let i = 0; i < out.length; i++) {
        for (let j = i + 1; j < out.length; j++) {
          const dx = out[j].x - out[i].x;
          const dy = out[j].y - out[i].y;
          const d = Math.sqrt(dx*dx + dy*dy) || 0.000001;
          if (d < minDist) {
            const push = (minDist - d) * 0.5;
            const ux = dx / d;
            const uy = dy / d;
            out[i].x -= ux * push;
            out[i].y -= uy * push;
            out[j].x += ux * push;
            out[j].y += uy * push;
          }
        }
      }
    }

    return out.map(p => ({
      lat: baseLat + p.y,
      lon: baseLon + (p.x / cosLat),
    }));
  }

  let memberPinsCount = 0;
  function rebuildMembersPinsAndSelect() {
    fillSelect(
      el('selKindred'),
      allMembers.map(k => ({ value: k.id, label: `${k.name} (${k.clan}; ${k.sect || '-'})` })),
      'Selecione um membro'
    );

    try { membersGroup.clearLayers(); } catch(e) {}
    const groupedMembers = new Map();
    allMembers.forEach(k => {
      const p = approximateCoordsForMember(k);
      if (!Number.isFinite(p.lat) || !Number.isFinite(p.lon)) return;
      const key = `${p.lat.toFixed(5)}|${p.lon.toFixed(5)}`;
      const arr = groupedMembers.get(key) || [];
      arr.push({ k, p });
      groupedMembers.set(key, arr);
    });

    memberPinsCount = 0;
    groupedMembers.forEach(arr => {
      const spread = organicSpread(arr[0].p.lat, arr[0].p.lon, arr);
      arr.forEach((entry, idx) => {
        const k = entry.k;
        const p = spread[idx] || { lat: entry.p.lat, lon: entry.p.lon };
        const m = L.marker([p.lat, p.lon], { pane: 'panePins', icon: memberIcon(k) });
        m.bindTooltip(k.name, { sticky: true, opacity: 0.94 });
        m.on('click', () => {
          const sel = el('selKindred');
          sel.value = k.id;
          sel.dispatchEvent(new Event('change'));
        });
        membersGroup.addLayer(m);
        memberPinsCount += 1;
      });
    });
    setStatusText();
  }

  function normalizeBookEntity(e) {
    const kind = String((e && e.kind) || 'kindred');
    const fallbackClan = kind === 'ghoul' ? 'Ghoul' : (kind === 'mortal' ? 'Mortal' : '-');
    const name = (e && (e.display_name || e.name || e.id)) || 'Sem nome';
    return {
      id: String((e && e.id) || ''),
      name: String(name),
      clan: String((e && e.clan) || fallbackClan),
      sect: String((e && (e.sect_norm || e.sect)) || (kind === 'mortal' ? 'Mortal' : '-')),
      role: String((e && e.role) || ''),
      tier: String((e && e.tier) || ''),
      kind: kind,
      domain_raw: String((e && e.domain) || ''),
      map_domains: Array.isArray(e && e.map_domains) ? e.map_domains : [],
      residence_id: String((e && e.residence_id) || ''),
      coteries: Array.isArray(e && e.coteries_all) ? e.coteries_all : (Array.isArray(e && e.coteries) ? e.coteries : []),
      mortal_footprint: [],
      appearance_explicit: String((e && e.appearance_explicit) || ''),
      portrait_path: (e && e.portrait_path)
        ? String(e.portrait_path)
        : (e && e.file_stem ? `../05_ASSETS/portraits/${String(e.file_stem)}.jpg` : ''),
    };
  }

  async function tryLoadMembersFromBook() {
    const urls = [
      '../07_LIVRO_BY_NIGHT/index.html',
      '../book/index.html',
    ];
    for (const u of urls) {
      try {
        const res = await fetch(u, { cache: 'no-store' });
        if (!res.ok) continue;
        const html = await res.text();
        const m = html.match(/<script id="bookDataJson" type="application\\/json">([\\s\\S]*?)<\\/script>/i);
        if (!m) continue;
        const parsed = JSON.parse(m[1]);
        const ents = Array.isArray(parsed && parsed.entities) ? parsed.entities : [];
        if (!ents.length) continue;
        const normalized = ents
          .map(normalizeBookEntity)
          .filter(x => x && x.id && x.name);
        if (!normalized.length) continue;
        allMembers = normalized;
        rebuildMembersPinsAndSelect();
        return true;
      } catch (_e) {}
    }
    return false;
  }

  el('selKindred').addEventListener('change', () => {
    const id = el('selKindred').value;
    const k = allMembers.find(x => x.id === id);
    if (!k) return;

    el('selCamarillaDomain').value = '';
    applyMacroVisibility();

    const did = (k.map_domains || [])[0] || '';
    if (did) showDomain(did, '#00c2ff'); else clearDomain();

    const approx = approximateCoordsForMember(k);
    const lat = approx.lat;
    const lon = approx.lon;
    setKindredPin(lat, lon, '#00c2ff');
    try { map.setView([lat, lon], Math.max(map.getZoom(), 13), { animate:true }); } catch(e) {}

    const lines = [];
    lines.push('Membro: ' + k.name);
    lines.push('Tipo: ' + memberTypeLabel(k));
    lines.push('Seita: ' + (k.sect || '-'));
    lines.push('Cla: ' + (k.clan || '-'));
    if (k.role) lines.push('Papel: ' + k.role);
    if (k.tier) lines.push('Tier: ' + k.tier);
    if (k.domain_raw) lines.push('Dominio (texto): ' + k.domain_raw);
    if (Array.isArray(k.coteries) && k.coteries.length) {
      lines.push('');
      lines.push('Coteries/associacoes:');
      k.coteries.slice(0,8).forEach(cid => {
        const meta = (DATA.coteries || []).find(x => x && x.id === cid) || null;
        const nm = meta ? (meta.name || cid) : cid;
        lines.push('- ' + nm);
      });
      if (k.coteries.length > 8) lines.push('- ...');
    }
    if (k.appearance_explicit) {
      lines.push('');
      lines.push('Aparencia (para imagem):');
      lines.push(String(k.appearance_explicit));
    }
    if (Array.isArray(k.mortal_footprint) && k.mortal_footprint.length) {
      lines.push('');
      lines.push('Atuacao mortal:');
      k.mortal_footprint.slice(0,6).forEach(x => lines.push('- ' + x));
    }
    setTitle(k.name + ' (' + k.clan + ')');
    setPortrait(k.portrait_path || '', 'Retrato: ' + k.name);
    setDetails(lines);
  });

  ['cbCamarilla','cbAnarch','cbIndep','cbLupino'].forEach(id => el(id).addEventListener('change', applyMacroVisibility));
  el('cbPois').addEventListener('change', () => {
    if (el('cbPois').checked) poiGroup.addTo(map); else poiGroup.removeFrom(map);
  });
  el('cbMembers').addEventListener('change', () => {
    if (el('cbMembers').checked) membersGroup.addTo(map); else membersGroup.removeFrom(map);
  });

  poiGroup.addTo(map);
  membersGroup.addTo(map);
  function setStatusText() {
    setStatus(
      'Marque faccoes para ver dominio macro por distrito. Marque NPCs para pins dos membros da cidade e Pontos para locais relevantes. Clique em qualquer area/pin para abrir detalhes no painel da direita. ' +
      `Pins de membros carregados: ${memberPinsCount}.`
    );
  }

  rebuildMembersPinsAndSelect();
  applyMacroVisibility();
  setTimeout(() => {
    try { map.invalidateSize(); } catch(e) {}
    try { map.fitBounds(districtOutlines.getBounds().pad(0.05), { animate:true }); } catch(e) {}
  }, 80);
  setTimeout(() => { try { map.invalidateSize(); } catch(e) {} }, 260);
  setTimeout(() => { try { map.invalidateSize(); } catch(e) {} }, 640);
  window.addEventListener('resize', () => {
    try { map.invalidateSize(false); } catch(e) {}
  });
  tryLoadMembersFromBook();
  </script>
</body>
</html>
