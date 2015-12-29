from utils import *

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
		context['favorite'] = check_favourite(request.user, father_forum)
	else:
		return redirect(reverse('in_forum',kwargs={'forum_name':father_forum_name}))

	return render(request, 'SubForum.html', context)

def in_forum(request, forum_name):
	forum = None
	context = {'forum_name':forum_name}
	forum = get_object_or_404(Forum, name=forum_name)
	if check_login(request.user):
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
	
	topic_list = Topic.objects.filter(forum__exact=forum).order_by('-upped', '-last_reply_on')

	if filter_tag != None:
		if filter_tag == 'good':
			topic_list = topic_list.filter(good_topic=True)
		elif filter_tag == 'images':
			context['images'] = PostImage.objects.filter(forum=forum)
			return render(request, 'ImageGallery.html', context)
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

	context['favorite'] = check_favourite(request.user, forum)
	return render(request, 'InForum.html', context)

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
def delete_topic(request, forum_name, topic_id, page_num, filter_tag):
	topic = get_object_or_404(Topic, id=topic_id)
	posts = Post.objects.filter(topic=topic)
	post_images = PostImage.objects.filter(post__in=posts)  # TODO: delete real files on disk
	post_images.delete()
	posts.delete()
	topic.delete()
	#url = reverse('in_forum', kwargs={"forum_name":forum_name}) + '?page='+page_num+'&filter_tag='+filter_tag
	#return redirect(url)
	return HttpResponse()




