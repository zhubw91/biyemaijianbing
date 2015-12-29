from mimetypes import guess_type
from utils import *

@login_required
@transaction.atomic
def new_post(request, forum_name):
	context = {}
	forum = get_object_or_404(Forum, name=forum_name)

	tags = Tag.objects.exclude(name__in=['Event','Vote'])
	context['forum'] = forum
	context['tags'] = tags

	if request.method == 'GET':
		context['form'] = CreatePostForm()
		return render(request, 'newpost/NewPost.html', context)

	if request.FILES:
		form = CreatePostForm(request.POST, description_required=False)
	else:
		form = CreatePostForm(request.POST)
		

	if not form.is_valid():
		context ['form'] = form
		return render(request, 'newpost/NewPost.html', context)

	new_topic = Topic(user=request.user, forum=forum, title=form.cleaned_data['post_title'])
	new_topic.save()
	if 'tag' in request.POST and len(request.POST['tag']) != 0:
		tag = get_object_or_404(Tag, name=request.POST['tag'])
		new_topic.tags.add(tag)
	new_topic.save()

	new_post = Post(text=form.cleaned_data['post_body'], user=request.user, topic=new_topic, plain_text=form.cleaned_data['plain_text'])
	new_post.save()

	# save images
	if request.FILES:
		save_post_images(request, new_post)
	return redirect(reverse('in_forum', kwargs={"forum_name":forum_name}))


@login_required
@transaction.atomic
def save_post_images(request, post):
	for up_image in request.FILES.getlist('up_image_list'):
		new_post_image = PostImage(post=post, forum = post.topic.forum)
		new_post_image.save()
		new_post_image.image.save(up_image.name,up_image)


def post_images(request, image_id):
	try:
	  post_image = PostImage.objects.get(id__exact=image_id)
	except ObjectDoesNotExist:
		return HttpResponse(open(settings.DEFAULT_POST_IMG).read(), content_type='image/jpeg')

	content_type = guess_type(post_image.image.name) 
	return HttpResponse(post_image.image, content_type=content_type)

MAX_CHOICES = 10
INIT_CHOICE_CNT = 2

@login_required
@transaction.atomic
def new_poll(request, forum_name):
	context = {}
	forum = get_object_or_404(Forum, name=forum_name)
	tags = Tag.objects.exclude(name__exact='Event')
	context['forum'] = forum
	context['tags'] = tags

	if request.method == 'GET':
		context['pollform'] = PollForm()
		context['form'] = CreatePostForm()
		context['choices'] = []
		for i in range(1, 1 + INIT_CHOICE_CNT):
			context['choices'].append({'name':'choice'+str(i),'value':''})
		return render(request, 'newpost/NewPoll.html', context)

	form = CreatePostForm(request.POST, description_required=False)
	pollform = PollForm(request.POST)

	# choices validation
	choices = []
	context['choices'] = []
	
	for i in range(1, 1 + MAX_CHOICES):
		key = 'choice' + str(i)
		if i > INIT_CHOICE_CNT:
			removable = True
		else:
			removable = False
		if key not in request.POST:
			continue 
		else:
			context['choices'].append({'name':key, 'value':request.POST[key], 'removable':removable})
			if len(request.POST[key]) == 0:
				context ['pollerror'] = "The choices can not be empty."
			else:
				choices.append(request.POST[key])

	if not form.is_valid() or not pollform.is_valid() or 'pollerror' in context:
		context ['form'] = form
		context ['pollform'] = pollform
		return render(request, 'newpost/NewPoll.html', context)

	new_topic = Topic(user=request.user, forum=forum, title=form.cleaned_data['post_title'])
	new_topic.save()
	tag = get_object_or_404(Tag, name='Vote')
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
def preview_post(request):
	if request.method == 'GET':
		return JsonResponse({'info':"wrong entry"})
	post_text = request.POST['post_text']
	post_text = clean_font_tag(post_text)
	return JsonResponse({'post_text':post_text})



