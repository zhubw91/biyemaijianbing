
from utils import *

def intro(request):
	if check_login(request.user):
		if 'next' in request.GET and request.GET['next']:
			return redirect(request.GET['next'])
		return redirect(reverse('cmu_home'))
	return render(request, 'intro.html', {})

def home(request):
	context={}
	if check_login(request.user):
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

	
	context['broadcast'] = None
	if len(Broadcast.objects.all()) > 0:
		broadcast = Broadcast.objects.all()[0]
		if request.method == 'POST':
			broadcastform = BroadcastForm(request.POST)
			if broadcastform.is_valid():
				broadcast.text = broadcastform.cleaned_data['text']
				broadcast.save()
		else:
			broadcastform = BroadcastForm(initial={'text':broadcast.text})
		context['broadcast'] = broadcast
	context['broadcastform'] = broadcastform
	return render(request, 'HomePage.html', context)


def hot_topics(request):
	context = {}
	#cur_date = time.strftime("%Y-%m-%d") # hot topics within one day
	# hot topics within two days
	cur_date = datetime.date.today().strftime("%Y-%m-%d")
	yes_date = (datetime.date.today()-timedelta(days=1)).strftime("%Y-%m-%d")

	cur_topics = Topic.objects.filter(created_on__range=[yes_date+' 00:00:00',cur_date+' 23:59:59']).order_by("-created_on")
	hot_topics = sorted(cur_topics,  key=lambda t: t.score, reverse=True)[:10]
	context['topics'] =  hot_topics
	return render(request, 'HotTopics.html',context)

def back_to_forum(request, forum_id):
	try:
	  forum = Forum.objects.get(id__exact=forum_id)
	  return redirect(reverse('sub_forum', kwargs={'father_forum_name': forum.name}))
	except ObjectDoesNotExist:
		return redirect(reverse('cmu_home'))




