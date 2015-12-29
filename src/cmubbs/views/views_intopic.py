from django.utils.timezone import get_current_timezone
from utils import *

@transaction.atomic
def add_reply_notification(user_post, user_to_remind, reply_type, key):
	if user_post != user_to_remind:
		if not Notification.objects.filter(user=user_to_remind).filter(notification_type__startswith="reply").filter(key=key).exists():
			new_notification = Notification(user=user_to_remind, notification_type=reply_type, key=key)
			new_notification.save()


def in_topic(request, topic_id):
	topic = None
	context = {}
	topic = get_object_or_404(Topic, id=topic_id)
	context['secret'] = topic.forum.secret
	context['topic'] = topic
	print topic.tags.all()
	for tag in topic.tags.all():
		print tag.name
		if tag.name == 'Vote':
			context['poll'] = get_object_or_404(Poll, topic=topic)
			votes_num = 0
			for choice in context['poll'].choices.all():
				votes_num += choice.votes
			votes_num = max(votes_num,1)
			context['vote_per'] = {}
			for choice in context['poll'].choices.all():
				context['vote_per'][choice] = int((choice.votes+0.0)/votes_num*100)

	
	post_list = Post.objects.filter(topic__exact=topic).order_by("created_on")
	paginator = Paginator(post_list, 10)

	if request.method == 'POST':
		page = paginator.num_pages
	elif 'page_num' in request.GET:
		page = request.GET['page_num']
	else:
		page = request.GET.get('page')

	if page != None and int(page) == -1:
		page = paginator.num_pages
	posts = getPageContent(paginator, page)

	context['posts'] = posts
	context['commentable'] = check_login(request.user)# and (context['secret'] == False)
	context['post_pages'] = [None]*paginator.num_pages
	if page != None:
		context['post_pages'][int(page)-1] = 1
	
	if request.session.session_key and not TopicView.objects.filter(topic=topic,session=request.session.session_key):
		new_view = TopicView(topic=topic,session=request.session.session_key)
		new_view.save()
		clean_view_count_history()
		topic.view_count += 1
		topic.save()
	if check_login(request.user):
		context['like'] = check_like(request.user, topic)
		context['edit_title'] = check_topic_permission(request.user, topic)
		context['participated'] = False
		context['event_available'] = False
		context['userinfo'] = get_object_or_404(UserInfo, user=request.user)
		context['append_topic_form'] = AppendTopicForm()
		if Event.objects.filter(topic__exact=topic).exists():
			event = Event.objects.get(topic__exact=topic)
			context['participated'] = event.participants.filter(user__exact=request.user)
			context['event_available'] =  (Event.objects.filter(topic__exact=topic).filter(time_period__end__gte=datetime.date.today).exists()) and (len(event.participants.all()) < event.max_participants) and not EventApplication.objects.filter(applicant__exact=request.user).filter(event__topic__exact=topic).exists()
			if not event.public :
				context['apply_form'] = EventApplicationForm()
	form = ReplyPostForm(request.POST)
	comment_form = ReplyCommentForm()
	context['comment_form'] = comment_form
	if not form.is_valid():
		context ['form'] = form
		return render(request, 'InTopic.html', context)
	if request.method == 'POST':
		new_reply = Post(text=form.cleaned_data['reply_body'], user=request.user, topic=topic, plain_text=form.cleaned_data['plain_text'])
		new_reply.save()

		topic.last_reply_on = new_reply.created_on
		topic.save()

	# create notification for new post
	add_reply_notification(request.user, topic.user, "reply-newpost", topic.id)
	for liked_user in topic.liked.all():
		add_reply_notification(request.user, liked_user, "reply-likepost", topic.id)

	

	if request.FILES:
		save_post_images(request, new_reply)

	return HttpResponseRedirect(topic_id+'?page='+str(page))


@login_required
@transaction.atomic
def save_post_images(request, post):
	for up_image in request.FILES.getlist('up_image_list'):
		new_post_image = PostImage(post=post, forum = post.topic.forum)
		new_post_image.save()
		new_post_image.image.save(up_image.name,up_image)

def clean_view_count_history():
	cur_time = datetime.datetime.now().replace(tzinfo=get_current_timezone())-datetime.timedelta(1,0) # clear view session one day ago
	TopicView.objects.filter(created_on__lt=cur_time).delete()

@login_required
def like_topic(request, topic_id):
	topic = get_object_or_404(Topic, id=int(topic_id))
	topic.liked.add(request.user)
	topic.save()
	return HttpResponse()


@login_required
def dislike_topic(request, topic_id):
	topic = get_object_or_404(Topic, id=int(topic_id))
	topic.liked.remove(request.user)
	topic.save()
	return HttpResponse()

def check_like(user, topic):
	if user.like.filter(title=topic.title).exists():
		return True
	return False

def check_topic_permission(user, topic):
	forum = topic.forum
	return check_edit_permission(user, forum)

@login_required
@transaction.atomic
def reply_comment(request):
	reply_to_post = get_object_or_404(Post, id=request.POST["postId"])
	topic = reply_to_post.topic
	reply_form = ReplyCommentForm(request.POST)
	url = reverse('in_topic', kwargs={'topic_id':topic.id}) + '?page=-1'
	if not reply_form.is_valid():
		return redirect(url)
	new_post = Post(text=reply_form.cleaned_data['reply_comment_body'], user=request.user, topic=topic, reply_to=reply_to_post)
	new_post.save()
	topic.last_reply_on = new_post.created_on
	topic.save()

	# create notification for reply comment
	add_reply_notification(request.user, reply_to_post.user, "reply-replypost", topic.id)
	add_reply_notification(request.user, topic.user, "reply-newpost", topic.id)
	for liked_user in topic.liked.all():
		add_reply_notification(request.user, liked_user, "reply-likepost", topic.id)
		
	return redirect(url)

@login_required
def vote(request, topic_id):
	topic = get_object_or_404(Topic, id=topic_id)
	poll = get_object_or_404(Poll, topic=topic)
	userinfo = UserInfo.objects.get(user=request.user)
	if poll.is_multiple == True:
		if userinfo in poll.polled_by.all()[:] or 'checkbox' not in request.POST or len(request.POST.getlist('checkbox')) == 0:
			return redirect(reverse('in_topic',  kwargs={'topic_id':topic_id}))
		votes = request.POST.getlist('checkbox')
	else:
		if userinfo in poll.polled_by.all()[:] or 'optionsradio' not in request.POST or len(request.POST['optionsradio']) == 0:
			return redirect(reverse('in_topic',  kwargs={'topic_id':topic_id}))
		votes = [request.POST['optionsradio']]
	print votes
	for index,choice in enumerate(poll.choices.all()):
		if str(index+1) in votes:
			choice.votes += 1
			choice.save()
	poll.polled_by.add(userinfo)
	poll.save()

	return redirect(reverse('in_topic',  kwargs={'topic_id':topic_id}))


@login_required
@transaction.atomic
def add_sub_post(request, topic_id):

	append_topic_form = AppendTopicForm(request.POST)
	if not append_topic_form.is_valid():
		# context['append_topic_form'] = AppendTopicForm()
		return redirect(reverse('in_topic',  kwargs={'topic_id':topic_id}))

	topic = get_object_or_404(Topic, id=topic_id)
	father_post = topic.post.all().order_by('created_on')[0]

	new_sub_post = SubPost(text = append_topic_form.cleaned_data['append_topic_body'], father_post=father_post)
	new_sub_post.save()

	topic.last_reply_on = new_sub_post.created_on
	topic.save()

	return redirect(reverse('in_topic',  kwargs={'topic_id':topic_id}))




