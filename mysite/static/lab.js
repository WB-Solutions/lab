
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
  _log('w_*', w_dt, w_cal, w_modal, w_form)

  function modal(z) {
	if (!z) { z = {} }
	var visit = z.visit
	if (!visit) { return alert('Error @ modal, NO visit') }
	// _log('modal', visit)
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
	var refvars = {}
	var forms = data.forms
	_log('modal', z, vjson)
	var schema2 = {}
	var fieldsets = _(visit.forms).collect(function(form_id){
	  var form = data.forms[form_id]
	  return {
		type: 'fieldset',
		title: form.name,
		// expandable: true,
		items: _(form.fields).collect(function(field){
		  var key = _('field_%s').sprintf(field.id)
		  schema2[key] = { type: 'string' }
		  return { key: key, prepend: field.name, notitle: true }
		}),
	  }
	})
	_log('modal forms', schema2, fieldsets)
	w_form.empty().jsonForm({
	  schema: _({
		datetime: { type: 'string' },
		doc_name: { type: 'string' },
		doc_email: { type: 'string' },
		doc_cats: { type: 'string' },
		doc_specialties: { type: 'string' },
		loc_name: { type: 'string' },
		loc_address: { type: 'string' },
		observations: { type: 'string' },
	  }).extend(schema2),
	  form: [
		{
		  type: 'fieldset',
		  title: 'Visit',
		  items: [
			{ key: 'datetime', prepend: 'Date/Time', notitle: true },
			{ key: 'doc_name', prepend: 'Doctor', notitle: true },
			{ key: 'doc_email', prepend: 'Email', notitle: true },
			{ key: 'doc_cats', prepend: 'Categories', notitle: true },
			{ key: 'doc_specialties', prepend: 'Specialties', notitle: true },
			{ key: 'loc_name', prepend: 'Location', notitle: true },
			{ key: 'loc_address', prepend: 'Address', notitle: true },
			{ key: 'observations', prepend: 'Observations', notitle: true },
		  ],
		},
	  ].concat(fieldsets).concat([
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
			_(data2.data).each(function(each, k){
			  _(data[k]).extend(each)
			})
			data_set()
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
	_log('visit_edit', visit_id, visit)
	modal({ visit: visit })
  }

  w_doc.on('click', '.visit-edit', function(){
	var w_act = $(this)
	var visit_id = w_act.data('ref')
	_log('click @ visit-edit', w_act, visit_id)
	visit_edit(visit_id)
  })

  function _button(cls_button, cls_service, ref, label) {
	return _('<p><button class="btn btn-%s btn-sm %s" data-ref="%s">%s</button></p>').sprintf(cls_button, cls_service, ref, label)
  }

  w_dt.dataTable({
    // paging: false,
    // filter: false,
    // info: false,
    columns: [
	  { title: 'Visit', data: 'acts' },
	  { title: 'Date/Time', data: 'datetime' },
	  { title: 'Doctor', data: 'h_doc' },
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
	select: function(start, end, allDay, ev, view) {
	  _log('cal.select')
	  modal({ sched: start })
	},
	dayClick: null, // otherwise it will trigger "select" again.
	// editable: true, // draggable & resizable events.
	// eventDrop: function(calev, dayDelta, minuteDelta, allDay, revertFunc, ev, ui, view) { _log('cal.eventDrop') },
	// eventResize: function(calev, dayDelta, minuteDelta, revertFunc, ev, ui, view) { _log('cal.eventResize') },
	eventClick: function(calev, ev, view) {
	  _log('cal.eventClick')
	  visit_edit(calev.id)
	},
	events: [],
  })

  function data_set() {
	_log('data_set', data)

	var events = _(_(data.visits)).collect(function(visit, id){
	  return { id: visit.id, allDay: false, start: visit.datetime, title: visit.doc_name }
	})

	var visits = _(data.visits).values()

	function _h2(h1, h2) {
	  return _('%s <br> %s').sprintf(h1 || '-', h2 || '-')
	}

	_(visits).each(function(visit){
	  _(visit).extend({
		acts: _button('primary', 'visit-edit', visit.id, 'Visit'),
		h_doc: _h2(visit.doc_name, _('<a href="mailto:%(email)s"> %(email)s </a>').sprintf({ email: visit.doc_email })),
		h_cats: _h2(visit.doc_cats, visit.doc_specialties),
		h_loc: _h2(visit.loc_name, visit.loc_address),
	  })
	})

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
