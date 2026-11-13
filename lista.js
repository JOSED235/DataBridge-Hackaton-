// Lista de predios para brigadas: CSV para Excel en español (";" y coma decimal) y XLSX sin dependencias,
// para que el visor siga funcionando sin internet. Lo usa app.js; tests/test_visor_lista.py lo prueba con Node.
(function (global) {
  const COLAS = {
    inspeccion_priorizada: 'Inspección priorizada',
    verificar_dato_satelital: 'Verificar en terreno: sin dato satelital',
    verificar_predio_sin_construccion: 'Verificar: predio sin construcción registrada',
  };
  const MOTIVOS = {
    danio: 'daño', vulnerabilidad: 'vulnerabilidad', exposicion: 'ocupantes', suelo: 'suelo',
    altura: 'altura', acceso_salud: 'lejanía a salud', bloqueo_via: 'bloqueo de vía',
  };
  const num = (v) => (v == null || v === '' || Number.isNaN(Number(v)) ? null : Number(v));

  // [encabezado, ancho en Excel, valor, tipo]
  const COLUMNAS = [
    ['Posición', 9, (p) => num(p.posicion), 'entero'],
    ['ID predio', 10, (p) => (p.id == null ? '' : String(p.id)), 'texto'],
    ['Comuna', 8, (p) => num(p.comuna), 'entero'],
    ['Barrio', 26, (p) => p.barrio ?? '', 'texto'],
    ['Prioridad', 30, (p) => p.prioridad ?? '', 'texto'],
    ['Índice de riesgo', 10, (p) => num(p.indice_riesgo), 'decimal'],
    ['Cola de trabajo', 40, (p) => COLAS[p.cola_trabajo] ?? p.cola_trabajo ?? '', 'texto'],
    ['Motivos principales', 36, (p) => String(p.motivos_principales ?? '').split(', ').filter(Boolean).map((m) => MOTIVOS[m] ?? m).join(', '), 'texto'],
    ['Estado satelital', 34, (p) => p.estado ?? 'Sin dato', 'texto'],
    ['Pisos', 7, (p) => num(p.pisos), 'entero'],
    ['Fuente de pisos', 26, (p) => p.pisos_fuente ?? '', 'texto'],
    ['Distancia a salud (m)', 11, (p) => (num(p.dist_salud_m) == null ? null : Math.round(p.dist_salud_m)), 'entero'],
    ['Puede bloquear vía', 11, (p) => (p.puede_bloquear_via ? 'Sí' : 'No'), 'texto'],
    ['Longitud', 12, (p) => num(p.lon), 'coord'],
    ['Latitud', 12, (p) => num(p.lat), 'coord'],
  ];
  const DECIMALES = { decimal: 3, coord: 6 };

  function csv(predios) {
    const celda = (v, tipo) => {
      if (v == null || v === '') return '';
      if (typeof v === 'number') return (tipo in DECIMALES ? v.toFixed(DECIMALES[tipo]) : String(v)).replace('.', ',');
      return /[";\r\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
    };
    const filas = predios.map((p) => COLUMNAS.map(([, , valor, tipo]) => celda(valor(p), tipo)).join(';'));
    return `﻿${[COLUMNAS.map((c) => c[0]).join(';'), ...filas].join('\r\n')}\r\n`;  // BOM: Excel lee las tildes
  }

  // --- XLSX: libro OOXML mínimo (estilos, encabezado fijo, autofiltro) empaquetado en ZIP sin compresión ---
  const esc = (s) => String(s).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const letra = (i) => { let s = ''; for (i += 1; i > 0; i = Math.floor((i - 1) / 26)) s = String.fromCharCode(65 + ((i - 1) % 26)) + s; return s; };
  const ESTILO = { encabezado: 1, decimal: 2, coord: 3, entero: 4, texto: 0 };

  function hojaXml({ columnas, filas, filtro }) {
    const ult = letra(columnas.length - 1);
    const celda = (v, ref, estilo) => {
      if (v == null || v === '') return '';
      if (typeof v === 'number') return `<c r="${ref}" s="${estilo}"><v>${v}</v></c>`;
      return `<c r="${ref}" s="${estilo}" t="inlineStr"><is><t xml:space="preserve">${esc(v)}</t></is></c>`;
    };
    const encabezado = `<row r="1" ht="30" customHeight="1">${columnas.map((c, i) => celda(c.titulo, `${letra(i)}1`, ESTILO.encabezado)).join('')}</row>`;
    const cuerpo = filas.map((fila, r) => `<row r="${r + 2}">${fila.map((v, i) =>
      celda(v, `${letra(i)}${r + 2}`, typeof v === 'number' ? ESTILO[columnas[i].tipo] ?? 0 : 0)).join('')}</row>`).join('');
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      + '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
      + `<dimension ref="A1:${ult}${filas.length + 1}"/>`
      + '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
      + `<cols>${columnas.map((c, i) => `<col min="${i + 1}" max="${i + 1}" width="${c.ancho}" customWidth="1"/>`).join('')}</cols>`
      + `<sheetData>${encabezado}${cuerpo}</sheetData>`
      + (filtro ? `<autoFilter ref="A1:${ult}${filas.length + 1}"/>` : '')
      + '</worksheet>';
  }

  const ESTILOS = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    + '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    + '<numFmts count="2"><numFmt numFmtId="164" formatCode="0.000"/><numFmt numFmtId="165" formatCode="0.000000"/></numFmts>'
    + '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
    + '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
    + '<fill><patternFill patternType="solid"><fgColor rgb="FF1E232B"/><bgColor indexed="64"/></patternFill></fill></fills>'
    + '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
    + '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    + '<cellXfs count="5"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    + '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>'
    + '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    + '<xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    + '<xf numFmtId="1" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/></cellXfs>'
    + '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>';

  let tablaCrc;
  function crc32(datos) {
    if (!tablaCrc) {
      tablaCrc = new Uint32Array(256);
      for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; tablaCrc[n] = c >>> 0; }
    }
    let c = 0xffffffff;
    for (let i = 0; i < datos.length; i++) c = tablaCrc[(c ^ datos[i]) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  }

  function zip(archivos) {
    const enc = new TextEncoder();
    const locales = [], centrales = [];
    let desplazamiento = 0;
    for (const { nombre, texto } of archivos) {
      const n = enc.encode(nombre), d = enc.encode(texto), crc = crc32(d);
      const local = new DataView(new ArrayBuffer(30));
      [[0, 0x04034b50, 4], [4, 20, 2], [10, 0x21, 2], [14, crc, 4], [18, d.length, 4], [22, d.length, 4], [26, n.length, 2]]
        .forEach(([o, v, t]) => (t === 4 ? local.setUint32(o, v, true) : local.setUint16(o, v, true)));
      const central = new DataView(new ArrayBuffer(46));
      [[0, 0x02014b50, 4], [4, 20, 2], [6, 20, 2], [12, 0x21, 2], [16, crc, 4], [20, d.length, 4], [24, d.length, 4], [28, n.length, 2], [42, desplazamiento, 4]]
        .forEach(([o, v, t]) => (t === 4 ? central.setUint32(o, v, true) : central.setUint16(o, v, true)));
      locales.push(new Uint8Array(local.buffer), n, d);
      centrales.push(new Uint8Array(central.buffer), n);
      desplazamiento += 30 + n.length + d.length;
    }
    const tamCentral = centrales.reduce((s, a) => s + a.length, 0);
    const fin = new DataView(new ArrayBuffer(22));
    [[0, 0x06054b50, 4], [8, archivos.length, 2], [10, archivos.length, 2], [12, tamCentral, 4], [16, desplazamiento, 4]]
      .forEach(([o, v, t]) => (t === 4 ? fin.setUint32(o, v, true) : fin.setUint16(o, v, true)));
    const partes = [...locales, ...centrales, new Uint8Array(fin.buffer)];
    const salida = new Uint8Array(partes.reduce((s, a) => s + a.length, 0));
    let o = 0;
    for (const a of partes) { salida.set(a, o); o += a.length; }
    return salida;
  }

  // predios: propiedades con lon/lat; notas: [[campo, valor], ...] para la hoja "Notas".
  function xlsx(predios, notas) {
    const hojas = [
      { nombre: 'Lista', filtro: true, columnas: COLUMNAS.map(([titulo, ancho, , tipo]) => ({ titulo, ancho, tipo })),
        filas: predios.map((p) => COLUMNAS.map(([, , valor]) => valor(p))) },
      { nombre: 'Notas', filtro: false, columnas: [{ titulo: 'Campo', ancho: 28, tipo: 'texto' }, { titulo: 'Valor', ancho: 100, tipo: 'texto' }],
        filas: notas },
    ];
    const ult = letra(COLUMNAS.length - 1);
    const archivos = [
      { nombre: '[Content_Types].xml', texto: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
        + '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        + '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        + hojas.map((_, i) => `<Override PartName="/xl/worksheets/sheet${i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`).join('')
        + '</Types>' },
      { nombre: '_rels/.rels', texto: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>' },
      { nombre: 'xl/workbook.xml', texto: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        + `<sheets>${hojas.map((h, i) => `<sheet name="${h.nombre}" sheetId="${i + 1}" r:id="rId${i + 1}"/>`).join('')}</sheets>`
        + `<definedNames><definedName name="_xlnm._FilterDatabase" localSheetId="0" hidden="1">Lista!$A$1:$${ult}$${predios.length + 1}</definedName></definedNames></workbook>` },
      { nombre: 'xl/_rels/workbook.xml.rels', texto: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + hojas.map((_, i) => `<Relationship Id="rId${i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${i + 1}.xml"/>`).join('')
        + `<Relationship Id="rId${hojas.length + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>` },
      { nombre: 'xl/styles.xml', texto: ESTILOS },
      ...hojas.map((h, i) => ({ nombre: `xl/worksheets/sheet${i + 1}.xml`, texto: hojaXml(h) })),
    ];
    return zip(archivos);
  }

  const api = { COLUMNAS, csv, xlsx };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else global.Lista = api;
})(this);
