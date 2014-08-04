
var js_debug = false
function _log() { if (js_debug) { console.log(arguments) } }

$(function(){
  _.mixin(_.str.exports()) /* underscore + string. */

  /* note that w_* properties & variables point to jquery widgets/elements. */
  var w_doc = $(document)
  var w_dt = $('#dt')
  var w_cal = $('#cal')
  var w_modal = $('#service-modal')
  var w_form = $('#service-form')
  // _log('w_*', w_dt, w_cal, w_modal, w_form)

  function modal(z) {
	if (!z) { z = {} }
	var service = z.service
	var isnew = !service
	var car = isnew ? z.car : data.cars[service.car]
	function _ids(source) {
	  var _v = _(_(source).sortBy('full')).pluck('id')
	  // _log('_ids', _v)
	  return _v
	}
	function _obj(source) {
	  var _v = {}
	  _(source).each(function(each, id){ _v[id] = each.full })
	  // _log('_obj', _v)
	  return _v
	}
	var vjson = {}
	var refvars = {}
	var title = 'Create Owner & Car & Service'
	if (z.owner_id) {
	  title = 'Create Car & Service for Owner'
	  refvars.ref_owner = z.owner_id
	  _(vjson).extend({
		car_owner: z.owner_id,
	  })
	}
	if (z.sched) {
	  _(vjson).extend({
		sched: $.fullCalendar.formatDate(z.sched, "yyyy-MM-dd HH:mm"),
	  })
	}
	var tasks = _(data.tasks).clone()
	if (car) {
	  if (!service) {
		title = 'Create Service for Car'
		refvars.ref_car = car.id
	  }
	  _(vjson).extend({
		car: car.id,
		// car_owner: car.owner,
		// car_model: car.model,
		// car_year: car.year,
		// car_plate: car.plate,
	  })
	  var engine = data.models[car.model].engine
	  _(tasks).each(function(task, id){ // filter engine-compatible tasks.
		if (!_(task.engines).include(engine)) {
		  // _log('delete task', id)
		  delete tasks[id]
		}
	  })
	  // _log('tasks', engine, tasks)
	}
	else {
	  _(vjson).defaults({
		car_year: 2014,
	  })
	  // pending to filter engine-compatible tasks based on the user-selected model.
	}
	if (service) {
	  title = 'Edit Service'
	  refvars.ref_service = service.id
	  _(vjson).extend({
		service: service.id,
		sched: service.sched,
		enter: service.enter,
		exit: service.exit,
		odometer: service.odometer,
		total: service.total,
		observations: service.observations,
		servicetasks: _(service.servicetasks).values(),
	  })
	}
	else {
	  _(vjson).defaults({
		sched: $.fullCalendar.formatDate(new Date(), 'yyyy-MM-dd HH:mm'),
	  })
	}
	_log('modal', z, vjson)
	w_form.empty().jsonForm({
	  schema: {
		service: { type: 'string', required: true, "enum": _ids(data.services) },
		car: { type: 'string', required: true, "enum": _ids(data.cars) },
		car_owner: { type: 'string', required: true, "enum": _ids(data.owners) },
		car_owner_name: { type: 'string', required: true },
		car_model: { type: 'string', required: true, "enum": _ids(data.models) },
		car_year: { type: 'string', required: true },
		car_plate: { type: 'string' },
		sched: { type: 'string' },
		enter: { type: 'string' },
		exit: { type: 'string' },
		odometer: { type: 'integer' },
		total: { type: 'number' },
		observations: { type: 'string' },
		servicetasks: {
		  type: 'array',
		  items: {
			type: 'object',
			title: 'Task',
			properties: {
			  id: { type: 'string' },
			  task: { type: 'string', required: true, "enum": _ids(tasks) },
			  start: { type: 'string' },
			  end: { type: 'string' },
			  observations: { type: 'string' },
			}
		  },
		},
	  },
	  form: [
		service ? { key: 'service', titleMap: _obj(data.services), prepend: 'Service', notitle: true, disabled: true } : {},
		car && !service ? { key: 'car', titleMap: _obj(data.cars), prepend: 'Car', notitle: true, disabled: true } : {},
		z.owner_id ? { key: 'car_owner', titleMap: _obj(data.owners), prepend: 'Owner', notitle: true, disabled: true } : {},
		car || z.owner_id ? {} : { key: 'car_owner_name', prepend: 'Owner', notitle: true },
		car ? {} : { key: 'car_model', titleMap: _obj(data.models), prepend: 'Model', notitle: true },
		car ? {} : { key: 'car_year', prepend: 'Year', notitle: true },
		car ? {} : { key: 'car_plate', prepend: 'Plate', notitle: true },
		{ key: 'sched', prepend: 'Schedule', notitle: true },
		{ key: 'enter', prepend: 'Enter', notitle: true },
		{ key: 'exit', prepend: 'Exit', notitle: true },
		{ key: 'odometer', prepend: 'Odometer', notitle: true },
		{ key: 'total', prepend: 'Total', notitle: true },
		{ key: 'observations', prepend: 'Observations', notitle: true },
		{
		  type: 'tabarray',
		  items: [
			{
			  type: 'section',
			  legend: '{{idx}}',
			  items: [
				{ key: 'servicetasks[].id', prepend: 'Ref', notitle: true, readonly: true },
				{ key: 'servicetasks[].task', titleMap: _obj(tasks), prepend: 'Task', notitle: true },
				{ key: 'servicetasks[].start', prepend: 'Start', notitle: true },
				{ key: 'servicetasks[].end', prepend: 'End', notitle: true },
				{ key: 'servicetasks[].observations', prepend: 'Observations', notitle: true },
			  ],
			},
		  ],
		},
		{ type: 'submit', title: 'Save Service', htmlClass: 'btn-success center-block' },
		// isnew ? '' : { type: 'button', title: 'Delete', id: 'service-delete', htmlClass: 'btn-danger btn-xs pull-right' }
	  ],
	  value: vjson,
	  onSubmitValid: function(vals){ // https://github.com/joshfire/jsonform/wiki#wiki-submission-values
		var postvars = _({}).extend(refvars, vals)
		_log('onSubmitValid', postvars)
		$.ajax({
		  url: '/cars/ajax',
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
	w_form.find('.tabbable:last').before('<label class="control-label">Tasks</label>')
	w_modal.find('#service-label').text(title)
	w_modal.modal('show')
  }

  function service_edit(service_id) {
	var service = data.services[service_id]
	// _log('service_edit', service_id, service)
	modal({ service: service })
  }

  w_doc.on('click', '.service-owner-car-create', function(){
	var w_act = $(this)
	// _log('click @ service-owner-car-create', w_act)
	modal()
  })

  w_doc.on('click', '.service-car-create', function(){
	var w_act = $(this)
	var owner_id = w_act.data('ref')
	// _log('click @ service-car-create', w_act, owner_id)
	modal({ owner_id: owner_id })
  })

  w_doc.on('click', '.service-create', function(){
	var w_act = $(this)
	var car_id = w_act.data('ref')
	var car = data.cars[car_id]
	// _log('click @ service-create', w_act, car_id, car)
	modal({ car: car })
  })

  w_doc.on('click', '.service-edit', function(){
	var w_act = $(this)
	var service_id = w_act.data('ref')
	// _log('click @ service-edit', w_act, service_id)
	service_edit(service_id)
  })

  function _button(cls_button, cls_service, ref, label) {
	return _('<p><button class="btn btn-%s btn-sm %s" data-ref="%s">%s</button></p>').sprintf(cls_button, cls_service, ref, label)
  }

  $('#create-full').html(_button('default center-block', 'service-owner-car-create', '', '+ Owner & Car & Service'))

  w_dt.dataTable({
    // paging: false,
    // filter: false,
    // info: false,
    columns: [
	  { title: 'Owner', data: 'owner_info' },
	  { title: 'Services', data: 'acts', sortable: false },
	  { title: 'Make', data: 'make_name' },
	  { title: 'Model', data: 'model_name' },
	  { title: 'Engine', data: 'engine_name' },
	  { title: 'Year', data: 'year' },
	  { title: 'Plate', data: 'plate' },
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
	selectable: true,
	selectHelper: true,
	select: function(start, end, allDay, ev, view) {
	  _log('cal.select')
	  modal({ sched: start })
	},
	dayClick: null, // otherwise it will trigger "select" again.
	// editable: true, // draggable & resizable events.
	eventDrop: function(calev, dayDelta, minuteDelta, allDay, revertFunc, ev, ui, view) { // http://arshaw.com/fullcalendar/docs/event_ui/eventDrop/
	  _log('cal.eventDrop')
	},
	eventResize: function(calev, dayDelta, minuteDelta, revertFunc, ev, ui, view) { // http://arshaw.com/fullcalendar/docs/event_ui/eventResize/
	  _log('cal.eventResize')
	},
	eventClick: function(calev, ev, view) {
	  _log('cal.eventClick')
	  service_edit(calev.id)
	},
	events: [],
  })

  function data_set() {
	_log('data_set', data)
	var data_cars = _(data.cars).values()

	_(data.services).each(function(service, id){
	  service['datetime'] = service.start || service.sched
	})

	var events = _(_(data.services)).collect(function(service, id){
	  return { id: service.id, allDay: false, start: service.datetime, end: service.end, title: service.car_name }
	})

	_(data_cars).each(function(car){
	  _(car).extend({
		acts: (_([
		  _button('default', 'service-create', car.id, '+ Service'),
		  _(_(_(car.services).collect(function(id){ return data.services[id] })).sortBy('datetime')).collect(function(service) {
			return _button('primary', 'service-edit', service.id, service.datetime || '?')
		  })
		]).flatten()).join(' '),
		owner_info: [
		  _('<p> %s </p>').sprintf(car.owner_name),
		  _button('default', 'service-car-create', car.owner, '+ Car & Service')
		].join(' '),
	  })
	})

	api.clear()
	api.rows.add(data_cars)
	api.draw()

	w_cal
	  .fullCalendar('removeEvents')
	  .fullCalendar('addEventSource', events)
	  .fullCalendar('refetchEvents')
  }

  data_set()
})
