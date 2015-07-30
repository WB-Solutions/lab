
var js_debug = true
function _log() { if (js_debug) { console.log.apply(console, arguments) } }

$(function(){
  _.mixin(_.str.exports()) /* underscore + string. */

  /* note that w_* properties & variables point to jquery widgets/elements. */
  var w_doc = $(document)
  var w_dt = $('#dt')
  var w_dt2 = $('#dt2')
  var w_cal = $('#cal')
  var w_modal = $('#modal')
  var w_form = $('#go-form')
  var w_list = $('#go-list')
  // _log('w_*', w_dt2, w_dt, w_cal, w_modal, w_form, w_list)

  var w_user = $('#go_user')
  var w_visits = $('#go_visits')
  var w_forms = $('#go_forms')
  var w_nodes = $('#go_nodes')

  var w_visit1 = $('#go_visit1')

  var w_loading = $('#go-loading')
  var w_sources = $('#go-sources')
  var w_target = $('#go-target')

  var gotop = function() {
    $('body').scrollTop(0)
  }

  // w_doc.on('click', '#go-cancel', function(){ console.log('go-cancel') })

  var goclose = function() {
    console.log('goclose')
    w_form.empty()
    gotop()
  }

  function modal(z) {
    _log('modal', z)
    var _get = function(k, kn) {
      var kv = z[k]
      return kv ? kn[kv] : undefined
    }
    if (!z) { z = {} }
    var formtype = _get('formtype_id', data.allformtypes)
    var visit = _get('visit_id', data.visits)
    var userform = _get('userform_id', data.allforms)

    w_form.empty()
    w_list.empty()

    function _ids(source) {
      var _v = _(source).chain()
	.sortBy('full')
	.pluck('id')
	.value()
      _log('_ids', _v)
      return _v
    }
    function _obj(source) {
      var _v = {}
      _(source).each(function(each, id){ _v[id] = each.full })
      _log('_obj', _v)
      return _v
    }
    function _sorted(_els) {
      return _(_els).sortBy(function(each){
	return [ each.order, each.name ]
      })
    }
    var vjson = {}
    var refvars = {}
    var rec, zforms, zrepitems, zrepusercats, label

    function _forms(ids) {
      return _(ids).chain()
	.collect(function(each){ return data.allforms[each] })
	.compact() // compact to handle not found.
	.value()
    }

    var err
    var jschema = {}
    var jitems = []
    var selformtype = false
    var fieldsets = []
    var fieldsets2 = []

    if (visit) {
      if (userform) { err = 'BOTH' }
      _(vjson).extend(visit)
      _(refvars).extend({
	ref_visit: visit.id
      })
      rec = visit.rec
      zforms = visit.forms
      zrepitems = visit.repdict_items
      zrepusercats = visit.repdict_usercats
      label = 'Visit'
      _(jschema).extend({
	datetime: { type: 'string' },
	user_name: { type: 'string' },
	user_email: { type: 'string' },
	user_cats: { type: 'string' },
	loc_name: { type: 'string' },
	loc_address: { type: 'string' }
      })
      jitems.push(
	{ key: 'datetime', prepend: 'Date/Time', notitle: true, disabled: true },
	{ key: 'user_name', prepend: 'User', notitle: true, disabled: true },
	{ key: 'user_email', prepend: 'Email', notitle: true, disabled: true },
	{ key: 'user_cats', prepend: 'Categories', notitle: true, disabled: true },
	{ key: 'loc_name', prepend: 'Location', notitle: true, disabled: true },
	{ key: 'loc_address', prepend: 'Address', notitle: true, disabled: true }
      )
    }
    else if (userform) {
      _(refvars).extend({
	ref_user: data.user.id,
	ref_form: userform.id
      })
      zrec = data.user.recs[userform.id]
      rec = zrec ? zrec.rec : {}
      _(vjson).extend({
	rec: rec,
	observations: zrec ? zrec.observations : ''
      })
      var formid = userform.id
      var _zreps = function(nreps) {
	nreps = nreps[formid]
	return _(nreps).chain()
	  .collect(function(e){ return [ e, [formid] ] })
	  .object()
	  .value()
      }
      zrepitems = _zreps(data.user.repdict_items)
      zrepusercats = zrepitems.length ? [] : _zreps(data.user.repdict_usercats)
      zforms = _(zrepitems).size() || _(zrepusercats).size() ? [] : [formid]
      label = 'Form'
    }
    else { err = 'NO' }
    if (err) { return alert(_('Error @ modal : %s visit / userform').sprintf(err)) }
    // _log('modal', z, vjson)
    _log('zforms', zforms, 'zrepitems', zrepitems, 'zrepusercats', zrepusercats)

    if (!formtype) {
      var _zids = function(zreps) {
	return _(zreps).chain()
	  .values()
	  .flatten()
	  .value()
      }
      var allformids = zforms.concat(_zids(zrepitems)).concat(_zids(zrepusercats))
      _log('allformids', allformids)
      var nforms = _forms(allformids)
      var formtypes = _sorted(_(nforms).chain()
	.collect(function(eform){ return eform.types })
	.flatten()
	.uniq()
	.collect(function(eid){ return data.allformtypes[eid] })
	.compact() // compact to handle not found.
	.value())
      _log('formtypes', nforms, formtypes.length, formtypes)

      selformtype = formtypes.length > 1

      if (selformtype) {
	var wlist = $('<div class="list-group">')
	_(formtypes).each(function(eformtype){
	  // _log('eformtype', eformtype.name, eformtype.description)
	  var w1 = $('<a href="#" class="list-group-item">')
	  w1.click(function(ev){
	    // _log('click @ eformtype', eformtype)
	    ev.preventDefault()
	    setTimeout(function(){
	      // _log('setTimeout @ eformtype', eformtype)
	      modal(_({}).extend(z, { formtype_id: eformtype.id }))
	    }, 10)
	    return false
	  })
	  var wname = $('<h4 class="list-group-item-heading">')
	  wname.append(eformtype.name)
	  var wdesc = $('<p class="list-group-item-text">')
	  wdesc.append(eformtype.description)
	  w1.append(wname, wdesc)
	  wlist.append(w1)
	})
	w_list.append(wlist)
      }
    }
    _log('selformtype', selformtype, 'visit', visit)


    if (visit) {
      _(jschema).extend({
	accompanied: { type: 'boolean' },
	name: { type: 'string' },
	status: { type: 'string', enum: [ 's', 'v', 'n', 'r' ] },

	f_contact: { type: 'string', enum: [ 'Presencial', 'Telefonica', 'Web' ] },
	f_goal: { type: 'string', enum: [ 'Presentacion Inicial', 'Promocion', 'Pedido', 'Negociar' ] },
	f_option: { type: 'string', enum: [ 'Planeada', 'Re-agendada', 'Asignada' ] }
      })
      var readonly = selformtype
      jitems.push(
	{ key: 'accompanied', prepend: 'Accompanied', inlinetitle: 'Accompanied', htmlClass: 'lab-field-boolean', disabled: readonly },
	{ key: 'name', prepend: 'Name', notitle: true, disabled: readonly },
	{ key: 'status', prepend: 'Status', notitle: true, titleMap: { "s": 'Scheduled', "v": 'Visited', "n": 'Negative', "r": 'Re-scheduled' }, disabled: readonly },

	{ key: 'f_contact', prepend: 'Contact', notitle: true, disabled: readonly },
	{ key: 'f_goal', prepend: 'Goal', notitle: true, disabled: readonly },
	{ key: 'f_option', prepend: 'Option', notitle: true, disabled: readonly }
      )
    }


    if (selformtype) {
    }
    else {
      var _filter_formtype = function(v1) {
	var v2 = v1
	if (formtype) {
	  v2 = _(v1).select(function(e){
	    // those with empty types will apply !
	    return !e.types || !e.types.length || _(e.types).contains(formtype.id)
	  })
	}
	// _log('_filter_formtype', v1, formtype, v2)
	return v2
      }

      var schema2 = {}

      function _do_fields(fields, pre_id) {
	// _log('_do_fields', fields)
	return _(_sorted(fields)).collect(function(field){
	  var key = pre_id + 'field:' + field.id // _('field_%s').sprintf(k)
	  if (!(key in rec)) { rec[key] = field.default }
	  var ftype = field.type
	  var fwidget = field.widget
	  var desc = field.description
	  var req = field.required
	  var f_schema = {}
	  var f_form = {}
	  var isbool = ftype == 'boolean'
	  var ftype2 = 'string'
	  var fwidget2 = ''
	  if (ftype == 'string') {
	    if (fwidget == 'textarea') {
	      ftype2 = fwidget
	      fwidget2 = fwidget
	    }
	  }
	  else if (ftype == 'date') {
	    ftype2 = ftype
	  }
	  else if (isbool) {
	    f_form['inlinetitle'] = desc
	    ftype2 = ftype
	  }
	  else if (_(ftype).startsWith('opts')) {
	    ftype = 'opts'
	    var opts = field.opts
	    if (!opts || !opts.length) { opts = [ ['','x'] ] }
	    var enums = [] // respect order.
	    var opts = _(opts).collect(function(opt){
	      var opt2 = opt.length == 2 ? opt : [ opt[0], opt[0] ]
	      enums.push(opt2[0])
	      return opt2
	    })
	    // _log('modal > each opts', opts)
	    f_form['titleMap'] = _(opts).object()
	    f_schema['enum'] = enums
	    if (fwidget == 'radios') {
	      f_form['type'] = fwidget
	      fwidget2 = fwidget
	    }
	  }
	  _(f_schema).extend({
	    type: ftype2,
	    description: isbool ? null : desc,
	    required: req
	  })
	  _(f_form).extend({
	    key: _('rec.%s').sprintf(key),
	    prepend: field.name,
	    notitle: true,
	    // https://github.com/joshfire/jsonform/issues/63
	    // such that empty/blank fields are included in the submit values, otherwise form fields could NOT be emptied.
	    allowEmpty: !req,
	    htmlClass: _('lab-field-%s%s%s').sprintf(ftype, fwidget2 ? '-' : '', fwidget2)
	  })
	  schema2[key] = f_schema
	  return f_form
	})
      }

      function _do_fieldset(forms_ids, erep, erepid) {
	// _log('_do_fieldset', forms_ids, erep, erepid)
	var forms = _filter_formtype(_forms(forms_ids))
	var fields = _(forms).chain()
	  .collect(function(eform){ return _(eform.fields).values() })
	  .flatten()
	  .value()
	// _log('_do_fieldset > fields', forms, fields)
	if (!fields.length) { return }
	fields = _filter_formtype(fields)
	var source = erep || forms[0]
	var f_fields = _do_fields(fields, erepid ? erepid + erep.id + '_' : '')
	var desc = source.description
	if (desc) { f_fields = [ { type: 'help', helpvalue: desc } ].concat(f_fields) }
	fset = {
	  type: 'fieldset',
	  title: source.name,
	  expandable: source.expandable,
	  items: f_fields
	}
	fieldsets.push(fset)
      }
      _(zforms).each(function(form_id){
	_do_fieldset([form_id])
      })

      _([
	{ zreps: zrepitems, alls: data.allitems, zid: 'item:' },
	{ zreps: zrepusercats, alls: data.allusercats, zid: 'usercat:' }
      ]).each(function(ez){
	var nreps = _sorted(_(ez.zreps).chain()
	  .keys()
	  .collect(function(item_id){ return ez.alls[item_id] })
	  .compact() // compact to handle not found.
	  .value())
	_(nreps).each(function(erep){
	  _do_fieldset(ez.zreps[erep.id], erep, ez.zid)
	})
      })

      _(jschema).extend({
	observations: { type: 'string' },
	rec: {
	  type: 'object',
	  title: 'Forms',
	  properties: schema2,
	},
      })
      fieldsets2.push(
	{
	  type: 'fieldset',
	  title: 'Observations',
	  items: [
	    { key: 'observations', type: 'textarea' },
	  ],
	},
	{ type: 'submit', title: _('Save %s').sprintf(label), id: 'go-save', htmlClass: 'btn-success X-center-block' },
	{
	  type: 'button', title: 'Cancel', id: 'go-cancel', htmlClass: 'btn-default btn-sm X-pull-right',
	  onClick: function(ev) {
	    ev.preventDefault()
	    goclose()
	  }
        }
	// isnew ? '' : { type: 'button', title: 'Delete', id: 'X-delete', htmlClass: 'btn-danger btn-xs pull-right' }
      )
    }

    w_form.toggleClass('form-user', Boolean(userform && !selformtype))

    _log('jschema', jschema, 'jitems', jitems, 'fieldsets', fieldsets, 'fieldsets2', fieldsets2)
    // _log('modal > vjson', vjson)

    w_form.jsonForm({
      schema: jschema,
      form: [
	{
	  type: 'section', // fieldset
	  title: label,
	  items: jitems,
	},
      ].concat(fieldsets).concat(fieldsets2),
      value: vjson,
      onSubmitValid: function(vals){ // https://github.com/joshfire/jsonform/wiki#wiki-submission-values
	if (selformtype) { return alert('Save NOT allowed if selformtype !!') }
	var postvars = _({}).extend(refvars, vals)
	_log('onSubmitValid', postvars)
	$.ajax({
	  url: '/lab/ajax' + location.search, // "private" param.
	  data: { data: JSON.stringify(postvars) },
	  type: 'post',
	  dataType: 'json',
	  complete: function(xhr, text_status){
	    var data2 = xhr.responseJSON
	    _log('ajax COMPLETE', text_status, data2)
	    if (data2 && data2.error) { return alert(data2.error) } // regardless of status.
	    if (xhr.status != 200) {
	      _log('ajax ERROR', xhr)
	      return alert('Error communicating to the server, please try again. If the error persists, please contact x@x.com.')
	    }
	    if (!data2) { return alert('Ajax success, but NO data returned, please try again.') }
	    /*
	    _(data2.data).each(function(each, k){ _(data[k]).extend(each) })
	    data_set()
	    */
	    var visit2 = data2.visit
	    var rec2 = data2.rec
	    if (visit) {
	      if (rec2) { return alert('Error @ visit, unexpected rec2.') }
	      if (visit2.id != visit.id) { return alert('Error @ visit, invalid id.') }
	      _(visit).extend(visit2)
	      var calevs = w_cal.fullCalendar('clientEvents', visit.id)
	      if (calevs.length != 1) { return alert('Error @ visit, calev not found.') }
	      var calev = calevs[0]
	      // _log('calev', calev)
	      var ev2 = _visit_prep(visit2)
	      _(calev).extend(ev2)
	      var wtr = $('#' + _visit_row(visit))
	      // _log('wtr', wtr)
	      var row = api.row(wtr)
	      if (row.length) { row.data(visit2) } // replace.
	      else { row = api.row.add(visit2) } // add.
	      api.draw()
	      w_cal.fullCalendar('updateEvent', calev)
	      // visit_edit(visit2.id)
	    }
	    else { // userform.
	      if (visit2) { return alert('Error @ userform, unexpected visit2.') }
	      data.user.recs[userform.id] = rec2
	    }
	    // w_modal.modal('hide')
	    goclose()
	  }
	})
      },
    })

    // w_form.find('.tabbable:last').before('<label class="control-label">Forms</label>')
    // w_modal.find('#modal-label').text('Medical Visit')

    // w_modal.modal('show')
    gotop()
  }

  function visit_edit(visit_id) {
    modal({ visit_id: visit_id })
/*
    var _p = function(label, value, wel) {
      return _('<p> <mark>%s:</mark> %s </p>').sprintf(label, value)
    }
    var ftypes = visit.formtypes
    var hsel
    if (ftypes.length) {
      _(ftypes).each(function(e){
	var hopt = _('<option value="%s"> %s </option>').sprintf(e.id, e.name)
	hsel += hopt
      })
      hsel = '<select id="formtype"><option/>' + hsel + '</select>'
    }
    var hn = [
      _p('Name', visit.name),
      _p('Status', visit.status),
      _p('User', visit.h_user),
      _p('Cats', visit.h_cats),
      _p('Loc', visit.h_loc),
      _p('Contact', visit.f_contact),
      _p('Goal', visit.f_goal),
      _p('Option', visit.f_option),
      _p('Observations', visit.observations),
      hsel ? _p('Type', hsel) : '',
    ]
    var h = hn.join('')
    var wbutton = $('<p><button class="btn btn-info">Visit</button></p>')
    wbutton.click(function(){
      var ftype = $('#formtype').val()
      modal({ visit: visit, formtype_id: ftype })
    })
    w_visit1.empty().append(h, wbutton)
*/
  }

  function userform_edit(form_id) {
    modal({ userform_id: form_id })
  }

  function _onclick(sel, fn) {
    w_doc.on('click', sel, function(){
      var w_act = $(this)
      var xid = w_act.data('ref')
      // _log('click', sel, w_act, xid)
      fn(xid)
    })
  }

  _onclick('.visit-edit', visit_edit)
  _onclick('.userform-edit', userform_edit)

  w_dt2.dataTable({
    columns: [
      { title: 'Form', data: 'acts' },
      { title: 'Name', data: 'name' },
      { title: 'Items', data: 'repitems' },
      { title: 'Cats', data: 'repusercats' }
    ],
    data: [],
  })
  var api2 = w_dt2.api()

  w_dt.dataTable({
    // paging: false,
    // filter: false,
    // info: false,
    columns: [
      { title: 'Visit', data: 'acts' },
      { title: 'Date/Time', data: 'datetime' },
      { title: 'User', data: 'h_user' },
      { title: 'Categories', data: 'h_cats' },
      { title: 'Address', data: 'h_loc' },
    ],
    data: [],
  })
  var api = w_dt.api()

  w_cal.fullCalendar({
    header: {
      left: 'prev,next today', // prevYear,X,nextYear
      center: 'title',
      right: 'month,agendaWeek,agendaDay', // ,basicWeek,basicDay
    },
    selectable: false,
    selectHelper: false,
    /*
    select: function(start, end, allDay, ev, view) {
      _log('cal.select')
      modal({ sched: start })
    },
    dayClick: null, // otherwise it will trigger "select" again.
    editable: true, // draggable & resizable events.
    eventDrop: function(calev, dayDelta, minuteDelta, allDay, revertFunc, ev, ui, view) { _log('cal.eventDrop') },
    eventResize: function(calev, dayDelta, minuteDelta, revertFunc, ev, ui, view) { _log('cal.eventResize') },
    */
    eventClick: function(calev, ev, view) {
      // _log('cal.eventClick', calev)
      visit_edit(calev.id)
    },
    events: [],
  })

  function _button(ref, cls_button, cls_service, label) {
    return _('<p><button class="btn btn-%s btn-sm %s" data-ref="%s">%s</button></p>').sprintf(cls_button, cls_service, ref, label)
  }

  function _visit_row(visit) {
    return _('visit_%s').sprintf(visit.id)
  }

  function _visit_prep(visit) {
    // _log('_visit_prep', visit)
    function _h2(h1, h2) {
      return _('%s <br> %s').sprintf(h1 || '-', h2 || '-')
    }
    var s = visit.status
    function _stat(v_def, v_v, v_r, v_n) {
      return s == 'v' ? v_v : (s == 'r' ? v_r : (s == 'n' ? v_n : v_def))
    }
    _(visit).extend({
      DT_RowId: _visit_row(visit), // http://next.datatables.net/examples/server_side/ids.html
      acts: _h2(visit.name, _button(visit.id, _stat('primary', 'success', 'warning', 'danger'), 'visit-edit', 'Visit')),
      h_user: _h2(visit.user_name, _('<a href="mailto:%(email)s"> %(email)s </a>').sprintf({ email: visit.user_email })),
      h_cats: visit.user_cats || '-',
      h_loc: _h2(visit.loc_name, visit.loc_address),
    })
    var ev = {
      id: visit.id,
      allDay: false,
      start: visit.datetime,
      end: visit.end,
      title: visit.user_name,
      color: _stat('#357ebd', '#4cae4c', '#eea236', '#d43f3a'),
    }
    // _log('ev @ _visit_prep', visit, ev)
    return ev
  }

  function _count(coll) {
    return _(coll).keys().length
  }

  function w_count(w, total) {
    w.html(_('%s').sprintf(total))
  }

  function data_set() {
    _log('data_set', data)

    var user = data.user
    var userforms = []

    if (user) {
      function _form(formid, repkey, reps, alls) {
	var form = data.allforms[formid]
	var repobj = {
	  name: _('%s <br> <i> %s </i>').sprintf(form.name, form.description),
	  acts: _button(formid, 'primary', 'userform-edit', 'Form'),
	  repitems: '',
	  repusercats: ''
	}
	repobj[repkey] = _('<ul> %s </ul>').sprintf(_(reps).collect(function(repid){
	  return _('<li> %s </li>').sprintf(alls[repid].name)
	}).join(''))
	return repobj
      }
      _(user.forms).each(function(formid){
	userforms.push(_form(formid))
      })
      _(user.repdict_items).each(function(repitems, formid){
	userforms.push(_form(formid, 'repitems', repitems, data.allitems))
      })
      _(user.repdict_usercats).each(function(repusercats, formid){
	userforms.push(_form(formid, 'repusercats', repusercats, data.allusercats))
      })
      // _log('userforms', userforms)
    }

    w_count(w_forms, userforms.length)

    api2.clear()
    api2.rows.add(userforms)
    api2.draw()

    var visits = _(data.visits).values()
    var events = _(visits).collect(function(visit){
      return _visit_prep(visit)
    })

    api.clear()
    api.rows.add(visits)
    api.draw()

    w_cal
      .fullCalendar('removeEvents')
      .fullCalendar('addEventSource', events)
      .fullCalendar('refetchEvents')

    w_user.html(user ? user.name : 'X')
    w_count(w_visits, _count(data.visits))
    var wn = $('<ul></ul>')
    _(data.nodes).each(function(node){
      wn.append(_('<li> %s </li>').sprintf(node.name))
    })
    w_nodes.append(wn)

    w_loading.hide()

    var params = _(location.search.split("?")[1].split("&")).chain()
      .collect(function(e){ return e.split('=') })
      .object()
      .value()

    if (params.visit) {
      $('#go-target').attr('class', 'col-xs-12')
      modal({ visit_id: params.visit, formtype_id: params.formtype })
    }
    else {
      w_sources.show()
      $('#cal').fullCalendar('render')
    }
  }

  if (data) { data_set() }
})
