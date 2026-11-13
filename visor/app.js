// Visor de prioridad de inspección ante réplicas. Datos en ./data (exportados por notebooks/03_gold).
const { MapboxOverlay, GeoJsonLayer, ColumnLayer, ScatterplotLayer, HeatmapLayer, TextLayer } = deck;

const CALI = { longitude: -76.522, latitude: 3.43, zoom: 11.6, pitch: 0, bearing: 0 };
const EPICENTRO = [-76.2558, 4.8601];
const ESTILO_ONLINE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';
const ESTILO_OFFLINE = { version: 8, sources: {}, layers: [{ id: 'fondo', type: 'background', paint: { 'background-color': '#0e1013' } }] };

const PRIORIDAD = {
  'Muy alta': [255, 59, 48], 'Alta': [255, 149, 0], 'Media': [255, 214, 10],
  'Baja': [70, 78, 92], 'Sin dato: verificar en terreno': [150, 120, 200],
  'Sin construcción registrada: verificar': [90, 170, 220],
};
const RAMPA = [[38, 70, 83], [42, 157, 143], [233, 196, 106], [244, 162, 97], [231, 111, 81], [200, 30, 30]];

const estado = {
  modo: 'prioridad', comuna: '', soloAlta: false,
  capas: { edificios: true, calor: false, comunas: true, vias: true, salud: true, emergencia: false, sismos: false },
};
const datos = {};
const $ = (id) => document.getElementById(id);
const fmt = (n, d = 0) => Number(n).toLocaleString('es-CO', { maximumFractionDigits: d, minimumFractionDigits: d });

function rampa(t) {
  t = Math.max(0, Math.min(1, t || 0)) * (RAMPA.length - 1);
  const i = Math.min(Math.floor(t), RAMPA.length - 2), f = t - i;
  return RAMPA[i].map((c, k) => Math.round(c + (RAMPA[i + 1][k] - c) * f));
}

function colorEdificio(p) {
  if (estado.modo === 'prioridad') return PRIORIDAD[p.prioridad] || [120, 120, 120];
  if (p.sin_dato_satelital) return PRIORIDAD['Sin dato: verificar en terreno'];
  return rampa(estado.modo === 'indice' ? p.indice_riesgo / maxIndice : p.sev_estado);
}
let maxIndice = 1;

const cargar = (f) => fetch(`data/${f}`).then((r) => (r.ok ? r.json() : null)).catch(() => null);

async function estiloBase() {
  try {
    const ctrl = new AbortController();
    setTimeout(() => ctrl.abort(), 4000);
    const r = await fetch(ESTILO_ONLINE, { signal: ctrl.signal });
    if (r.ok) return ESTILO_ONLINE;
  } catch (_) { /* sin internet: fondo plano y las comunas dibujan la ciudad */ }
  return ESTILO_OFFLINE;
}

// 2 predios de la fuente tienen área 0 m² y su polígono se exporta vacío: no se dibujan, pero sí cuentan en los KPI.
const dibujable = (f) => { const c = f.geometry && f.geometry.coordinates; return Boolean(c && c.length && c[0].length); };

function edificiosFiltrados() {
  return datos.edificios.features.filter((f) => {
    const p = f.properties;
    if (!dibujable(f)) return false;
    if (estado.comuna && String(p.comuna) !== estado.comuna) return false;
    if (estado.soloAlta && !['Muy alta', 'Alta'].includes(p.prioridad)) return false;
    return true;
  });
}

function capas() {
  const ed = edificiosFiltrados();
  const sonPuntos = ed.length && ed[0].geometry.type === 'Point';
  const tip = (info) => mostrarTip(info);
  const L = [];

  if (estado.capas.comunas) L.push(new GeoJsonLayer({
    id: 'comunas', data: datos.comunas, pickable: true, stroked: true, filled: true,
    getFillColor: (f) => [...rampa(f.properties.indice_p90 / maxP90), estado.capas.edificios ? 40 : 140],
    getLineColor: (f) => String(f.properties.comuna) === estado.comuna ? [255, 255, 255] : [140, 150, 165, 160],
    getLineWidth: (f) => String(f.properties.comuna) === estado.comuna ? 3 : 1, lineWidthUnits: 'pixels',
    updateTriggers: { getLineColor: estado.comuna, getLineWidth: estado.comuna, getFillColor: estado.capas.edificios },
    onHover: tip,
  }));
  if (estado.capas.vias && datos.vias) L.push(new GeoJsonLayer({
    id: 'vias', data: datos.vias, getLineColor: [200, 205, 215, 110], getLineWidth: 1.5, lineWidthUnits: 'pixels',
  }));
  if (estado.capas.calor) L.push(new HeatmapLayer({
    id: 'calor', data: ed, getPosition: (f) => centro(f), getWeight: (f) => f.properties.indice_riesgo ** 2, radiusPixels: 40,
  }));
  if (estado.capas.edificios) {
    const comun = {
      id: 'edificios', pickable: true, onHover: tip, extruded: true,
      getFillColor: (f) => colorEdificio(f.properties), getElevation: (f) => f.properties.sin_construccion_registrada ? 0 : (f.properties.pisos || 1) * 3,
      updateTriggers: { getFillColor: estado.modo },
    };
    L.push(sonPuntos
      ? new ColumnLayer({ ...comun, data: ed, diskResolution: 6, radius: 9, elevationScale: 2, getPosition: (f) => f.geometry.coordinates })
      : new GeoJsonLayer({ ...comun, data: ed, stroked: false }));
    if (estado.modo === 'prioridad') L.push(new ScatterplotLayer({
      id: 'marcas', data: ed.filter((f) => ['Muy alta', 'Alta'].includes(f.properties.prioridad)), pickable: true, onHover: tip,
      getPosition: (f) => centro(f), getFillColor: (f) => [...PRIORIDAD[f.properties.prioridad], 230],
      getRadius: (f) => (f.properties.prioridad === 'Muy alta' ? 5 : 3), radiusUnits: 'pixels',
      stroked: true, getLineColor: [14, 16, 19], lineWidthUnits: 'pixels', getLineWidth: 1,
    }));
  }
  if (estado.capas.comunas) L.push(new TextLayer({
    id: 'rotulos', data: datos.comunas.features, getPosition: (f) => centro(f),
    getText: (f) => `C${f.properties.comuna} · #${f.properties.ranking}`, getSize: 15, getColor: [255, 255, 255],
    fontWeight: 700, outlineWidth: 3, outlineColor: [14, 16, 19], fontSettings: { sdf: true },
    characterSet: 'auto', billboard: true,
  }));
  const puntos = (id, data, color, radio) => new ScatterplotLayer({
    id, data: data.features, pickable: true, onHover: tip, getPosition: (f) => centro(f), getFillColor: color,
    getRadius: radio, radiusUnits: 'pixels', stroked: true, getLineColor: [14, 16, 19], lineWidthUnits: 'pixels', getLineWidth: 1,
  });
  if (estado.capas.salud && datos.salud) L.push(puntos('salud', datos.salud, [62, 207, 142, 150], 3));
  if (estado.capas.emergencia && datos.emergencia) L.push(puntos('emergencia', datos.emergencia, [90, 160, 255], 5));
  if (estado.capas.sismos && datos.sismos) L.push(new ScatterplotLayer({
    id: 'sismos', data: datos.sismos.features, pickable: true, onHover: tip, getPosition: (f) => f.geometry.coordinates,
    getRadius: (f) => 2 ** f.properties.mag * 60, getFillColor: (f) => f.properties.mag >= 7 ? [255, 59, 48, 220] : [255, 149, 0, 120],
    stroked: true, getLineColor: [255, 255, 255, 120], lineWidthUnits: 'pixels', getLineWidth: 1,
  }));
  return L;
}

function centro(f) {
  let g = f.geometry;
  if (g.type === 'GeometryCollection') g = g.geometries.find((x) => x.type.endsWith('Polygon')) || g.geometries[0];  // polígonos reparados con make_valid
  if (g.type === 'Point') return g.coordinates;
  const anillo = g.type === 'Polygon' ? g.coordinates[0] : g.coordinates[0][0];
  const s = anillo.reduce((a, c) => [a[0] + c[0], a[1] + c[1]], [0, 0]);
  return [s[0] / anillo.length, s[1] / anillo.length];
}

function mostrarTip({ object, x, y, layer }) {
  const el = $('tip');
  if (!object) { el.style.display = 'none'; return; }
  const p = object.properties;
  let h = '';
  if (layer.id === 'edificios' || layer.id === 'marcas') h = `<b>${p.prioridad}</b> · índice ${fmt(p.indice_riesgo, 2)}<br>Comuna ${p.comuna ?? '–'} · ${p.barrio ?? ''}<br>
    ${p.pisos ?? 'sin dato'} pisos (${p.pisos_fuente ?? 'fuente no informada'}) · estado: ${p.estado ?? 'sin dato'}<br>Suelo: microzona ${p.microzona ?? '–'} · amplifica ${fmt(p.amplif_suelo, 2)}×<br>
    Motivos: ${p.motivos_principales ?? 'consultar tabla oro'}<br>Salud más cercana: ${fmt(p.dist_salud_m)} m${p.puede_bloquear_via ? '<br><b>Sus escombros podrían bloquear una vía principal</b>' : ''}`;
  else if (layer.id === 'comunas') h = `<b>Comuna ${p.comuna}</b> · puesto ${p.ranking}<br>${fmt(p.n_predios ?? p.n_edificios)} predios ·
    ${fmt(p.pct_alta_escombros, 1)} % alta prob. escombros<br>${fmt(p.pct_sin_dato, 1)} % sin dato satelital<br>
    ${p.n_salud} centros de salud · ${p.n_bomberos} est. de bomberos`;
  else if (layer.id === 'sismos') h = `<b>M${p.mag}</b> · ${new Date(p.time).toLocaleString('es-CO')}<br>${p.place}`;
  else h = `<b>${p.name || 'Sin nombre'}</b><br>${p.amenity || ''}`;
  el.innerHTML = h;
  el.style.display = 'block';
  el.style.left = `${x + 14}px`;
  el.style.top = `${y + 14}px`;
}

function kpis() {
  const ed = estado.comuna ? datos.edificios.features.filter((f) => String(f.properties.comuna) === estado.comuna) : datos.edificios.features;
  const n = ed.length || 1;
  const cuenta = (fn) => ed.filter((f) => fn(f.properties)).length;
  const alta = cuenta((p) => p.alta_escombros), sd = cuenta((p) => p.sin_dato_satelital);
  const muy = cuenta((p) => p.prioridad === 'Muy alta');
  const gente = ed.reduce((s, f) => { const p = f.properties; return s + (p.sev_estado >= 0.7 && !p.sin_construccion_registrada ? (p.ocupantes_noche || 0) : 0); }, 0);
  $('ambito').textContent = estado.comuna ? `· comuna ${estado.comuna}` : '· inventario analizado de Cali';
  $('kpis').innerHTML = [
    ['', fmt(ed.length), 'predios analizados'],
    ['hot', `${fmt((100 * alta) / n, 1)} %`, 'alta prob. de escombros'],
    ['', `${fmt((100 * cuenta((p) => p.sev_estado >= 0.7)) / n, 1)} %`, 'con daño visible (escombros o techo)'],
    ['hot', fmt(muy), 'prioridad muy alta'],
    ['hot', fmt(gente), 'ocupación GEM asignada con señal de daño (puede repetirse)'],
    ['', `${fmt((100 * sd) / n, 1)} %`, 'sin dato satelital'],

  ].map(([c, v, t]) => `<div class="kpi ${c}"><b>${v}</b><small>${t}</small></div>`).join('');
}

function leyenda() {
  $('leyenda').innerHTML = estado.modo === 'prioridad'
    ? Object.entries(PRIORIDAD).map(([k, c]) => `<span><i style="background:rgb(${c})"></i>${k.replace(': verificar en terreno', '')}</span>`).join('')
    : `<span><i style="background:rgb(${RAMPA[0]})"></i>bajo</span><span><i style="background:rgb(${RAMPA[3]})"></i>medio</span>
       <span><i style="background:rgb(${RAMPA[5]})"></i>alto</span><span><i style="background:rgb(${PRIORIDAD['Sin dato: verificar en terreno']})"></i>sin dato</span>`;
}

function ranking() {
  const cs = [...datos.comunas.features].sort((a, b) => a.properties.ranking - b.properties.ranking);
  $('ranking').innerHTML = cs.map((f) => {
    const p = f.properties;
    return `<li data-c="${p.comuna}" class="${String(p.comuna) === estado.comuna ? 'on' : ''}" tabindex="0">
      <div>Comuna ${p.comuna}<div class="bar" style="width:${(100 * p.indice_p90) / maxP90}%"></div></div>
      <span class="val">${fmt(p.indice_p90, 2)}</span></li>`;
  }).join('');
}
let maxP90 = 1;

function irAComuna(c) {
  const f = datos.comunas.features.find((x) => String(x.properties.comuna) === String(c));
  if (!f) return;
  const anillo = f.geometry.type === 'Polygon' ? f.geometry.coordinates[0] : f.geometry.coordinates.flat(1);
  const xs = anillo.map((p) => p[0]), ys = anillo.map((p) => p[1]);
  map.fitBounds([[Math.min(...xs), Math.min(...ys)], [Math.max(...xs), Math.max(...ys)]], { padding: 60, pitch: 45, duration: 1200 });
}

function render() {
  overlay.setProps({ layers: capas() });
  kpis(); leyenda(); ranking();
  $('selComuna').value = estado.comuna;
  $('soloAlta').checked = estado.soloAlta;
  document.querySelectorAll('[data-capa]').forEach((el) => { el.checked = estado.capas[el.dataset.capa]; });
  document.querySelectorAll('#modo button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.v === estado.modo));
}

// --- Recorrido guiado: del problema a la recomendación. TODO-VIERNES: textos con las cifras reales. ---
const top1 = () => datos.comunas.features.reduce((a, b) => (a.properties.ranking < b.properties.ranking ? a : b)).properties.comuna;
const PASOS = [
  {
    t: '1 · El sismo', p: () => 'M7,4 a 116 km de profundidad, 165 km al norte de Cali. Más de 70 réplicas de magnitud 2,5 o más registradas por el USGS hasta noviembre.',
    vista: { longitude: -76.4, latitude: 4.15, zoom: 7.2, pitch: 0, bearing: 0 },
    s: { capas: { sismos: true, comunas: true, edificios: false }, comuna: '', soloAlta: false },
  },
  {
    t: '2 · Qué pasó en Cali', p: () => `El análisis satelital marca ${$('kpis').children[1].querySelector('b').textContent} de los edificios con alta probabilidad de escombros. Las comunas más afectadas se concentran en las zonas oscuras del mapa.`,
    vista: { ...CALI }, s: { modo: 'escombros', capas: { edificios: false, comunas: true, calor: true }, comuna: '', soloAlta: false },
  },
  {
    t: '3 · Por qué importa', p: () => 'La altura, la densidad de edificios y la cercanía a vías y servicios de salud cambian el impacto de una réplica: un edificio alto dañado junto a una vía principal puede cortar el acceso de las ambulancias.',
    vista: { ...CALI, zoom: 13, pitch: 55, bearing: -20 }, s: { modo: 'indice', capas: { edificios: true, comunas: false, vias: true, salud: true }, comuna: '', soloAlta: false },
  },
  {
    t: '4 · Qué hacer ante réplicas', p: () => `Inspeccionar primero los edificios de prioridad muy alta, empezando por la comuna ${top1()}, y despejar las vías que sus escombros podrían bloquear. Los edificios sin dato satelital van a verificación en terreno.`,
    vista: null, s: { modo: 'prioridad', capas: { edificios: true, comunas: true, vias: true, salud: true }, soloAlta: true },
    al: () => { estado.comuna = String(top1()); irAComuna(top1()); },
  },
];
let paso = -1;
function irPaso(i) {
  paso = i;
  const P = PASOS[i];
  const base = { edificios: false, calor: false, comunas: false, vias: false, salud: false, emergencia: false, sismos: false };
  Object.assign(estado, P.s, { capas: { ...base, ...P.s.capas } });
  if (P.al) P.al();
  if (P.vista) map.flyTo({ center: [P.vista.longitude, P.vista.latitude], zoom: P.vista.zoom, pitch: P.vista.pitch, bearing: P.vista.bearing, duration: 1600 });
  render();
  $('tour').classList.add('on');
  $('tourT').textContent = P.t;
  $('tourP').textContent = P.p();
  $('tourN').textContent = `${i + 1}/${PASOS.length}`;
  $('tourPrev').disabled = i === 0;
  $('tourNext').textContent = i === PASOS.length - 1 ? 'Cerrar' : 'Siguiente';
}

// --- Arranque ---
let map, overlay;
(async () => {
  map = new maplibregl.Map({ container: 'map', style: await estiloBase(), center: [CALI.longitude, CALI.latitude], zoom: CALI.zoom, attributionControl: { compact: true } });
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');
  overlay = new MapboxOverlay({ interleaved: false, layers: [] });
  map.addControl(overlay);

  const [edificios, comunas, salud, emergencia, vias, sismos] = await Promise.all(
    ['edificios', 'comunas', 'salud', 'emergencia', 'vias', 'sismos'].map((n) => cargar(`${n}.geojson`)));
  if (!edificios || !comunas) {
    document.body.insertAdjacentHTML('beforeend', '<p class="aviso" style="position:fixed;top:12px;right:12px">No se encontraron data/edificios.geojson o data/comunas.geojson. ¿Se abrió con un servidor local?</p>');
    return;
  }
  Object.assign(datos, { edificios, comunas, salud, emergencia, vias, sismos });
  if (await fetch('data/MUESTRA.txt').then((r) => r.ok).catch(() => false)) {  // lo crea scripts/simular_pipeline.py
    document.querySelector('aside').insertAdjacentHTML('afterbegin', '<p class="aviso" style="margin:0 0 14px">DATOS DE MUESTRA FICTICIOS. Reemplazar visor/data/ con los exportados de Databricks y borrar data/MUESTRA.txt.</p>');
  }
  maxIndice = Math.max(...edificios.features.map((f) => f.properties.indice_riesgo || 0)) || 1;
  maxP90 = Math.max(...comunas.features.map((f) => f.properties.indice_p90 || 0)) || 1;
  const nums = comunas.features.map((f) => f.properties.comuna).sort((a, b) => a - b);
  $('selComuna').insertAdjacentHTML('beforeend', nums.map((c) => `<option value="${c}">Comuna ${c}</option>`).join(''));

  $('selComuna').onchange = (e) => { estado.comuna = e.target.value; if (estado.comuna) irAComuna(estado.comuna); render(); };
  $('soloAlta').onchange = (e) => { estado.soloAlta = e.target.checked; render(); };
  document.querySelectorAll('[data-capa]').forEach((el) => { el.onchange = () => { estado.capas[el.dataset.capa] = el.checked; render(); }; });
  document.querySelectorAll('#modo button').forEach((b) => { b.onclick = () => { estado.modo = b.dataset.v; render(); }; });
  $('ranking').onclick = (e) => {
    const li = e.target.closest('li'); if (!li) return;
    estado.comuna = estado.comuna === li.dataset.c ? '' : li.dataset.c;
    if (estado.comuna) irAComuna(estado.comuna); else map.flyTo({ center: [CALI.longitude, CALI.latitude], zoom: CALI.zoom, pitch: 0 });
    render();
  };
  $('ranking').onkeydown = (e) => { if (e.key === 'Enter') e.target.click(); };
  $('btnTour').onclick = () => irPaso(0);
  $('tourNext').onclick = () => (paso < PASOS.length - 1 ? irPaso(paso + 1) : $('tour').classList.remove('on'));
  $('tourPrev').onclick = () => paso > 0 && irPaso(paso - 1);
  const xs = [], ys = [];
  edificios.features.filter(dibujable).forEach((f) => { const c = centro(f); xs.push(c[0]); ys.push(c[1]); });
  map.fitBounds([[Math.min(...xs), Math.min(...ys)], [Math.max(...xs), Math.max(...ys)]], { padding: { top: 40, bottom: 90, left: 40, right: 60 }, duration: 0 });
  render();
})();
