from utils import *

@login_required
def get_all_messages(request):
	context = {}
	user = User.objects.get(username=request.user)
	context['messageto_form'] = MessageToForm()
	if request.method == 'POST':
		messageto_form = MessageToForm(request.POST)
		if messageto_form.is_valid():
			print "haha"
			return redirect(reverse('get_messages_with', kwargs={'friend_name':messageto_form.cleaned_data['text']}))
		else:
			context['messageto_form'] = messageto_form

	all_related_messages = Message.objects.filter(Q(receiver=user) | Q(sender=user)).order_by('-created_on')
	messages = []
	
	user_list = {}
	for item in all_related_messages:
		# Add all related messages in one list according to the username
		if item.sender != user:

			if item.sender.username not in user_list:
				user_list[item.sender.username] = len(messages)
				message_to_show = item.text.split('\n')[0].split('<br>')[0]
				if len(message_to_show) > 50:
					message_to_show = message_to_show[:50] + "......"
				messages.append({'user':item.sender,'recently_message':item,'has_new_unread_messages':False,'message_to_show':message_to_show})

				if item.is_read == False:
					messages[user_list[item.sender.username]]['has_new_unread_messages'] = True

		if item.receiver != user:
			if item.receiver.username not in user_list:
				user_list[item.receiver.username] = len(messages)
				message_to_show = item.text.split('\n')[0]
				if len(message_to_show) > 50:
					message_to_show = message_to_show[:50] + "......"
				messages.append({'user':item.receiver,'recently_message':item,'has_new_unread_messages':False,'message_to_show':message_to_show})

	context['messages'] = messages
	return render(request, 'message/MessagesMain.html', context)

@login_required
@transaction.atomic
def get_messages_with(request, friend_name):
	context = {}
	user = User.objects.get(username=request.user)
	try:
		friend = User.objects.get(username=friend_name)
	except ObjectDoesNotExist:
		raise Http404("User does not exist")

	context['message_form'] = MessageForm()
	if request.method == 'POST':
		message_form = MessageForm(request.POST)
		if not message_form.is_valid():
			return redirect(reverse('get_messages_with', kwargs={'friend_name':friend_name}))
		new_message = Message(text=message_form.cleaned_data['message_body'],sender=request.user,receiver=friend)
		new_message.save()

	all_related_messages = Message.objects.filter((Q(receiver=user) & Q(sender=friend)) | (Q(receiver=friend) & Q(sender=user))).order_by('created_on')
	for message in all_related_messages:
		if message.sender == friend and message.is_read == False:
			message.is_read = True
			message.save()
	context['messages'] = all_related_messages
	context['friend'] = friend
	return render(request, 'message/MessagesThread.html', context)

@login_required
def get_notifications(request):
	user = request.user
	unread_messages = Message.objects.filter(Q(receiver=user) & Q(is_read=False))
	distinct_unread = []
	username_hash = {}
	for message in unread_messages:
		if message.sender.username not in username_hash:
			username_hash[message.sender.username] = 1
			distinct_unread.append(message.sender.username)
	unread = []
	for item in distinct_unread:
		unread.append({'type':'message', 'url':reverse('get_messages_with', kwargs={"friend_name":item}), 'text':item})
	notifications = request.user.notifications.all()
	for item in notifications:
		remove_url = reverse('remove_notifications', kwargs={"id":item.id})
		print remove_url
		if item.notification_type.startswith('reply'):
			topic = get_object_or_404(Topic, id=item.key)
			unread.append({'type':item.notification_type, 'url':reverse('in_topic', kwargs={"topic_id":topic.id})+'?page=-1', 'text':topic.title, 'id':remove_url})
		elif item.notification_type == 'follow':
			unread.append({'type':item.notification_type, 'url':reverse('user_profile', kwargs={"user_name":item.key})+'?page=-1', 'text':item.key, 'id':remove_url})
		elif item.notification_type.startswith('moderator'):
			forum = get_object_or_404(Forum, id=item.key)
			if forum.father_forum:
				unread.append({'type':item.notification_type, 'url':reverse('in_forum', kwargs={"forum_name":forum.name}), 'text':forum.name, 'id':remove_url})
			else:
				unread.append({'type':item.notification_type, 'url':reverse('sub_forum', kwargs={"father_forum_name":forum.name}), 'text':forum.name, 'id':remove_url})
		elif item.notification_type.startswith('event'):
			topic = get_object_or_404(Topic, id=item.key)
			if item.notification_type == "event_app":
				unread.append({'type':item.notification_type, 'url':reverse('user_profile') + '#event_applications', 'text':topic.title, 'id':remove_url})
			else:
				unread.append({'type':item.notification_type, 'url':reverse('in_topic', kwargs={"topic_id":topic.id}), 'text':topic.title, 'id':remove_url})
	return JsonResponse({'unread':unread})

@login_required
@transaction.atomic
def remove_notifications(request, id):
	if Notification.objects.filter(id=int(id)).exists():
		notification = Notification.objects.get(id=id)
		notification.delete()
	return HttpResponse(status=200)





