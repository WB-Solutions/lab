
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
  var w_form = $('#modal-form')
  // _log('w_*', w_dt2, w_dt, w_cal, w_modal, w_form)

  var w_user = $('#go_user')
  var w_visits = $('#go_visits')
  var w_forms = $('#go_forms')
  var w_nodes = $('#go_nodes')

  function modal(z) {
	if (!z) { z = {} }
	var visit = z.visit
	if (!visit) { return alert('Error @ modal, NO visit') }
	_log('modal', visit)
	function _ids(source) {
	  var _v = _(_(source).sortBy('full')).pluck('id')
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
	var vjson = _({}).extend(visit)
	var refvars = { ref_visit: visit.id }
	// _log('modal', z, vjson)

	var rec = visit.rec
	var schema2 = {}
	function _do_fields(fields, pre_id) {
	  // _log('_do_fields', fields)
	  return _(_sorted(fields)).collect(function(field){
		var key = pre_id + field.id // _('field_%s').sprintf(k)
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

	var fieldsets = []
	function _do_fieldset(forms_ids, item) {
	  var forms = _(_(forms_ids).collect(function(each){
		return data.allforms[each]
	  })).compact() // compact to handle not found.
	  var fields = _(_(forms).collect(function(form){
		return _(form.fields).values()
	  })).flatten()
	  // _log('modal > fields', forms, fields)
	  if (!fields.length) { return }
	  var source = item || forms[0]
	  var f_fields = _do_fields(fields, item ? item.id + '_' : '')
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
	_(visit.forms).each(function(form_id){
	  _do_fieldset([form_id])
	})

	var reps = visit.repforms
	var repitems = _(_sorted(_(_(reps).keys()).collect(function(item_id){
	  return data.allitems[item_id]
	}))).compact() // compact to handle not found.
	// _log('repitems', repitems)
	_(repitems).each(function(item){
	  _do_fieldset(reps[item.id], item)
	})

	// _log('modal > vjson', vjson)
	// _log('modal > schema2 / fieldsets', schema2, fieldsets)
	w_form.empty().jsonForm({
	  schema: {
		datetime: { type: 'string' },
		user_name: { type: 'string' },
		user_email: { type: 'string' },
		user_cats: { type: 'string' },
		loc_name: { type: 'string' },
		loc_address: { type: 'string' },
		status: { type: 'string', enum: [ 's', 'v', 'n', 'r' ] },
		accompanied: { type: 'boolean' },
		observations: { type: 'string' },
		rec: {
		  type: 'object',
		  title: 'Forms',
		  properties: schema2,
		},
	  },
	  form: [
		{
		  type: 'section', // fieldset
		  title: 'Visit',
		  items: [
			{ key: 'status', prepend: 'Status', notitle: true, titleMap: { "s": 'Scheduled', "v": 'Visited', "n": 'Negative', "r": 'Re-scheduled' } },
			{ key: 'datetime', prepend: 'Date/Time', notitle: true, disabled: true },
			{ key: 'user_name', prepend: 'User', notitle: true, disabled: true },
			{ key: 'user_email', prepend: 'Email', notitle: true, disabled: true },
			{ key: 'user_cats', prepend: 'Categories', notitle: true, disabled: true },
			{ key: 'loc_name', prepend: 'Location', notitle: true, disabled: true },
			{ key: 'loc_address', prepend: 'Address', notitle: true, disabled: true },
			{ key: 'accompanied', prepend: 'Accompanied', inlinetitle: 'Accompanied', htmlClass: 'lab-field-boolean' },
		  ],
		},
	  ].concat(fieldsets).concat([
		{
		  type: 'fieldset',
		  title: 'Observations',
		  items: [
			{ key: 'observations', type: 'textarea' },
		  ],
		},
		{ type: 'submit', title: 'Save Visit', htmlClass: 'btn-success center-block' },
		// isnew ? '' : { type: 'button', title: 'Delete', id: 'X-delete', htmlClass: 'btn-danger btn-xs pull-right' }
	  ]),
	  value: vjson,
	  onSubmitValid: function(vals){ // https://github.com/joshfire/jsonform/wiki#wiki-submission-values
		var postvars = _({}).extend(refvars, vals)
		_log('onSubmitValid', postvars)
		$.ajax({
		  url: '/lab/ajax',
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
			if (visit2.id != visit.id) { return alert('Error @ id') }
			_(visit).extend(visit2)
			var calevs = w_cal.fullCalendar('clientEvents', visit.id)
			if (calevs.length != 1) { return alert('Error @ calev') }
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
			w_modal.modal('hide')
		  }
		})
	  },
	})
	// w_form.find('.tabbable:last').before('<label class="control-label">Forms</label>')
	// w_modal.find('#modal-label').text('Medical Visit')
	w_modal.modal('show')
  }

  function visit_edit(visit_id) {
	var visit = data.visits[visit_id]
	// _log('visit_edit', visit_id, visit)
	modal({ visit: visit })
  }

  function userform_edit(form_id) {
	var form = data.forms[form_id]
	_log('userform_edit', form_id, form)
	modal({ form: form })
  }

  function _onclick(sel, fn) {
	w_doc.on('click', sel, function(){
	  var w_act = $(this)
	  var xid = w_act.data('ref')
	  _log('click', sel, w_act, xid)
	  fn(xid)
	})
  }

  _onclick('.visit-edit', visit_edit)
  _onclick('.userform-edit', userform_edit)

  w_dt2.dataTable({
    columns: [
	  { title: 'Form', data: 'acts' },
	  { title: 'Name', data: 'name' },
	  { title: 'Items', data: 'items' },
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
	  acts: _button(visit.id, _stat('primary', 'success', 'warning', 'danger'), 'visit-edit', 'Visit'),
	  h_user: _h2(visit.user_name, _('<a href="mailto:%(email)s"> %(email)s </a>').sprintf({ email: visit.user_email })),
	  h_cats: _h2(visit.user_cats),
	  h_loc: _h2(visit.loc_name, visit.loc_address),
	})
	var ev = {
	  id: visit.id,
	  allDay: false,
	  start: visit.datetime,
	  title: visit.user_name,
	  color: _stat('#357ebd', '#4cae4c', '#eea236', '#d43f3a'),
	}
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
	  function _form(formid, repitems) {
		return {
		  name: 'name here',
		  items: _('<ul> %s </ul>').sprintf(_(repitems).collect(function(itemid){
			return _('<li> %s </li>').sprintf(data.allitems[itemid].name)
		  }).join('')),
		  acts: _button(formid, 'primary', 'userform-edit', 'Form'),
		}
	  }
	  _(user.forms).each(function(formid){
		userforms.push(_form(formid))
	  })
	  _(user.repforms).each(function(repitems, formid){
		userforms.push(_form(formid, repitems))
	  })
	  _log('userforms', userforms)
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
  }

  if (data) { data_set() }
})
