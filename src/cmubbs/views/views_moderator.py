
from utils import *

@login_required
def manage_forums(request):
	context = {}
	if request.user.userinfo.user_group == 0:
		context['father_forum_set'] = Forum.objects.all().filter(father_forum__exact=None)
	context['my_father_forums'] = request.user.userinfo.manages.filter(father_forum__exact=None)
	context['my_sub_forums'] = request.user.userinfo.manages.exclude(father_forum__exact=None)
	return render(request, 'moderator/manage_forums.html', context)

@login_required
def add_sub_forum(request, father_forum_name):
	context = {}	
	father_forum = get_object_or_404(Forum, name__exact=father_forum_name)
	if father_forum.father_forum: # not a father forum
		raise Http404();
	context ['father_forum_name'] = father_forum_name
	if not request.user.userinfo.manages.filter(name__exact=father_forum_name).exists():
		raise PermissionDenied()
	
	if request.method == 'GET':
		context ['form'] = ForumForm()
		return render(request, 'moderator/add_sub_forum.html', context)

	form = ForumForm(request.POST)

	if not form.is_valid():
		context ['form'] = form
		return render(request, 'moderator/add_sub_forum.html', context)
	new_forum = form.save(commit=False)
	new_forum.father_forum = father_forum
	new_forum.save()
	return redirect(reverse('manage_forums'))

@login_required
def add_father_forum(request):
	context = {}
	if request.user.userinfo.user_group > 0:
		raise PermissionDenied()
	
	if request.method == 'GET':
		context ['form'] = ForumForm()
		return render(request, 'moderator/add_father_forum.html', context)

	form = ForumForm(request.POST)

	if not form.is_valid():
		context ['form'] = form
		return render(request, 'moderator/add_father_forum.html', context)
	form.save()
	return redirect(reverse('manage_forums'))

@login_required
def edit_forum(request, forum_name):
	
	forum = get_object_or_404(Forum, name=forum_name)
	if not check_edit_permission(request.user, forum):
		raise PermissionDenied()
	context = {}
	context ['forum_name'] = forum_name
	context['moderators'] = forum.moderators.all()
	context['delete_permission'] = check_delete_permission(request.user, forum)
	context ['moderator_form'] = ModeratorForm(forum_name=forum_name)
	if request.method == 'GET':
		context ['form'] = ForumForm(instance=forum)
		return render(request, 'moderator/edit_forum.html', context)

	form = ForumForm(request.POST,instance=forum)

	if not form.is_valid():
		context ['form'] = form
		return render(request, 'moderator/edit_forum.html', context)
	form.save()
	return redirect(reverse('manage_forums'))


@login_required
def delete_forum(request, forum_name):
	context = {}
	forum = get_object_or_404(Forum, name=forum_name)
	if not check_delete_permission(request.user, forum):
		raise PermissionDenied()
	if not forum.father_forum:
		for sub_forum in forum.sub_forum.all():
			sub_forum.delete()
	forum.delete()
	return redirect(reverse('manage_forums'))

@login_required
def edit_moderator(request, forum_name):
	if request.method == 'POST':
		forum = get_object_or_404(Forum, name=forum_name)
		if not check_edit_permission(request.user, forum):
			raise PermissionDenied()

		context = {}
		context ['forum_name'] = forum_name
		context['moderators'] = forum.moderators.all()
		context['delete_permission'] = check_delete_permission(request.user, forum)

		form = ModeratorForm(request.POST, forum_name=forum_name)
		if not form.is_valid():
			context ['moderator_form'] = form
			context ['form'] = ForumForm(instance=forum)
			return render(request, 'moderator/edit_forum.html', context)

		new_moderator = get_object_or_404(User, username=form.cleaned_data['username'])
		forum.moderators.add(new_moderator.userinfo)
		forum.save()
		update_user_group(new_moderator.userinfo)
		# add notifications for new moderator
		if not Notification.objects.filter(user=new_moderator).filter(notification_type='moderator-add').filter(key=forum.id).exists():
			new_notification = Notification(user=new_moderator, notification_type='moderator-add', key=forum.id)
			new_notification.save()
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
	# add notifications for new moderator
	if not Notification.objects.filter(user=moderator).filter(notification_type='moderator-remove').filter(key=forum.id).exists():
		new_notification = Notification(user=moderator, notification_type='moderator-remove', key=forum.id)
		new_notification.save()
	return redirect(reverse('edit_forum', kwargs={"forum_name":forum_name}))


