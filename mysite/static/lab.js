
var js_debug = true
function _log() { if (js_debug) { console.log.apply(console, arguments) } }

$(function(){
  _.mixin(_.str.exports()) /* underscore + string. */

  /* note that w_* properties & variables point to jquery widgets/elements. */
  var w_doc = $(document)
  var w_dt = $('#dt')
  var w_cal = $('#cal')
  var w_modal = $('#modal')
  var w_form = $('#modal-form')
  // _log('w_*', w_dt, w_cal, w_modal, w_form)

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
	var vjson = _({}).extend(visit)
	var refvars = { ref_visit: visit.id }
	var forms = data.forms
	// _log('modal', z, vjson)
	var rec = visit.rec
	var schema2 = {}
	var fieldsets = _(_(visit.forms).collect(function(form_id){
	  var form = data.forms[form_id]
	  if (!form) { return } // removed via compact.
	  return {
		type: 'fieldset',
		title: form.name,
		// expandable: true,
		items: _(form.fields).collect(function(field){
		  var key = field.id // _('field_%s').sprintf(k)
		  if (!(key in rec)) { rec[key] = field.default }
		  var f_schema = { type: 'string', required: field.required }
		  var f_form = { key: _('rec.%s').sprintf(key), prepend: field.name, notitle: true }
		  if (field.opts.length) {
			var enums = [] // respect order.
			var opts = _(field.opts).collect(function(opt){
			  var opt2 = opt.length == 2 ? opt : [ opt[0], opt[0] ]
			  enums.push(opt2[0])
			  return opt2
			})
			// _log('modal > each opts', opts)
			f_form['titleMap'] = _(opts).object()
			f_schema['enum'] = enums
		  }
		  schema2[key] = f_schema
		  return f_form
		}),
	  }
	})).compact()
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
		status: { type: 'string', enum: [ '', 'v', 'n', 'r' ] },
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
		  type: 'fieldset',
		  title: 'Visit',
		  items: [
			{ key: 'status', prepend: 'Status', notitle: true, titleMap: { "": 'Scheduled', "v": 'Visited', "n": 'Negative', "r": 'Re-scheduled' } },
			{ key: 'datetime', prepend: 'Date/Time', notitle: true, disabled: true },
			{ key: 'user_name', prepend: 'User', notitle: true, disabled: true },
			{ key: 'user_email', prepend: 'Email', notitle: true, disabled: true },
			{ key: 'user_cats', prepend: 'Categories', notitle: true, disabled: true },
			{ key: 'loc_name', prepend: 'Location', notitle: true, disabled: true },
			{ key: 'loc_address', prepend: 'Address', notitle: true, disabled: true },
			{ key: 'accompanied', inlinetitle: 'Accompanied' },
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

  w_doc.on('click', '.visit-edit', function(){
	var w_act = $(this)
	var visit_id = w_act.data('ref')
	// _log('click @ visit-edit', w_act, visit_id)
	visit_edit(visit_id)
  })

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

  function data_set() {
	_log('data_set', data)

	var visits = _(data.visits).values()
	var events = _(visits).collect(function(visit){ return _visit_prep(visit) })

	api.clear()
	api.rows.add(visits)
	api.draw()

	w_cal
	  .fullCalendar('removeEvents')
	  .fullCalendar('addEventSource', events)
	  .fullCalendar('refetchEvents')
  }

  if (data) { data_set() }
})
