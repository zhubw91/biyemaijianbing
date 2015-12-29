import datetime

from django.utils import timezone
from utils import *

RCD_PER_PAGE = 8

def user_own_events(request, userid):
	context = {}
	context['user_info'] = get_object_or_404(UserInfo, user__username=userid)
	event_list = Event.objects.filter(topic__user__exact=context['user_info'].user).order_by("-time_period__start")
	
	paginator = Paginator(event_list, RCD_PER_PAGE)
	context['pages'] = [None] * paginator.num_pages
	page = request.GET.get('page')
	if page != None:
		context['pages'][int(page)-1] = 1
	context['own_events'] = getPageContent(paginator,page)

	return render(request, 'event/user_own_events.json', context, content_type="application/json")

@login_required
def user_event_applications(request):
	context = {}

	application_list = EventApplication.objects.filter(event__topic__user__exact=request.user).order_by("-created_on")
	paginator = Paginator(application_list, RCD_PER_PAGE)
	context['pages'] = [None] * paginator.num_pages
	page = request.GET.get('page')
	if page != None:
		context['pages'][int(page)-1] = 1

	context['event_applications'] = getPageContent(paginator,page)

	return render(request, 'event/user_event_applications.json', context, content_type="application/json")

def user_participating_events(request, userid):
	context = {}
	context['user_info'] = get_object_or_404(UserInfo, user__username=userid)

	event_list = context['user_info'].participating_events.order_by("-time_period__start")
	paginator = Paginator(event_list, RCD_PER_PAGE)
	context['pages'] = [None] * paginator.num_pages
	page = request.GET.get('page')
	if page != None:
		context['pages'][int(page)-1] = 1

	context['participanting_events'] = getPageContent(paginator,page)
	return render(request, 'event/user_participating_events.json', context, content_type="application/json")

@login_required
@transaction.atomic
def create_event(request, forum_name):
	context = {}
	forum = get_object_or_404(Forum, name=forum_name)
	context['forum'] = forum
	if request.method == 'GET':
		context['form'] = EventForm(initial={'start':timezone.now(),'end':timezone.now() + datetime.timedelta(minutes=60)})
		return render(request, 'event/create_event.html', context)

	form = EventForm(request.POST, user=request.user, forum=forum)

	if not form.is_valid():
		context ['form'] = form
		return render(request, 'event/create_event.html', context)
	new_event = form.save()
	new_event.topic.user = request.user
	new_event.topic.forum = forum
	new_event.save()
	return redirect(reverse('in_forum', kwargs={"forum_name":forum_name})+ "?filter_tag=Event")


@transaction.atomic
def load_events(request, forum_name):
	forum = get_object_or_404(Forum, name=forum_name)
	events = Event.objects.filter(topic__forum=forum).filter(time_period__end__gte=datetime.date.today)
	return render(request, 'event/events.json', {"events":events}, content_type="application/json")

@login_required
@transaction.atomic
def edit_event(request, topic_id):
	event = get_object_or_404(Event, topic_id__exact=topic_id)
	if event.topic.user.username != request.user.username:
		raise PermissionDenied()
	context = {}
	context['topic_id'] = topic_id
	context['participants'] = event.participants.all()
	if request.method == 'GET':
		context ['form'] = EventForm(event=event)
		context['participant_form'] = ParticipantForm(event=event)
		return render(request, 'event/edit_event.html', context)

	form = EventForm(request.POST,event=event)

	if not form.is_valid():
		context ['form'] = form
		return render(request, 'event/edit_event.html', context)
	form.save()
	return redirect(reverse('in_topic', kwargs={'topic_id':topic_id}))

@login_required
def apply_for_event(request, topic_id):
	if request.method == 'POST':
		event = get_object_or_404(Event, topic__id__exact=topic_id)
		event_available =  (Event.objects.filter(topic__exact=event.topic).filter(time_period__end__gte=datetime.date.today).exists()) and (len(event.participants.all()) < event.max_participants) and not EventApplication.objects.filter(applicant__exact=request.user).filter(event__exact=event).exists()
		if event.public	or event.participants.filter(user__exact=request.user).exists() or not event_available:
			raise PermissionDenied();
		user = User.objects.get(username=request.user)
		friend = event.topic.user
		context = {}
		apply_form = EventApplicationForm(request.POST)
		if not apply_form.is_valid():
			return HttpResponse()
		context['message'] = apply_form.cleaned_data['message']
		new_application = EventApplication(event=event, applicant=request.user, message=context['message'])
		new_application.save()

		context['application'] = new_application

		notification = Notification(user=friend, notification_type="event_app", key=event.topic.id)
		notification.save()
		
		return redirect(reverse('in_topic',kwargs={'topic_id':topic_id}))
	return HttpResponse()
@transaction.atomic
def add_event_participant(event, new_participant, notify=False):
	event.participants.add(new_participant.userinfo)
	event.save()
	if notify:
		context = {}
		context['operation'] = 'added into'
		context['event'] = event
		context['time'] = time.strftime("%I:%M %d/%m/%Y")
		notification = Notification(user=new_participant, notification_type="event_add", key=event.topic.id)
		notification.save()
	return True

@transaction.atomic
def delete_event_participant(event, participant, notify=False):
	if event.participants.filter(user__exact=participant).exists():
		event.participants.remove(participant.userinfo)
		event.save()
		if notify:
			context = {}
			context['operation'] = 'deleted from'
			context['event'] = event
			context['time'] = time.strftime("%I:%M %d/%m/%Y")
			notification = Notification(user=participant, notification_type="event_del", key=event.topic.id)
			notification.save()
		return True
	return False

@login_required
@transaction.atomic
def delete_participant(request, topic_id, userid):
	participant = get_object_or_404(User, username=userid)
	event = get_object_or_404(Event, topic__id__exact=topic_id)
	if event.topic.user != request.user:
		raise PermissionDenied()
	delete_event_participant(event, participant, True)
	return redirect(reverse('edit_event', kwargs={"topic_id":topic_id}))

@login_required
@transaction.atomic
def add_participant(request, topic_id):
	event = get_object_or_404(Event, topic__id__exact=topic_id)
	if event.topic.user != request.user:
		raise PermissionDenied()
	context = {}
	if request.method == 'GET':
		form = ParticipantForm(event=event)
		return render(request, 'event/add_participant.json', context, content_type="application/json")
	form = ParticipantForm(request.POST, event=event)
	if not form.is_valid():
		context ['participant_form'] = form
		context ['successful'] = False
		return render(request, 'event/add_participant.json', context, content_type="application/json")
	
	new_participant = get_object_or_404(User, username__exact=form.cleaned_data['username'])
	context ['successful'] = add_event_participant(event, new_participant, True)
	return render(request, 'event/add_participant.json', context, content_type="application/json")

@login_required
@transaction.atomic
def rsvp_event(request, topic_id):
	event = get_object_or_404(Event, topic__id__exact=topic_id)
	if not event.public:
		raise PermissionDenied()
	if not event.participants.filter(user__exact=request.user).exists():
		if len(event.participants.all()) < event.max_participants:
			add_event_participant(event, request.user, False)
			return JsonResponse({'rsvp_successful':True})
		else:
			return JsonResponse({'rsvp_successful':False})
		
@login_required
@transaction.atomic
def undo_rsvp_event(request, topic_id):
	event = get_object_or_404(Event, topic__id__exact=topic_id)
	st = delete_event_participant(event, request.user, False)
	return JsonResponse({'undo_rsvp_successful':st})

@login_required
@transaction.atomic
def accept_event_application(request, application_id):
	application = get_object_or_404(EventApplication, id__exact=application_id)
	if application.event.topic.user != request.user:
		raise PermissionDenied()
	add_event_participant(application.event, application.applicant, True)
	application.delete()
	return JsonResponse({'successful':True})

@login_required
@transaction.atomic
def decline_event_application(request, application_id):
	application = get_object_or_404(EventApplication, id__exact=application_id)
	if application.event.topic.user != request.user:
		raise PermissionDenied()
	application.delete()
	return JsonResponse({'successful':True})







