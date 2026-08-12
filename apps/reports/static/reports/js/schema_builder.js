/**
 * schema_builder.js - SITADC Youth Hub Phase 19 Dynamic Report Builder
 * Visual drag-and-drop Schema Designer.
 *
 * Three-panel WYSIWYG:  LEFT=palette | CENTER=canvas | RIGHT=inspector
 * Serialises state to hidden textarea on form submit.
 */

/* eslint-disable no-alert */
/* globals document, confirm */

const FIELD_TYPES = [
  {type:'TEXT',           label:'Single-line Text',     icon:'bi-type',              group:'Text'},
  {type:'MULTILINE_TEXT', label:'Multi-line Text',       icon:'bi-textarea-resize',   group:'Text'},
  {type:'RICH_TEXT',      label:'Rich Text',             icon:'bi-file-richtext',     group:'Text'},
  {type:'INTEGER',        label:'Integer',               icon:'bi-123',               group:'Numbers'},
  {type:'DECIMAL',        label:'Decimal',               icon:'bi-currency-dollar',   group:'Numbers'},
  {type:'CURRENCY',       label:'Currency',              icon:'bi-cash-coin',         group:'Numbers'},
  {type:'PERCENTAGE',     label:'Percentage',            icon:'bi-percent',           group:'Numbers'},
  {type:'DATE',           label:'Date',                  icon:'bi-calendar3',         group:'Date & Time'},
  {type:'TIME',           label:'Time',                  icon:'bi-clock',             group:'Date & Time'},
  {type:'DATETIME',       label:'Date & Time',           icon:'bi-calendar-date',     group:'Date & Time'},
  {type:'DROPDOWN',       label:'Dropdown',              icon:'bi-menu-button-wide',  group:'Selection'},
  {type:'MULTI_SELECT',   label:'Multi-select',          icon:'bi-ui-checks',         group:'Selection'},
  {type:'RADIO',          label:'Radio Buttons',         icon:'bi-ui-radios',         group:'Selection'},
  {type:'CHECKBOX',       label:'Checkboxes',            icon:'bi-check2-square',     group:'Selection'},
  {type:'TOGGLE',         label:'Toggle Switch',         icon:'bi-toggle-on',         group:'Selection'},
  {type:'IMAGE',          label:'Image Upload',          icon:'bi-image',             group:'Media'},
  {type:'DOCUMENT',       label:'Document Upload',       icon:'bi-file-earmark-text', group:'Media'},
  {type:'SIGNATURE',      label:'Signature',             icon:'bi-pen',               group:'Specialized'},
  {type:'GPS_COORDINATES',label:'GPS Coordinates',       icon:'bi-geo-alt',           group:'Specialized'},
  {type:'USER_SELECTOR',  label:'User Selector',         icon:'bi-person',            group:'Specialized'},
  {type:'FORMULA',        label:'Formula (calculated)',  icon:'bi-calculator',        group:'Advanced'},
  {type:'TABLE_GRID',     label:'Table / Grid',          icon:'bi-table',             group:'Advanced'},
  {type:'REPEATING_GROUP',label:'Repeating Group',       icon:'bi-layers',            group:'Advanced'},
];

/* ── State ── */
var state = {sections:[], selectedId:null, selectedType:null, dragPayload:null, sc:0, gc:0, fc:0};
function uid(p){return p+'_'+Date.now()+'_'+Math.random().toString(36).slice(2,7);}

var canvasEl, inspectorEl, hiddenTA, sbForm;

/* ── Init ── */
document.addEventListener('DOMContentLoaded', function(){
  hiddenTA = document.getElementById('id_schema');
  sbForm   = hiddenTA ? hiddenTA.closest('form') : null;
  if(!hiddenTA) return;
  buildShell();
  loadSchema();
  if(sbForm) sbForm.addEventListener('submit', syncTA);
  render();
});

/* ── Shell ── */
function buildShell(){
  hiddenTA.style.display='none';
  var s = document.createElement('div');
  s.className = 'sb-shell';
  s.innerHTML =
    '<div class="sb-palette">' +
      '<div class="sb-palette-header"><i class="bi bi-grid-3x3-gap me-1"></i>Field Types</div>' +
      '<div class="sb-palette-search-wrap"><input type="text" id="sbps" class="sb-palette-search" placeholder="Search..."></div>' +
      '<div id="sbpl"></div>' +
    '</div>' +
    '<div class="sb-canvas-wrap">' +
      '<div class="sb-canvas-toolbar">' +
        '<button type="button" class="sb-btn sb-btn-primary" id="sb-add-sec"><i class="bi bi-plus-lg me-1"></i>Add Section</button>' +
        '<button type="button" class="sb-btn sb-btn-outline" id="sb-prev-json"><i class="bi bi-braces me-1"></i>Preview JSON</button>' +
        '<div class="sb-toolbar-spacer"></div>' +
        '<span id="sb-ind" class="sb-save-indicator"><i class="bi bi-check-circle-fill text-success me-1"></i>Schema ready</span>' +
      '</div>' +
      '<div class="sb-canvas" id="sb-canvas"></div>' +
    '</div>' +
    '<div class="sb-inspector">' +
      '<div class="sb-inspector-header"><i class="bi bi-sliders me-1"></i>Properties</div>' +
      '<div id="sbi-body" class="sb-inspector-body"><p class="text-muted small px-3 pt-3">Select an element to edit its properties.</p></div>' +
    '</div>' +
    '<div class="sb-modal-overlay" id="sbmo" hidden>' +
      '<div class="sb-modal">' +
        '<div class="sb-modal-header"><span>Schema JSON Preview</span><button type="button" id="sbmc" aria-label="Close">\xD7</button></div>' +
        '<div class="sb-modal-body"><pre id="sbmj"></pre></div>' +
      '</div>' +
    '</div>';
  hiddenTA.parentElement.insertBefore(s, hiddenTA);
  canvasEl    = s.querySelector('#sb-canvas');
  inspectorEl = s.querySelector('#sbi-body');
  buildPalette();
  s.querySelector('#sbps').addEventListener('input', filterPal);
  s.querySelector('#sb-add-sec').addEventListener('click', addSection);
  s.querySelector('#sb-prev-json').addEventListener('click', function(){
    document.getElementById('sbmj').textContent = JSON.stringify(buildSchema(), null, 2);
    document.getElementById('sbmo').hidden = false;
  });
  s.querySelector('#sbmc').addEventListener('click', function(){ document.getElementById('sbmo').hidden = true; });
  s.querySelector('#sbmo').addEventListener('click', function(e){ if(e.target.id === 'sbmo') document.getElementById('sbmo').hidden = true; });
  canvasEl.addEventListener('dragover', function(e){ e.preventDefault(); });
  canvasEl.addEventListener('drop', canvasDrop);
}

/* ── Palette ── */
function buildPalette(){
  var list = document.getElementById('sbpl');
  var groups = {};
  FIELD_TYPES.forEach(function(ft){
    if(!groups[ft.group]) groups[ft.group] = [];
    groups[ft.group].push(ft);
  });
  Object.keys(groups).forEach(function(g){
    var h = document.createElement('div');
    h.className = 'sb-palette-group-header'; h.textContent = g;
    list.appendChild(h);
    groups[g].forEach(function(ft){
      var el = document.createElement('div');
      el.className = 'sb-palette-item'; el.draggable = true;
      el.innerHTML = '<i class="bi '+ft.icon+' me-2"></i>'+ft.label;
      el.addEventListener('dragstart', function(e){ state.dragPayload = {source:'palette', fieldType:ft.type, label:ft.label}; e.dataTransfer.effectAllowed='copy'; });
      el.addEventListener('dragend', function(){ state.dragPayload = null; });
      list.appendChild(el);
    });
  });
}

function filterPal(){
  var q = document.getElementById('sbps').value.toLowerCase();
  document.querySelectorAll('.sb-palette-item').forEach(function(el){
    el.style.display = el.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
  });
}

/* ── Schema load/save ── */
function loadSchema(){
  try{
    var p = JSON.parse(hiddenTA.value.trim());
    if(p.sections) state.sections = p.sections.map(impSec);
  } catch(e){}
}

function impSec(r){
  return {_id:r._builder_id||uid('sec'), name:r.name||'Section', code:r.code||'section',
          description:r.description||'', instructions:r.instructions||'',
          is_repeatable:!!r.is_repeatable, is_collapsible:r.is_collapsible!==false,
          sort_order:r.sort_order||0, groups:(r.groups||[]).map(impGrp)};
}
function impGrp(r){
  return {_id:r._builder_id||uid('grp'), name:r.name||'Group', code:r.code||'group',
          description:r.description||'', sort_order:r.sort_order||0, fields:(r.fields||[]).map(impFld)};
}
function impFld(r){
  return {_id:r._builder_id||uid('fld'), label:r.label||'Field', code:r.code||'field',
          field_type:r.field_type||'TEXT', data_type:r.data_type||'STRING',
          required:!!r.required, read_only:!!r.read_only, hidden:!!r.hidden,
          is_repeatable:!!r.is_repeatable, is_calculated:!!r.is_calculated,
          formula:r.formula||'', placeholder:r.placeholder||'',
          help_text:r.help_text||'', tooltip:r.tooltip||'', sort_order:r.sort_order||0};
}

function buildSchema(){
  return {sections: state.sections.map(function(s, si){
    return {
      _builder_id:s._id, name:s.name, code:s.code, description:s.description,
      instructions:s.instructions, is_repeatable:s.is_repeatable, is_collapsible:s.is_collapsible,
      sort_order:si,
      groups:(s.groups||[]).map(function(g, gi){
        return {
          _builder_id:g._id, name:g.name, code:g.code, description:g.description, sort_order:gi,
          fields:(g.fields||[]).map(function(f, fi){
            return {_builder_id:f._id, label:f.label, code:f.code, field_type:f.field_type,
                    data_type:f.data_type, required:f.required, read_only:f.read_only,
                    hidden:f.hidden, is_repeatable:f.is_repeatable, is_calculated:f.is_calculated,
                    formula:f.formula, placeholder:f.placeholder, help_text:f.help_text,
                    tooltip:f.tooltip, sort_order:fi};
          })
        };
      })
    };
  })};
}
function syncTA(){ hiddenTA.value = JSON.stringify(buildSchema(), null, 2); }

/* ── Canvas drop (from palette to blank canvas) ── */
function canvasDrop(e){
  e.preventDefault();
  var p = state.dragPayload;
  if(!p || p.source !== 'palette') return;
  if(state.sections.length === 0) addSection();
  var ls = state.sections[state.sections.length-1];
  if(ls.groups.length === 0) addGroup(ls._id);
  var lg = ls.groups[ls.groups.length-1];
  addField(ls._id, lg._id, p.fieldType);
  state.dragPayload = null;
}

/* ── Data mutations ── */
function addSection(){
  state.sc++;
  var id = uid('sec');
  state.sections.push({_id:id, name:'Section '+state.sc, code:'section_'+state.sc,
                        description:'', instructions:'', is_repeatable:false,
                        is_collapsible:true, sort_order:state.sections.length, groups:[]});
  dirty(); render(); sel(id, 'section');
}
function delSection(id){
  state.sections = state.sections.filter(function(s){ return s._id !== id; });
  if(state.selectedId === id){ state.selectedId = null; state.selectedType = null; }
  dirty(); render(); renderInspector();
}
function addGroup(sid){
  var sec = state.sections.find(function(s){ return s._id === sid; });
  if(!sec) return;
  state.gc++;
  var id = uid('grp');
  sec.groups.push({_id:id, name:'Field Group '+state.gc, code:'group_'+state.gc,
                   description:'', sort_order:sec.groups.length, fields:[]});
  dirty(); render(); sel(id, 'group');
}
function delGroup(sid, gid){
  var sec = state.sections.find(function(s){ return s._id === sid; });
  if(!sec) return;
  sec.groups = sec.groups.filter(function(g){ return g._id !== gid; });
  if(state.selectedId === gid){ state.selectedId = null; state.selectedType = null; }
  dirty(); render(); renderInspector();
}
function addField(sid, gid, ftype){
  ftype = ftype || 'TEXT';
  var sec = state.sections.find(function(s){ return s._id === sid; });
  if(!sec) return;
  var grp = sec.groups.find(function(g){ return g._id === gid; });
  if(!grp) return;
  state.fc++;
  var id  = uid('fld');
  var ft  = FIELD_TYPES.find(function(f){ return f.type === ftype; }) || FIELD_TYPES[0];
  grp.fields.push({_id:id, label:ft.label, code:ftype.toLowerCase()+'_'+state.fc,
                   field_type:ftype, data_type:'STRING', required:false, read_only:false,
                   hidden:false, is_repeatable:false, is_calculated:false, formula:'',
                   placeholder:'', help_text:'', tooltip:'', sort_order:grp.fields.length});
  dirty(); render(); sel(id, 'field');
}
function delField(sid, gid, fid){
  var sec = state.sections.find(function(s){ return s._id === sid; });
  if(!sec) return;
  var grp = sec.groups.find(function(g){ return g._id === gid; });
  if(!grp) return;
  grp.fields = grp.fields.filter(function(f){ return f._id !== fid; });
  if(state.selectedId === fid){ state.selectedId = null; state.selectedType = null; }
  dirty(); render(); renderInspector();
}

/* ── Selection ── */
function sel(id, type){
  state.selectedId   = id;
  state.selectedType = type;
  document.querySelectorAll('.sb-selected').forEach(function(el){ el.classList.remove('sb-selected'); });
  var el = document.querySelector('[data-id="'+id+'"]');
  if(el) el.classList.add('sb-selected');
  renderInspector();
}

/* ── Render canvas ── */
function render(){
  canvasEl.innerHTML = '';
  if(state.sections.length === 0){
    canvasEl.innerHTML =
      '<div class="sb-empty-state">' +
        '<i class="bi bi-layout-text-window-reverse display-3 text-muted"></i>' +
        '<p class="mt-3 text-muted">No sections yet.<br>Click <strong>Add Section</strong> or drag a field here.</p>' +
      '</div>';
    return;
  }
  state.sections.forEach(function(sec){ canvasEl.appendChild(renderSection(sec)); });
}

function renderSection(sec){
  var el = document.createElement('div');
  el.className = 'sb-section' + (state.selectedId === sec._id ? ' sb-selected' : '');
  el.dataset.id = sec._id;
  el.innerHTML =
    '<div class="sb-section-header">' +
      '<i class="bi bi-grip-vertical sb-drag-handle text-muted me-2"></i>' +
      '<i class="bi bi-layout-text-window-reverse me-2 text-primary"></i>' +
      '<span class="sb-section-title fw-semibold">'+esc(sec.name)+'</span>' +
      '<div class="sb-element-actions ms-auto">' +
        '<button type="button" class="sb-icon-btn" data-a="ag" title="Add Group"><i class="bi bi-plus-square"></i></button>' +
        '<button type="button" class="sb-icon-btn sb-icon-btn-danger" data-a="ds" title="Delete Section"><i class="bi bi-trash3"></i></button>' +
      '</div>' +
    '</div>' +
    '<div class="sb-section-body"></div>' +
    '<div class="sb-section-drop-zone">' +
      '<span class="text-muted small"><i class="bi bi-plus-circle me-1"></i>Drop a field here or click Add Field Group</span>' +
    '</div>';

  el.querySelector('.sb-section-header').addEventListener('click', function(e){
    if(!e.target.closest('[data-a]')) sel(sec._id, 'section');
  });
  el.querySelector('[data-a=ag]').addEventListener('click', function(){ addGroup(sec._id); });
  el.querySelector('[data-a=ds]').addEventListener('click', function(){
    if(confirm('Delete section "'+sec.name+'" and all its contents?')) delSection(sec._id);
  });

  var dz = el.querySelector('.sb-section-drop-zone');
  dz.addEventListener('dragover', function(e){
    if(state.dragPayload && state.dragPayload.source === 'palette'){ e.preventDefault(); dz.classList.add('sb-drag-over'); }
  });
  dz.addEventListener('dragleave', function(){ dz.classList.remove('sb-drag-over'); });
  dz.addEventListener('drop', function(e){
    e.preventDefault(); dz.classList.remove('sb-drag-over');
    var p = state.dragPayload;
    if(!p || p.source !== 'palette') return;
    if(sec.groups.length === 0) addGroup(sec._id);
    var lg = sec.groups[sec.groups.length-1];
    addField(sec._id, lg._id, p.fieldType);
  });

  setupSecDrag(el, sec);

  var body = el.querySelector('.sb-section-body');
  sec.groups.forEach(function(grp){ body.appendChild(renderGroup(sec, grp)); });
  return el;
}

function renderGroup(sec, grp){
  var el = document.createElement('div');
  el.className = 'sb-group' + (state.selectedId === grp._id ? ' sb-selected' : '');
  el.dataset.id = grp._id;
  el.innerHTML =
    '<div class="sb-group-header">' +
      '<i class="bi bi-collection me-2 text-secondary"></i>' +
      '<span class="sb-group-title">'+esc(grp.name)+'</span>' +
      '<div class="sb-element-actions ms-auto">' +
        '<button type="button" class="sb-icon-btn" data-a="af" title="Add Field"><i class="bi bi-plus-circle"></i></button>' +
        '<button type="button" class="sb-icon-btn sb-icon-btn-danger" data-a="dg" title="Delete Group"><i class="bi bi-trash3"></i></button>' +
      '</div>' +
    '</div>' +
    '<div class="sb-group-fields"></div>';

  el.querySelector('.sb-group-header').addEventListener('click', function(e){
    if(!e.target.closest('[data-a]')) sel(grp._id, 'group');
  });
  el.querySelector('[data-a=af]').addEventListener('click', function(){ addField(sec._id, grp._id); });
  el.querySelector('[data-a=dg]').addEventListener('click', function(){
    if(confirm('Delete group "'+grp.name+'"?')) delGroup(sec._id, grp._id);
  });

  var fc = el.querySelector('.sb-group-fields');
  grp.fields.forEach(function(fld){ fc.appendChild(renderField(sec, grp, fld)); });
  fc.addEventListener('dragover', function(e){
    if(state.dragPayload){ e.preventDefault(); e.stopPropagation(); fc.classList.add('sb-group-drop-active'); }
  });
  fc.addEventListener('dragleave', function(){ fc.classList.remove('sb-group-drop-active'); });
  fc.addEventListener('drop', function(e){
    e.preventDefault(); e.stopPropagation(); fc.classList.remove('sb-group-drop-active');
    var p = state.dragPayload;
    if(p && p.source === 'palette') addField(sec._id, grp._id, p.fieldType);
  });
  return el;
}

function renderField(sec, grp, fld){
  var ft = FIELD_TYPES.find(function(f){ return f.type === fld.field_type; }) || {icon:'bi-question-circle', label:fld.field_type};
  var el = document.createElement('div');
  el.className = 'sb-field' + (state.selectedId === fld._id ? ' sb-selected' : '');
  el.dataset.id = fld._id;
  el.draggable   = true;
  el.innerHTML =
    '<i class="bi '+ft.icon+' sb-field-icon"></i>' +
    '<div class="sb-field-info">' +
      '<span class="sb-field-label">'+esc(fld.label)+'</span>' +
      '<span class="sb-field-meta text-muted">'+esc(fld.code)+' \u00B7 '+esc(ft.label)+(fld.required ? ' \u00B7 <span class="text-danger">Required</span>' : '')+'</span>' +
    '</div>' +
    '<div class="sb-element-actions ms-auto">' +
      '<button type="button" class="sb-icon-btn sb-icon-btn-danger" data-a="df" title="Delete Field"><i class="bi bi-trash3"></i></button>' +
    '</div>';

  el.addEventListener('click', function(e){
    if(!e.target.closest('[data-a]')) sel(fld._id, 'field');
  });
  el.querySelector('[data-a=df]').addEventListener('click', function(){ delField(sec._id, grp._id, fld._id); });

  el.addEventListener('dragstart', function(e){
    state.dragPayload = {source:'field', id:fld._id, sid:sec._id, gid:grp._id};
    e.dataTransfer.effectAllowed = 'move';
    e.stopPropagation();
    el.classList.add('sb-dragging');
  });
  el.addEventListener('dragend', function(){ el.classList.remove('sb-dragging'); state.dragPayload = null; });
  el.addEventListener('dragover', function(e){
    if(state.dragPayload){ e.preventDefault(); e.stopPropagation(); el.classList.add('sb-drag-over'); }
  });
  el.addEventListener('dragleave', function(){ el.classList.remove('sb-drag-over'); });
  el.addEventListener('drop', function(e){
    e.preventDefault(); e.stopPropagation(); el.classList.remove('sb-drag-over');
    var p = state.dragPayload;
    if(!p) return;
    if(p.source === 'palette'){ addField(sec._id, grp._id, p.fieldType); return; }
    if(p.source === 'field'){
      var fs = state.sections.find(function(s){ return s._id === p.sid; });
      var fg = fs && fs.groups.find(function(g){ return g._id === p.gid; });
      if(!fg) return;
      var fi = fg.fields.findIndex(function(f){ return f._id === p.id; });
      var mv = fg.fields.splice(fi, 1)[0];
      var ts = state.sections.find(function(s){ return s._id === sec._id; });
      var tg = ts && ts.groups.find(function(g){ return g._id === grp._id; });
      if(!tg) return;
      var ti = tg.fields.findIndex(function(f){ return f._id === fld._id; });
      tg.fields.splice(ti, 0, mv);
      dirty(); render();
    }
  });
  return el;
}

function setupSecDrag(el, sec){
  el.addEventListener('dragstart', function(e){
    if(state.dragPayload && state.dragPayload.source !== 'section') return;
    state.dragPayload = {source:'section', id:sec._id};
    e.dataTransfer.effectAllowed = 'move';
    el.classList.add('sb-dragging');
  });
  el.addEventListener('dragend', function(){ el.classList.remove('sb-dragging'); state.dragPayload = null; });
  el.addEventListener('dragover', function(e){
    if(state.dragPayload && state.dragPayload.source === 'section'){ e.preventDefault(); el.classList.add('sb-drag-over'); }
  });
  el.addEventListener('dragleave', function(){ el.classList.remove('sb-drag-over'); });
  el.addEventListener('drop', function(e){
    e.preventDefault(); el.classList.remove('sb-drag-over');
    var p = state.dragPayload;
    if(!p || p.source !== 'section' || p.id === sec._id) return;
    var fi = state.sections.findIndex(function(s){ return s._id === p.id; });
    var ti = state.sections.findIndex(function(s){ return s._id === sec._id; });
    var mv = state.sections.splice(fi, 1)[0];
    state.sections.splice(ti, 0, mv);
    dirty(); render();
  });
}

/* ── Inspector ── */
function renderInspector(){
  if(!state.selectedId){
    inspectorEl.innerHTML = '<p class="text-muted small px-3 pt-3">Select an element to edit its properties.</p>';
    return;
  }
  if(state.selectedType === 'section'){
    var sec = state.sections.find(function(s){ return s._id === state.selectedId; });
    if(sec) buildSecInsp(sec);
  } else if(state.selectedType === 'group'){
    state.sections.forEach(function(s){
      var g = s.groups.find(function(g){ return g._id === state.selectedId; });
      if(g) buildGrpInsp(s, g);
    });
  } else if(state.selectedType === 'field'){
    state.sections.forEach(function(s){
      s.groups.forEach(function(g){
        var f = g.fields.find(function(f){ return f._id === state.selectedId; });
        if(f) buildFldInsp(s, g, f);
      });
    });
  }
}

function ir(label, id, val, type){
  type = type || 'text';
  return '<div class="sb-prop-row"><label class="sb-prop-label" for="'+id+'">'+label+'</label>' +
         '<input type="'+type+'" id="'+id+'" class="sb-prop-input" value="'+esc(String(val||''))+'"></div>';
}
function ita(label, id, val){
  return '<div class="sb-prop-row"><label class="sb-prop-label" for="'+id+'">'+label+'</label>' +
         '<textarea id="'+id+'" class="sb-prop-input" rows="2">'+esc(String(val||''))+'</textarea></div>';
}
function ic(label, id, chk){
  return '<div class="sb-prop-row sb-prop-row-check">' +
         '<input type="checkbox" id="'+id+'" class="sb-prop-check"'+(chk?' checked':'')+'>' +
         '<label class="sb-prop-label-inline" for="'+id+'">'+label+'</label></div>';
}

function buildSecInsp(sec){
  inspectorEl.innerHTML =
    '<div class="sb-inspector-title"><i class="bi bi-layout-text-window-reverse me-2 text-primary"></i>Section Properties</div>' +
    ir('Name', 'ip-n', sec.name) + ir('Code', 'ip-c', sec.code) +
    ita('Description', 'ip-d', sec.description) + ita('Instructions', 'ip-i', sec.instructions) +
    ic('Repeatable', 'ip-r', sec.is_repeatable) + ic('Collapsible', 'ip-co', sec.is_collapsible);
  b('ip-n',  function(v){ sec.name = v; rt(sec._id, '.sb-section-title', v); });
  b('ip-c',  function(v){ sec.code = v; });
  b('ip-d',  function(v){ sec.description = v; });
  b('ip-i',  function(v){ sec.instructions = v; });
  bc('ip-r',  function(v){ sec.is_repeatable = v; });
  bc('ip-co', function(v){ sec.is_collapsible = v; });
}

function buildGrpInsp(sec, grp){
  void sec;
  inspectorEl.innerHTML =
    '<div class="sb-inspector-title"><i class="bi bi-collection me-2 text-secondary"></i>Field Group Properties</div>' +
    ir('Name', 'ip-n', grp.name) + ir('Code', 'ip-c', grp.code) +
    ita('Description', 'ip-d', grp.description);
  b('ip-n', function(v){ grp.name = v; rt(grp._id, '.sb-group-title', v); });
  b('ip-c', function(v){ grp.code = v; });
  b('ip-d', function(v){ grp.description = v; });
}

function buildFldInsp(sec, grp, fld){
  void sec; void grp;
  var opts = FIELD_TYPES.map(function(ft){
    return '<option value="'+ft.type+'"'+(fld.field_type===ft.type?' selected':'')+'>'+ft.label+'</option>';
  }).join('');
  inspectorEl.innerHTML =
    '<div class="sb-inspector-title"><i class="bi bi-input-cursor-text me-2 text-info"></i>Field Properties</div>' +
    ir('Label', 'ip-l', fld.label) + ir('Code', 'ip-c', fld.code) +
    '<div class="sb-prop-row"><label class="sb-prop-label" for="ip-t">Field Type</label>' +
    '<select id="ip-t" class="sb-prop-select">'+opts+'</select></div>' +
    ir('Placeholder', 'ip-ph', fld.placeholder) + ir('Help Text', 'ip-h', fld.help_text) + ir('Tooltip', 'ip-tt', fld.tooltip) +
    ic('Required', 'ip-req', fld.required) + ic('Read Only', 'ip-ro', fld.read_only) +
    ic('Hidden', 'ip-hd', fld.hidden) + ic('Repeatable', 'ip-rp', fld.is_repeatable) +
    ic('Calculated', 'ip-calc', fld.is_calculated) +
    '<div id="ip-frow" class="sb-prop-row"'+(fld.is_calculated ? '' : ' style="display:none"')+'>' +
    '<label class="sb-prop-label" for="ip-f">Formula</label>' +
    '<input type="text" id="ip-f" class="sb-prop-input" value="'+esc(fld.formula)+'" placeholder="sum([a, b]) * 1.1"></div>';

  b('ip-l',   function(v){ fld.label = v; var el=document.querySelector('[data-id="'+fld._id+'"] .sb-field-label'); if(el) el.textContent=v; });
  b('ip-c',   function(v){ fld.code = v; });
  b('ip-ph',  function(v){ fld.placeholder = v; });
  b('ip-h',   function(v){ fld.help_text = v; });
  b('ip-tt',  function(v){ fld.tooltip = v; });
  b('ip-f',   function(v){ fld.formula = v; });
  bc('ip-req',  function(v){ fld.required = v; });
  bc('ip-ro',   function(v){ fld.read_only = v; });
  bc('ip-hd',   function(v){ fld.hidden = v; });
  bc('ip-rp',   function(v){ fld.is_repeatable = v; });
  bc('ip-calc', function(v){
    fld.is_calculated = v;
    document.getElementById('ip-frow').style.display = v ? '' : 'none';
  });
  var te = document.getElementById('ip-t');
  if(te) te.addEventListener('change', function(){ fld.field_type = te.value; dirty(); render(); sel(fld._id, 'field'); });
}

function b(id, cb){
  var el = document.getElementById(id);
  if(el) el.addEventListener('input', function(){ cb(el.value); dirty(); });
}
function bc(id, cb){
  var el = document.getElementById(id);
  if(el) el.addEventListener('change', function(){ cb(el.checked); dirty(); });
}
function rt(id, selector, val){
  var el = document.querySelector('[data-id="'+id+'"] '+selector);
  if(el) el.textContent = val;
}
function dirty(){
  var ind = document.getElementById('sb-ind');
  if(ind) ind.innerHTML = '<i class="bi bi-circle-fill text-warning me-1"></i>Unsaved changes';
}
function esc(s){
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
