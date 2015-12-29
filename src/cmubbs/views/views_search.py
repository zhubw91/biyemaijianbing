from utils import *

def display_search_results(topic_list, context, request, next=True):
	if next:
		topic_list = topic_list.order_by("-created_on")

		paginator = Paginator(topic_list, 10)
		
		if 'goto_page' in request.POST:
			page = request.POST['goto_page']
		elif 'page_num' in request.POST:
			page = request.POST['page_num']
		else:
			page = 1
		
		if page != None and int(page) == -1:
			page = paginator.num_pages

		topics = getPageContent(paginator, page)
		context['topic_pages'] = [None]*paginator.num_pages
		if page != None:
			context['topic_pages'][int(page)-1] = 1
	else:
		topics = topic_list

	context["num_results"] = topic_list.count()
	context['topics'] = topics



@login_required
def search_topic(request, forum_name=None):
	context = {}
	re_form = SearchKeyForm(request.POST)

	if not re_form.is_valid():
		if forum_name == None:
			return redirect(reverse('cmu_home'))
		else:
			return redirect(reverse('sub_forum', kwargs={'father_forum_name':forum_name}))
	key_words = re_form.cleaned_data['key_words']

	context['key_words'] = key_words
	tag = 'title'
	if 'tag' in request.POST and len(request.POST['tag']) != 0:
		tag = request.POST['tag']
	context['tag'] = tag
	context['tags'] = ['title','author']
	context['form'] = SearchKeyForm()

	topic_list = SearchTopicList(tag, key_words, forum_name, context)
	display_search_results(topic_list, context, request)
	return render(request,'search/SearchResults.html',context)

def filter_by_author(topic_list, author):
	author = User.objects.filter(username__icontains=author)
	return topic_list.filter(user__in=author)

def filter_by_title(topic_list, title_words):
	title_word_list = title_words.split()
	re_topics = topic_list.filter(title__icontains=title_words)
	for word in title_word_list:
		re_topics |= topic_list.filter(title__icontains=word)
	return re_topics

def filter_by_content(topic_list, content_words):
	content_word_list = content_words.split()
	post_list = Post.objects.filter(text__icontains=content_words)
	for word in content_words:
		post_list |= Post.objects.filter(text__icontains=word)
	return topic_list.filter(post__in=post_list)

def SearchTopicList(tag, key_word, forum_name, context):
	secret_forum = Forum.objects.filter(name="Secret Words")
	forums = Forum.objects.all().exclude(name="Secret Words").exclude(father_forum__in=secret_forum)
	topic_list = Topic.objects.filter(forum__in=forums)
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

@login_required
def advanced_search(request, forum_id):
	context = {}
	context['entry_forum'] = forum_id

	if request.method == 'GET':
		context['form'] = AdvancedSearchForm()
		context['forums'] = Forum.objects.filter(father_forum__exact=None).exclude(name="Secret Words")
		context['tags'] = Tag.objects.all()
		return render(request,'search/AdvancedSearch.html',context)

	
	form = AdvancedSearchForm(request.POST)
	
	if not form.is_valid():
		context['form'] = form
		context['forums'] = Forum.objects.filter(father_forum__exact=None).exclude(name="Secret Words")
		context['tags'] = Tag.objects.all()
		return render(request,'search/AdvancedSearch.html',context)

	context['advanced'] = True
	topic_list = AdvancedSearchTopicList(form, request)
	display_search_results(topic_list, context, request, False)
	context['tags'] = ['title','author']
	context['form'] = SearchKeyForm()
	return render(request,'search/SearchResults.html',context)

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
		secret_forum = Forum.objects.filter(name="Secret Words")
		forums = Forum.objects.all().exclude(name="Secret Words").exclude(father_forum__in=secret_forum)
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
