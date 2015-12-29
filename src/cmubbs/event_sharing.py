import datetime

from cmubbs.forms import *
from cmubbs.models import *
from django.forms import formset_factory
from django.conf import settings

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.files import File
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import escape
from django.utils.timezone import get_current_timezone

from mimetypes import guess_type


class ForumData:
	def __init__(self, forum_info):
		self.forum_info = forum_info
		self.threads = 0
		self.moderator = []

def user_login(request):
	username = request.POST['username']
	password = request.POST['password']
	user = authenticate(username=username, password=password)
	if check_login(user):
		login(request, user)
		return JsonResponse({'login_successful':True})
	return JsonResponse({'login_successful':False})

@login_required
def user_logout(request):
	logout(request)
	return HttpResponse()

@transaction.atomic
def user_register(request):
	#if request.method == 'POST':
	context = {}
	form = RegistrationForm(request.POST)
	if not form.is_valid():
		itemTemplate = loader.get_template('register_errors.html')
		html =  itemTemplate.render({'form':form}).replace('\n','') 
		context['register_successful'] = False
		context['html'] = html
		return JsonResponse(context)
	new_user = User.objects.create_user(username=form.cleaned_data['username'], \
										password=form.cleaned_data['password1'], \
										email=form.cleaned_data['email'])
	new_user.save()
	new_user_info = UserInfo(user=new_user)
	new_user_info.save()
	new_user = authenticate(username=form.cleaned_data['username'], \
							password=form.cleaned_data['password1'])
	login(request, new_user)
	context['register_successful'] = True
	return JsonResponse(context)

def intro(request):
	if check_login(request.user):
		if 'next' in request.GET and request.GET['next']:
			return redirect(request.GET['next'])
		return redirect(reverse('cmu_home'))
	return render(request, 'intro.html', {})

def home(request):
	context={}
	context['logged_in'] = check_login(request.user)
	if context['logged_in']:
		user = request.user
		favourites = UserInfo.objects.get(user__exact=user).favorite_forums.all()
		context['favourites'] = favourites
	forums = list(Forum.objects.filter(father_forum__exact=None))
	len_forums = len(forums)
	forum_reorder = []

	i = 0
	while i< len_forums:  # three sessions one line
		forum_reorder.append(forums[i:i+3])
		i += 3
	context['forums'] = forum_reorder
	context['tags'] = ['title','author']
	context['form'] = SearchKeyForm()
	return render(request, 'HomePage.html', context)


def hot_topics(request):
	context = {}
	context['logged_in'] = check_login(request.user)
	cur_date = time.strftime("%Y-%m-%d")
	#cur_date = '2015-10-30'  # for test
	cur_topics = Topic.objects.filter(created_on__range=[cur_date+' 00:00:00',cur_date+' 23:59:59']).order_by("-created_on")
	hot_topics = sorted(cur_topics,  key=lambda t: t.score, reverse=True)[:10]
	context['topics'] =  hot_topics
	return render(request, 'HotTopics.html',context)

def user_profile(request, user_name):
	context = {}
	try:
		user_to_show = User.objects.get(username=user_name)
	except ObjectDoesNotExist:
		raise Http404("No such user!")
	context['user_info'] = UserInfo.objects.get(user=user_to_show)
	context['logged_in'] = check_login(request.user)
	context['if_self'] = False
	if context['logged_in'] and user_to_show == request.user:
		context['if_self'] = True
	return render(request, 'UserProfile.html', context)

@login_required
def get_all_messages(request):
	context = {}
	context['logged_in'] = True
	user = User.objects.get(username=request.user)
	all_related_messages = Message.objects.filter(Q(receiver=user) | Q(sender=user)).order_by('created_on')
	messages = []
	user_list = {}
	for item in all_related_messages:
		# Add all related messages in one list according to the username
		if item.sender != user:

			if item.sender.username not in user_list:
				user_list[item.sender.username] = len(messages)
				messages.append({'user':item.sender,'message_list':[],'has_new_unread_messages':False})
			messages[user_list[item.sender.username]]['message_list'].append(item)
			if item.is_read == False:
				messages[user_list[item.sender.username]]['has_new_unread_messages'] = True

		if item.receiver != user:
			if item.receiver.username not in user_list:
				user_list[item.receiver.username] = len(messages)
				messages.append({'user':item.receiver,'message_list':[]})
			messages[user_list[item.receiver.username]]['message_list'].append(item)
	context['messages'] = messages
	return render(request, 'MessagesMain.html', context)

@login_required
def get_messages_with(request, friend_name):
	context = {}

	context['logged_in'] = True

	user = User.objects.get(username=request.user)
	try:
		friend = User.objects.get(username=friend_name)
	except ObjectDoesNotExist:
		raise Http404("User does not exist")
	if request.method == 'POST':
		new_message = Message(text=request.POST['new_message'],sender=request.user,receiver=friend)
		new_message.save()

	all_related_messages = Message.objects.filter((Q(receiver=user) & Q(sender=friend)) | (Q(receiver=friend) & Q(sender=user))).order_by('created_on')
	for message in all_related_messages:
		if message.sender == friend and message.is_read == False:
			message.is_read = True
			message.save()
	context['messages'] = all_related_messages
	context['friend'] = friend
	return render(request, 'MessagesThread.html', context)

@login_required
def apply_for_event(request, topic_id):
	event = get_object_or_404(Event, topic__id__exact=topic_id)
	
	user = User.objects.get(username=request.user)
	friend = event.topic.user
	context = {}
	context['message'] = "Please accept my application~~~" #request.POST['new_message']

	new_application = EventApplication(event=event, applicant=request.user, message=context['message'])
	new_application.save()

	context['application'] = new_application
	notification_template = loader.get_template('sys_notifications/event_application.html')
	notification_content = notification_template.render(Context(context))
	sysuser = User.objects.get(username='cmubbs-system')
	new_message = Message(text=notification_content,sender=sysuser,receiver=friend)
	new_message.save()
	
	return redirect(reverse('in_topic',kwargs={'topic_id':topic_id}))


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
	return JsonResponse({'unread':distinct_unread})

def sub_forum(request, father_forum_name):
	father_forum = None
	context = {'father_forum_name':father_forum_name}
	father_forum = get_object_or_404(Forum, name=father_forum_name)
	
	context['father_forum'] = father_forum
	context['secret'] = father_forum.secret
	sub_forums = Forum.objects.filter(father_forum__exact=father_forum)
	if len(sub_forums) != 0:
		context['tags'] = ['title','author']
		context['form'] = SearchKeyForm()
		context['sub_forums'] = sub_forums
		check_favourite(request, father_forum, context)
	else:
		return redirect(reverse('in_forum',kwargs={'forum_name':father_forum_name}))

	return render(request, 'SubForum.html', context)


def in_forum(request, forum_name):
	forum = None
	context = {'forum_name':forum_name}
	context['logged_in'] = check_login(request.user)
	forum = get_object_or_404(Forum, name=forum_name)
	if context['logged_in']:
		context['edit_topic'] = check_edit_permission(request.user, forum)
	
	context['forum'] = forum
	context['secret'] = forum.secret
	context['tags'] = ['title','author']
	context['topic_tags'] = Tag.objects.all()
	context['form'] = SearchKeyForm()

	if 'go_filter_tag' in request.GET:
		filter_tag = request.GET['go_filter_tag']
	else:
		filter_tag = request.GET.get('filter_tag')
	context['filter_tag'] = filter_tag
	
	topic_list = Topic.objects.filter(forum__exact=forum).order_by('-upped', '-created_on')

	if filter_tag != None:
		if filter_tag == 'good':
			topic_list = topic_list.filter(good_topic=True)
		elif filter_tag == 'all':
			pass
		else:
			filter_tag_obj = get_object_or_404(Tag, name=filter_tag)
			topic_list = topic_list.filter(tags__exact=filter_tag_obj)
	else:
		filter_tag = 'all'
	context['filter_tag'] = filter_tag
	paginator = Paginator(topic_list, 10)  # test----5 post per page

	if 'page_num' in request.GET:
		page = request.GET['page_num']
	else:
		page = request.GET.get('page')

	topics = getPageContent(paginator,page)
	
	context['topics'] = topics
	context['topic_pages'] = [None] * paginator.num_pages
	if page != None:
		context['topic_pages'][int(page)-1] = 1

	check_favourite(request, forum, context)
	return render(request, 'InForum.html', context)


def getPageContent(paginator,page):
	content = None
	try:
		content = paginator.page(page)
	except PageNotAnInteger:
		content = paginator.page(1)
	except EmptyPage:
		content = paginator.page(paginator.num_pages)
	return content


def check_login(user):
	if user is not None:
		if user.is_active:
			return True
	return False

def check_favourite(request, forum, context):
	context['logged_in'] = check_login(request.user)
	if context['logged_in']:
		if forum.favorited_by.filter(user__exact=request.user).exists():
			context['favorite'] = True
		else:
			context['favorite'] = False


def in_topic(request, topic_id):
	topic = None
	context = {}

	topic = get_object_or_404(Topic, id=topic_id)
	context['secret'] = topic.forum.secret
	context['topic'] = topic
	for tag in topic.tags.all():
		if tag.name == 'vote':
			context['poll'] = get_object_or_404(Poll, topic=topic)
			votes_num = 0
			for choice in context['poll'].choices.all():
				votes_num += choice.votes
			votes_num = max(votes_num,1)
			context['vote_per'] = {}
			for choice in context['poll'].choices.all():
				context['vote_per'][choice] = (choice.votes+0.0)/votes_num*100

	
	post_list = Post.objects.filter(topic__exact=topic).order_by("created_on")
	paginator = Paginator(post_list, 5)  # test----5 post per page

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
	context['logged_in'] = check_login(request.user)
	context['commentable'] = context['logged_in'] and (context['secret'] == False)
	context['post_pages'] = [None]*paginator.num_pages
	if page != None:
		context['post_pages'][int(page)-1] = 1
	
	if request.session.session_key and not TopicView.objects.filter(topic=topic,session=request.session.session_key):
		new_view = TopicView(topic=topic,session=request.session.session_key)
		new_view.save()
		clean_view_count_history()
		topic.view_count += 1
		topic.save()
	if context['logged_in']:
		context['like'] = check_like(request.user, topic)
		context['edit_title'] = check_topic_permission(request.user, topic)
		context['participated'] = False
		context['event_available'] = False
		context['event_public'] = False
		context['userinfo'] = get_object_or_404(UserInfo, user=request.user)
		if Event.objects.filter(topic__exact=topic).exists():
			event = Event.objects.get(topic__exact=topic)
			context['event_public'] = event.public
			context['participated'] = event.participants.filter(user__exact=request.user)
			context['event_available'] =  (Event.objects.filter(topic__exact=topic).filter(time_period__end__gte=datetime.date.today).exists()) and (len(event.participants.all()) < event.max_participants) and not EventApplication.objects.filter(applicant__exact=request.user).filter(event__topic__exact=topic).exists()
			
	form = ReplyPostForm(request.POST)
	comment_form = ReplyCommentForm()
	context['comment_form'] = comment_form
	if not form.is_valid():
		context ['form'] = form
		return render(request, 'InTopic.html', context)
	new_reply = Post(text=form.cleaned_data['reply_body'], user=request.user, topic=topic)
	new_reply.save()

	return HttpResponseRedirect(topic_id+'?page='+str(page))


def clean_view_count_history():
	cur_time = datetime.datetime.now().replace(tzinfo=get_current_timezone())-datetime.timedelta(1,0) # clear view session one day ago
	TopicView.objects.filter(created_on__lt=cur_time).delete()

def check_like(user, topic):
	if user.like.filter(title=topic.title).exists():
		return True
	return False

def check_topic_permission(user, topic):
	forum = topic.forum
	return check_edit_permission(user, forum)

@login_required
def good_topic(request, topic_id):
	topic = get_object_or_404(Topic, id=int(topic_id))
	topic.good_topic = True
	topic.save()
	return HttpResponse()

@login_required
def normal_topic(request, topic_id):
	topic = get_object_or_404(Topic, id=int(topic_id))
	topic.good_topic = False
	topic.save()
	return HttpResponse()


@login_required
def up_topic(request, topic_id):
	topic = get_object_or_404(Topic, id=int(topic_id))
	topic.upped = True
	topic.save()
	return HttpResponse()

@login_required
def down_topic(request, topic_id):
	topic = get_object_or_404(Topic, id=int(topic_id))
	topic.upped = False
	topic.save()
	return HttpResponse()

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

@login_required
def favorite_forum(request, forum_name):
	try:
	  forum = Forum.objects.get(name__exact=forum_name)
	except ObjectDoesNotExist:
		raise Http404("the forum does not DoesNotExist")
	request.user.userinfo.favorite_forums.add(forum)
	request.user.save()
	return HttpResponse()


@login_required
def dislike_forum(request, forum_name):
	try:
	  forum = Forum.objects.get(name__exact=forum_name)
	except ObjectDoesNotExist:
		raise Http404("the forum does not DoesNotExist")
	request.user.userinfo.favorite_forums.remove(forum)
	request.user.save()
	return HttpResponse()

@login_required
@transaction.atomic
def edit_profile(request):
	context = {}
	user_info = get_object_or_404(UserInfo, user=request.user)
	context ['user_info'] = user_info
	context['logged_in'] = True
	if request.method == 'GET':
		user_form = UserForm(instance=request.user)
		userinfo_form = UserInfoForm(instance=user_info)
		userimg_form = UserImgForm(instance=user_info)
		context ['user_form'] = user_form
		context['userimg_form'] = userimg_form
		context ['userinfo_form'] = userinfo_form
		return render(request, 'edit_profile.html', context)

	user_form = UserForm(request.POST, instance=request.user)
	userinfo_form = UserInfoForm(request.POST, instance=user_info)

	if (not user_form.is_valid()) or (not userinfo_form.is_valid()):
		context ['user_form'] = user_form
		context ['userinfo_form'] = userinfo_form
		return render(request, 'edit_profile.html', context)

	user_form.save()
	userinfo_form.save()

	return redirect(reverse('cmu_home')) # TODO change to user profile page

@login_required
@transaction.atomic
def upload_usr_image(request):
	if request.method == 'GET':
		return redirect(reverse('edit_profile'))

	user_info = get_object_or_404(UserInfo, user=request.user)
	userimg_form = UserImgForm(request.POST, request.FILES, instance = user_info)
	if not userimg_form.is_valid():
		return redirect(reverse('edit_profile'))
	userimg_form.save()
	return redirect(reverse('edit_profile'))


@login_required
@transaction.atomic
def change_password(request):
	context = {}
	context['logged_in'] = True
	user_info = get_object_or_404(UserInfo, user=request.user)
	if request.method == 'GET':
		context['form'] = PasswordForm()
		return render(request, 'change_password.html', context)

	form = PasswordForm(request.POST)
	context['form'] = form

	if not form.is_valid():
		return render(request, 'change_password.html', context)

	request.user.password = form.cleaned_data['password1']
	request.user.save()
	return redirect(reverse('cmu_home'))

def get_profile_photo(request, userid):
	user = get_object_or_404(User, username=userid)
	user_info = get_object_or_404(UserInfo, user=user)
	if not user_info.image:
		return HttpResponse(open(settings.DEFAULT_PROFILE_IMG).read(), content_type='image/jpeg')
		#raise Http404  
	content_type = guess_type(user_info.image.name)
	return HttpResponse(user_info.image, content_type=content_type)


def user_events(request, userid):
	context = {}
	context['user_info'] = get_object_or_404(UserInfo, user__username=userid)
	context['logged_in'] = check_login(request.user)
	if context['logged_in'] and context['user_info'] == request.user.userinfo:
		context['event_applications'] = EventApplication.objects.filter(event__topic__user__exact=request.user).order_by("-created_on")
	context['own_events'] = Event.objects.filter(topic__user__exact=context['user_info'].user).order_by("-time_period__start")
	context['participanting_events'] = context['user_info'].participating_events.order_by("-time_period__start")
	return render(request, 'user_events.html', context)

@login_required
def manage_forums(request):
	context = {}
	context['logged_in'] = True
	if request.user.userinfo.user_group == 0:
		context['father_forum_set'] = Forum.objects.all().filter(father_forum__exact=None)
	context['my_father_forums'] = request.user.userinfo.manages.filter(father_forum__exact=None)
	context['my_sub_forums'] = request.user.userinfo.manages.exclude(father_forum__exact=None)
	return render(request, 'manage_forums.html', context)

def check_edit_permission(user, forum):
	if user.userinfo.user_group == 0:
		return True
	if user.userinfo.manages.filter(name__exact=forum.name).exists():
		return True
	if forum.father_forum and user.userinfo.manages.filter(name__exact=forum.father_forum.name).exists():
		return True
	return False

def check_delete_permission(user, forum):
	if user.userinfo.user_group == 0:
		return True
	if forum.father_forum and user.userinfo.manages.filter(name__exact=forum.father_forum.name).exists():
		return True
	return False

@login_required
def add_sub_forum(request, father_forum_name):
	context = {}
	context['logged_in'] = True
	
	father_forum = get_object_or_404(Forum, name__exact=father_forum_name)
	if father_forum.father_forum: # not a father forum
		raise Http404();
	context ['father_forum_name'] = father_forum_name
	if not request.user.userinfo.manages.filter(name__exact=father_forum_name).exists():
		raise PermissionDenied()
	
	if request.method == 'GET':
		context ['form'] = ForumForm()
		return render(request, 'add_sub_forum.html', context)

	form = ForumForm(request.POST)

	if not form.is_valid():
		context ['form'] = form
		return render(request, 'add_sub_forum.html', context)
	new_forum = form.save(commit=False)
	new_forum.father_forum = father_forum
	new_forum.save()
	return redirect(reverse('manage_forums'))

@login_required
def add_father_forum(request):
	context = {}
	context['logged_in'] = True
	if request.user.userinfo.user_group > 0:
		raise PermissionDenied()
	
	if request.method == 'GET':
		context ['form'] = ForumForm()
		return render(request, 'add_father_forum.html', context)

	form = ForumForm(request.POST)

	if not form.is_valid():
		context ['form'] = form
		return render(request, 'add_father_forum.html', context)
	form.save()
	return redirect(reverse('manage_forums'))

@login_required
def edit_forum(request, forum_name):
	
	forum = get_object_or_404(Forum, name=forum_name)
	if not check_edit_permission(request.user, forum):
		raise PermissionDenied()
	context = {}
	context['logged_in'] = True
	context ['forum_name'] = forum_name
	context['moderators'] = forum.moderators.all()
	context['delete_permission'] = check_delete_permission(request.user, forum)
	context ['moderator_form'] = ModeratorForm(forum_name=forum_name)
	if request.method == 'GET':
		context ['form'] = ForumForm(instance=forum)
		return render(request, 'edit_forum.html', context)

	form = ForumForm(request.POST,instance=forum)

	if not form.is_valid():
		context ['form'] = form
		return render(request, 'edit_forum.html', context)
	form.save()
	return redirect(reverse('manage_forums'))


@login_required
def delete_forum(request, forum_name):
	context = {}
	forum = get_object_or_404(Forum, name=forum_name)
	if not check_delete_permission(request.user, forum):
		raise PermissionDenied()
	context['logged_in'] = True
	forum.delete()
	return redirect(reverse('manage_forums'))

@login_required
def edit_moderator(request, forum_name):
	if request.method == 'POST':
		forum = get_object_or_404(Forum, name=forum_name)
		if not check_edit_permission(request.user, forum):
			raise PermissionDenied()

		context = {}
		context['logged_in'] = True
		context ['forum_name'] = forum_name
		context['moderators'] = forum.moderators.all()
		context['delete_permission'] = check_delete_permission(request.user, forum)

		form = ModeratorForm(request.POST, forum_name=forum_name)
		if not form.is_valid():
			context ['moderator_form'] = form
			context ['form'] = ForumForm(instance=forum)
			return render(request, 'edit_forum.html', context)

		new_moderator = get_object_or_404(User, username=form.cleaned_data['username'])
		forum.moderators.add(new_moderator.userinfo)
		forum.save()
		update_user_group(new_moderator.userinfo)
		context['moderator_form'] = ModeratorForm(forum_name=forum_name)
		return redirect(reverse('edit_forum', kwargs={"forum_name":forum_name}))

def update_user_group(userinfo):
	if userinfo.user_group > 0:
		if userinfo.manages.filter(father_forum__exact=None).exists():
			userinfo.user_group = 1
		elif userinfo.manages.exclude(father_forum__exact=None).exists():
			userinfo.user_group = 2
		else:
			userinfo.user_group = 3
		userinfo.save()

@login_required
def delete_moderator(request, forum_name, userid):
	forum = get_object_or_404(Forum, name=forum_name)
	moderator = get_object_or_404(User, username=userid)
	if not check_delete_permission(request.user, forum):
		raise PermissionDenied()
	forum.moderators.remove(moderator.userinfo)
	forum.save()
	update_user_group(moderator.userinfo)
	return redirect(reverse('edit_forum', kwargs={"forum_name":forum_name}))

@transaction.atomic
def add_event_participant(event, new_participant, notify=False):
	event.participants.add(new_participant.userinfo)
	event.save()
	if notify:
		context = {}
		context['operation'] = 'added into'
		context['event'] = event
		context['time'] = time.strftime("%I:%M %d/%m/%Y")
		notification_template = loader.get_template('sys_notifications/participant_change.html')
		notification_content = notification_template.render(Context(context))
		sysuser = User.objects.get(username='cmubbs-system')
		new_message = Message(text=notification_content,sender=sysuser,receiver=new_participant)
		new_message.save()
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
			notification_template = loader.get_template('sys_notifications/participant_change.html')
			notification_content = notification_template.render(Context(context))
			sysuser = User.objects.get(username='cmubbs-system')
			new_message = Message(text=notification_content,sender=sysuser,receiver=participant)
			new_message.save()
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
		return render(request, 'add_participant.json', context, content_type="application/json")
	form = ParticipantForm(request.POST, event=event)
	if not form.is_valid():
		context ['participant_form'] = form
		context ['successful'] = False
		return render(request, 'add_participant.json', context, content_type="application/json")
	
	new_participant = get_object_or_404(User, username__exact=form.cleaned_data['username'])
	context ['successful'] = add_event_participant(event, new_participant, True)
	return render(request, 'add_participant.json', context, content_type="application/json")

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


@login_required
@transaction.atomic
def new_post(request, forum_name):
	context = {}
	context['logged_in'] = True
	forum = get_object_or_404(Forum, name=forum_name)

	tags = Tag.objects.exclude(name__exact='Event')
	context['forum'] = forum
	context['tags'] = tags

	if request.method == 'GET':
		context['form'] = CreatePostForm()
		return render(request, 'NewPost.html', context)

	form = CreatePostForm(request.POST)

	if not form.is_valid():
		context ['form'] = form
		return render(request, 'NewPost.html', context)

	new_topic = Topic(user=request.user, forum=forum, title=form.cleaned_data['post_title'])
	new_topic.save()
	if 'tag' in request.POST and len(request.POST['tag']) != 0:
		tag = get_object_or_404(Tag, name=request.POST['tag'])
		new_topic.tags.add(tag)
	new_topic.save()

	new_post = Post(text=form.cleaned_data['post_body'], user=request.user, topic=new_topic)
	new_post.save()

	# save images
	if request.FILES:
		save_post_images(request, new_post)
	return redirect(reverse('in_forum', kwargs={"forum_name":forum_name}))


@login_required
@transaction.atomic
def save_post_images(request, post):
	for up_image in request.FILES.getlist('up_image_list'):
		new_post_image = PostImage(post=post)
		new_post_image.save()
		new_post_image.image.save(up_image.name,up_image)


def post_images(request, image_id):
	try:
	  post_image = PostImage.objects.get(id__exact=image_id)
	except ObjectDoesNotExist:
		return HttpResponse(open(settings.DEFAULT_POST_IMG).read(), content_type='image/jpeg')

	content_type = guess_type(post_image.image.name) 
	return HttpResponse(post_image.image, content_type=content_type)


@login_required
@transaction.atomic
def new_poll(request, forum_name):
	
	context = {}
	
	context['logged_in'] = True
	forum = get_object_or_404(Forum, name=forum_name)

	tags = Tag.objects.exclude(name__exact='Event')
	context['forum'] = forum
	context['tags'] = tags

	if request.method == 'GET':
		context['pollform'] = PollForm()
		context['form'] = CreatePostForm()
		return render(request, 'NewPoll.html', context)

	form = CreatePostForm(request.POST)
	pollform = PollForm(request.POST)

	if not form.is_valid() or not pollform.is_valid():
		context ['form'] = form
		context ['pollform'] = pollform
		return render(request, 'NewPoll.html', context)

	# check poll choices
	choices = []
	for i in range(1,11):
		key = 'choice' + str(i)
		if key not in request.POST:
			break 
		else:
			if len(request.POST[key]) == 0:
				context ['form'] = form
				context ['pollform'] = pollform
				return render(request, 'NewPoll.html', context)
			else:
				choices.append(request.POST[key])


	new_topic = Topic(user=request.user, forum=forum, title=form.cleaned_data['post_title'])
	new_topic.save()
	tag = get_object_or_404(Tag, name='vote')
	new_topic.tags.add(tag)
	new_topic.save()

	new_post = Post(text=form.cleaned_data['post_body'], user=request.user, topic=new_topic)
	new_post.save()

	new_poll = Poll(topic=new_topic,question=pollform.cleaned_data['question'],is_multiple=pollform.cleaned_data['is_multiple'])
	new_poll.save()

	for choice in choices:
		new_choice = Choice(poll=new_poll, choice=choice)
		new_choice.save()

	# save images
	if request.FILES:
		save_post_images(request, new_post)#, request.FILES.getlist('up_image_list'))
	return redirect(reverse('in_forum', kwargs={"forum_name":forum_name}))

@login_required
@transaction.atomic
def create_event(request, forum_name):
	context = {}
	context['logged_in'] = True
	forum = get_object_or_404(Forum, name=forum_name)
	context['forum'] = forum
	if request.method == 'GET':
		context['form'] = EventForm()
		return render(request, 'create_event.html', context)

	form = EventForm(request.POST, user=request.user, forum=forum)

	if not form.is_valid():
		context ['form'] = form
		return render(request, 'create_event.html', context)
	new_event = form.save()
	new_event.topic.user = request.user
	new_event.topic.forum = forum
	new_event.save()
	return redirect(reverse('in_forum', kwargs={"forum_name":forum_name})+ "?filter_tag=Event")

@login_required
@transaction.atomic
def edit_event(request, topic_id):
	event = get_object_or_404(Event, topic_id__exact=topic_id)
	if event.topic.user.username != request.user.username:
		raise PermissionDenied()
	context = {}
	context['logged_in'] = True
	context['topic_id'] = topic_id
	context['participants'] = event.participants.all()
	if request.method == 'GET':
		context ['form'] = EventForm(event=event)
		context['participant_form'] = ParticipantForm(event=event)
		return render(request, 'edit_event.html', context)

	form = EventForm(request.POST,event=event)

	if not form.is_valid():
		context ['form'] = form
		return render(request, 'edit_event.html', context)
	form.save()
	# TODO(linxi): update/add post within the topic
	return redirect(reverse('in_topic', kwargs={'topic_id':topic_id}))

@transaction.atomic
def load_events(request, forum_name):
	forum = get_object_or_404(Forum, name=forum_name)
	events = Event.objects.filter(topic__forum=forum).filter(time_period__end__gte=datetime.date.today)
	return render(request, 'events.json', {"events":events}, content_type="application/json")


@login_required
@transaction.atomic
def delete_topic(request, forum_name, topic_id, page_num, filter_tag):
	topic = get_object_or_404(Topic, id=topic_id)
	posts = Post.objects.filter(topic=topic)
	post_images = PostImage.objects.filter(post__in=posts)  # TODO: delete real files on disk
	post_images.delete()
	posts.delete()
	topic.delete()
	url = reverse('in_forum', kwargs={"forum_name":forum_name}) + '?page='+page_num+'&filter_tag='+filter_tag
	return redirect(url)


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

	return redirect(url)



def display_search_results(topic_list, context, request):
	topic_list = topic_list.order_by("-created_on")
	context["num_results"] = topic_list.count()
	context['topics'] = topic_list



def search_topic(request, forum_name=None):
	context = {}
	form = SearchKeyForm(request.POST)

	if not form.is_valid():
		if forum_name == None:
			return redirect(reverse('cmu_home'))
		else:
			return redirect(reverse('sub_forum', kwargs={'father_forum_name':forum_name}))
	key_word = form.cleaned_data['key_words']

	context['logged_in'] = check_login(request.user)
	context['key_word'] = key_word
	tag = 'title'
	if 'tag' in request.POST and len(request.POST['tag']) != 0:
		tag = request.POST['tag']
	context['tag'] = tag
	
	topic_list = SearchTopicList(tag, key_word, forum_name, context)
	display_search_results(topic_list, context, request)
	return render(request,'SearchResults.html',context)


def SearchTopicList(tag, key_word, forum_name, context):
	topic_list = Topic.objects.all()
	if tag == 'author':
		topic_list = filter_by_author(topic_list, key_word)

	else:
		topic_list = filter_by_title(topic_list, key_word)

	topics = []
	if forum_name != None:
		forum = get_object_or_404(Forum, name=forum_name)
		context['forum'] = forum
		topics = topic_list.filter(forum=forum)
		sub_forums = Forum.objects.filter(father_forum=forum)
		topics |= topic_list.filter(forum__in=sub_forums)
	else:
		topics = topic_list
	return topics



def back_to_forum(request, forum_id):
	try:
	  forum = Forum.objects.get(id__exact=forum_id)
	  return redirect(reverse('sub_forum', kwargs={'father_forum_name': forum.name}))
	except ObjectDoesNotExist:
		return redirect(reverse('cmu_home'))



@login_required
def advanced_search(request, forum_id):
	context = {}
	context['logged_in'] = check_login(request.user)
	context['entry_forum'] = forum_id
	if request.method == 'GET':
		context['form'] = AdvancedSearchForm()
		context['forums'] = Forum.objects.filter(father_forum__exact=None).exclude(name="Secret Words")
		context['tags'] = Tag.objects.all()
		return render(request,'AdvancedSearch.html',context)

	
	form = AdvancedSearchForm(request.POST)
	context['form'] = form
	if not form.is_valid():
		return redirect(reverse('advanced_search'))

	context['advanced'] = True
	
	topic_list = AdvancedSearchTopicList(form, request)
	display_search_results(topic_list, context, request)
	
	return render(request,'SearchResults.html',context)




def AdvancedSearchTopicList(form, request):
	topic_list = Topic.objects.all()
	start_date = form.cleaned_data['start_date']
	if start_date:
		topic_list = topic_list.filter(created_on__gte=start_date)

	end_date = form.cleaned_data['end_date']
	if end_date:
		topic_list = topic_list.filter(created_on__lte=end_date)

	sel_forums = request.POST.getlist('optionsForums')
	if sel_forums:
		forums = Forum.objects.filter(id__in=sel_forums)
		forums |= Forum.objects.filter(father_forum__in=forums)
	else:
		forums = Forum.objects.all().exclude(name="Secret Words")
	topic_list = topic_list.filter(forum__in=forums)
	
	sel_tags = request.POST.getlist('optionsTags')
	if sel_tags:
		tags = Tag.objects.filter(id__in=sel_tags)
		topic_list = topic_list.filter(tags__in=tags)

	if form.cleaned_data['author']:
		topic_list = filter_by_author(topic_list, form.cleaned_data['author'])
	if form.cleaned_data['title']:
		topic_list = filter_by_title(topic_list, form.cleaned_data['title'])
	if form.cleaned_data['content']:
		topic_list = filter_by_content(topic_list, form.cleaned_data['content'])
	return topic_list


def filter_by_author(topic_list, author):
	author = User.objects.filter(username__icontains=author)
	return topic_list.filter(user__in=author)

def filter_by_title(topic_list, title_words):
	title_word_list = '|'.join(title_words.split()) + '|'+title_words
	return topic_list.filter(Q(title__iregex=r'\b'+title_word_list+r'\b'))

def filter_by_content(topic_list, content_words):
	content_word_list = '|'.join(content_words.split()) + '|'+content_words
	post_list = Post.objects.filter(Q(text__iregex=r'\b'+content_word_list+r'\b'))
	return topic_list.filter(post__in=post_list)

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






