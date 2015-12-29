from mimetypes import guess_type
from utils import *
import datetime

def user_profile(request, user_name=None):
	if not user_name:
		user_name = request.user.username
	context = {}
	try:
		user_to_show = User.objects.get(username=user_name)
	except ObjectDoesNotExist:
		raise Http404("No such user!")
	context['user_info'] = UserInfo.objects.get(user=user_to_show)
	context['if_self'] = False
	if check_login(request.user):
		login_user_info = UserInfo.objects.get(user=request.user)
		context['user_follows'] = login_user_info.follows.all()
		context['user_followers'] = login_user_info.followed_by.all()
		if user_to_show == request.user:
			context['if_self'] = True
	return render(request, 'profile/UserProfile.html', context)

def get_user_info(request, user_name):
	user_to_show = get_object_or_404(User, username__exact=user_name)
	context = {}
	context['user_info'] = user_to_show.userinfo
	return render(request, 'profile/user_info.json', context, content_type="application/json")

@login_required
@transaction.atomic
def edit_profile(request):
	context = {}
	user_info = get_object_or_404(UserInfo, user=request.user)
	context ['user_info'] = user_info
	if request.method == 'GET':
		user_form = UserForm(instance=request.user)
		userinfo_form = UserInfoForm(instance=user_info)
		userimg_form = UserImgForm(instance=user_info)
		context ['user_form'] = user_form
		context['userimg_form'] = userimg_form
		context ['userinfo_form'] = userinfo_form
		return render(request, 'profile/edit_profile.json', context, content_type="application/json")

	user_form = UserForm(request.POST, instance=request.user)
	userinfo_form = UserInfoForm(request.POST, instance=user_info)

	if (not user_form.is_valid()) or (not userinfo_form.is_valid()):
		context ['user_form'] = user_form
		context ['userinfo_form'] = userinfo_form
		return render(request, 'profile/edit_profile.json', context, content_type="application/json")

	user_form.save()
	userinfo_form.save()
	return render(request, 'profile/edit_profile.json', context, content_type="application/json")
	

@login_required 
@transaction.atomic
def upload_usr_image(request):
	if request.method == 'GET':
		return redirect(reverse('user_profile', kwargs={'user_name':request.user.username}))

	user_info = get_object_or_404(UserInfo, user=request.user)
	userimg_form = UserImgForm(request.POST, request.FILES, instance = user_info)
	if not userimg_form.is_valid():
		return redirect(reverse('user_profile', kwargs={'user_name':request.user.username}))
	userimg_form.save()
	return redirect(reverse('user_profile', kwargs={'user_name':request.user.username}))

@login_required
def collections(request):
	context = {}
	context['favorite_topics'] = request.user.like.all()
	return render(request, 'profile/collections.json', context, content_type="application/json")


def activities(request, user_name):
	context = {}
	activities = {}
	activities_self = {}

	# self activities no login requirement
	view_user = get_object_or_404(User, username=user_name)
	self_topics = view_user.has_post.all()
	for topic in self_topics:
		if topic.forum.secret:
			continue
		t = topic.created_on.date()
		if t not in activities_self:
			activities_self[t] = []
		activities_self[t].append(('topic', view_user, topic))
	events_self = view_user.userinfo.participating_events.all()
	for event in events_self:
		t = event.time_period.start.date()
		if t not in activities_self:
			activities_self[t] = []
		activities_self[t].append(('event', view_user, event))

	act_list = [(t, activities_self[t]) for t in activities_self]
	act_list.sort(reverse=True)
	context['activities_self'] = act_list
	context['is_self'] = False

	# activities for followings, login required
	if check_login(request.user) and request.user == view_user:
		context['is_self'] = True
		user_info = UserInfo.objects.get(user=request.user)
		follows = user_info.follows.all()
		for person in follows:
			# get all topics that the person post
			topics = person.user.has_post.all()
			for topic in topics:
				t = topic.created_on.date()
				if t not in activities:
					activities[t] = []
				activities[t].append(('topic', person, topic))
			# get all event that the person will attend
			events = person.user.userinfo.participating_events.all()
			for event in events:
				t = event.time_period.start.date()
				if t not in activities:
					activities[t] = []
				activities[t].append(('event', person, event))
		act_list = [(t, activities[t]) for t in activities]
		act_list.sort(reverse=True)
		context['activities'] = act_list

	

	return render(request, 'profile/activities.json', context, content_type="application/json")

def self_topics(request, user_name):
	user = get_object_or_404(User, username=user_name)
	context = {}
	context['favorite_topics'] = user.has_post.all()
	context['title'] = 'Topics that ' + user_name + ' has posted are'
	return render(request, 'profile/collections.json', context, content_type="application/json")


def get_profile_photo(request, userid):
	user = get_object_or_404(User, username=userid)
	user_info = get_object_or_404(UserInfo, user=user)
	if not user_info.image:
		return HttpResponse(open(settings.DEFAULT_PROFILE_IMG).read(), content_type='image/jpeg')
		#raise Http404  
	content_type = guess_type(user_info.image.name)
	return HttpResponse(user_info.image, content_type=content_type)

@login_required
def follow(request, user_name):
	friend_user = get_object_or_404(User, username=user_name)
	if check_login(request.user):	
		friend_info = get_object_or_404(UserInfo, user=friend_user)
		user_info = get_object_or_404(UserInfo, user=request.user)
		if friend_info not in user_info.follows.all()[:]:
			user_info.follows.add(friend_info)
			user_info.save()
		# add the notification (make sure no duplications)
		if not Notification.objects.filter(user=friend_user).filter(notification_type='follow').filter(key=request.user.username).exists():
			new_notification = Notification(user=friend_user, notification_type='follow', key=request.user.username)
			new_notification.save()
	return HttpResponse()

@login_required
def unfollow(request, user_name):
	friend_user = get_object_or_404(User, username=user_name)
	if check_login(request.user):	
		friend_info = get_object_or_404(UserInfo, user=friend_user)
		user_info = get_object_or_404(UserInfo, user=request.user)
		if friend_info in user_info.follows.all()[:]:
			user_info.follows.remove(friend_info)
			user_info.save()
	return HttpResponse()

def show_follow(request, username, type_id):
	context = {}
	user_to_show = get_object_or_404(User, username=username)
	user_to_show_info = get_object_or_404(UserInfo, user=user_to_show)
	if type_id == '0':
		context['follow_to_show'] = user_to_show_info.follows.all()
	else:
		context['follow_to_show'] = user_to_show_info.followed_by.all()
	return render(request, 'profile/follow.json', context, content_type="application/json")




