from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.shortcuts import get_object_or_404
from datetime import date,timedelta
import datetime
import time
from django.utils import timezone



class Forum(models.Model):
	name = models.CharField(max_length=100, unique=True)
	description = models.CharField(max_length=500)
	moderators = models.ManyToManyField('UserInfo', related_name='manages')
	father_forum = models.ForeignKey('self', null=True, related_name='sub_forum')

	@property 
	def num_threads(self):
		cur_date = time.strftime('%Y-%m-%d')
		num_threads = 0
		sub_forums = Forum.objects.filter(father_forum__exact=self)
		if not sub_forums:
			num_threads = Topic.objects.filter(forum__exact=self).filter(created_on__range=[cur_date+' 00:00:00',cur_date+' 23:59:59']).count()
		else:
			num_threads = sum(f.num_threads for f in sub_forums)
		return num_threads

	@property 
	def moderator_list(self):
		return self.moderators.all()

	@property 
	def secret(self):
		secret_forum = get_object_or_404(Forum, name="Secret Words")
		if self == secret_forum:
			return True
		elif self.father_forum == secret_forum:
			return True
		else:
			return False

class Topic(models.Model):
	user = models.ForeignKey(User, related_name="has_post")
	forum = models.ForeignKey(Forum)
	view_count = models.IntegerField(default=0)
	like_count = models.IntegerField(default=0)
	tags = models.ManyToManyField('Tag')
	title = models.CharField(max_length=50, default="", blank=True)
	created_on = models.DateTimeField(auto_now_add=True, editable=False)
	last_reply_on = models.DateTimeField(auto_now_add=True, editable=True)
	liked = models.ManyToManyField(User, related_name="like")
	upped = models.BooleanField(default=False)
	good_topic = models.BooleanField(default=False)

	@property 
	def like_count(self):
		return self.liked.all().count()

	@property
	def score(self):
		score = self.view_count + self.comments + self.like_count # demo algo, will be replaced later
		return score

	@property 
	def tag_list(self):
		return self.tags.all()

	@property 
	def last_reply(self):
		posts = Post.objects.filter(topic__exact=self)
		if len(posts) == 0:
			return ''
		else:
			return posts.order_by('-created_on')[0].user.username

	@property  
	def comments(self):
		if self.tag_list.filter(name__iexact='Event'):
			return Post.objects.filter(topic__exact=self).count()
		else:
			return Post.objects.filter(topic__exact=self).count()-1
	
	@property 
	def new_topic(self):
		if Post.objects.filter(topic__exact=self).count() == 1:
			return True
		else:
			return None

	@property 
	def has_image(self):
		if Post.objects.filter(topic=self).order_by('created_on').exists():
			topic_post = Post.objects.filter(topic=self).order_by('created_on')[0]
			if topic_post:
				return topic_post.post_image_list
		return False

	@property
	def get_time_create(self):
		now = datetime.datetime.now()
		delta = now.date() - self.created_on.date()
		result = str(delta.days) + ' days ago'
		return result

	@property
	def get_time_lastreply(self):
		now = timezone.now()
		print now
		delta = now.date() - self.last_reply_on.date()
		result = str(delta.days) + ' days ago'
		if delta.days == 1:
			result = '1 day ago'
		if delta.days <= 0:
			delta = now.time().hour - self.last_reply_on.time().hour
			result = str(delta) + ' hours ago'
			if delta == 1:
				result = '1 hour ago'
			if delta <= 0:
				delta = now.time().minute - self.last_reply_on.time().minute
				if delta <= 0:
					result = 'Just Now'
				elif delta == 1:
					result = '1 minute ago'
				else:
					result = str(delta) + ' minutes ago'
		elif delta.days >= 15:
			result = self.last_reply_on.strftime("%b %d, %Y")
		return result

	@property 
	def topic_preview(self):
		if self.tag_list.filter(name__iexact='Event'):
			return self.event.description
		else:
			return self.post.order_by('created_on')[0].text

class TopicView(models.Model):
	topic = models.ForeignKey(Topic)
	session = models.CharField(max_length=40)
	created_on = models.DateTimeField(auto_now_add=True)

class Tag(models.Model):
	name = models.CharField(max_length=100)

class Post(models.Model):
	text = models.CharField(max_length=1000)
	created_on = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User)
	topic = models.ForeignKey(Topic, related_name='post')
	reply_to = models.ForeignKey('self', null=True, related_name='reply_by')
	plain_text = models.BooleanField(default=False)

	@property 
	def user_image(self):
		return UserInfo.objects.get(user__exact=self.user).image.url

	@property 
	def post_image_list(self):
		return self.post_images.all()

	@property 
	def sub_post_list(self):
		return self.sub_post.all()

class PostImage(models.Model):
	forum = models.ForeignKey(Forum, related_name="forum_images")
	post = models.ForeignKey(Post, related_name='post_images')
	image = models.ImageField(upload_to = 'images/', blank=True)

class SubPost(models.Model):
	text = models.CharField(max_length=1000)
	created_on = models.DateTimeField(auto_now_add=True)
	father_post = models.ForeignKey(Post, related_name='sub_post')


@receiver(post_delete, sender=PostImage)
def postImage_delete(sender, instance, **kwargs):
    instance.image.delete(save=False)

class Message(models.Model):
	text = models.CharField(max_length=500)
	created_on = models.DateTimeField(auto_now_add=True)
	sender = models.ForeignKey(User,related_name='sender')
	receiver = models.ForeignKey(User,related_name='receiver')
	is_read = models.BooleanField(default=False)

class UserInfo(models.Model):
	GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
	user = models.OneToOneField(User)
	gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
	bio = models.CharField(max_length=420, blank=True)
	user_group = models.IntegerField(default=3)
	follows = models.ManyToManyField('UserInfo', related_name='followed_by', blank=True)
	favorite_forums = models.ManyToManyField('Forum', related_name='favorited_by', blank=True)
	image = models.ImageField(upload_to = 'images/', blank=True)
	birth = models.DateField(null=True, blank=True)

	@property 
	def age(self):
		age = 0
		if self.birth != None:
			age = date.today().year-self.birth.year
		return age

	@property
	def num_follows(self):
		return len(self.follows.all()[:])

	@property
	def num_followers(self):
		return len(self.followed_by.all()[:])


class Event(models.Model):
	topic = models.OneToOneField(Topic, related_name="event")
	description = models.CharField(max_length=500, blank=True)
	public = models.BooleanField(default=False)
	participants = models.ManyToManyField('UserInfo', related_name='participating_events', blank=True)
	max_participants = models.IntegerField(default=1)

class EventApplication(models.Model):
	event = models.ForeignKey(Event, related_name="application")
	message =  models.CharField(max_length=500, blank=True)
	applicant = models.ForeignKey(User,related_name='event_application',blank=True)
	created_on = models.DateTimeField(auto_now_add=True)

class Location(models.Model):
	event = models.OneToOneField(Event, related_name='location')
	lat = models.FloatField()
	lng = models.FloatField()
	formatted_address = models.CharField(max_length=500, default="", blank=True)

class TimePeriod(models.Model):
	event = models.OneToOneField(Event, related_name='time_period')
	start = models.DateTimeField(auto_now_add=False, editable=True)
	end = models.DateTimeField(auto_now_add=False, editable=True)

class Poll(models.Model):
	question = models.CharField(max_length=200)
	topic = models.OneToOneField(Topic, related_name='poll')
	is_multiple = models.BooleanField(default=False)
	polled_by = models.ManyToManyField('UserInfo',related_name='polled',blank=True)

class Choice(models.Model):
	poll = models.ForeignKey(Poll, related_name='choices')
	choice = models.CharField(max_length=200)
	votes = models.IntegerField(default=0)

class Notification(models.Model):
	user = models.ForeignKey(User, related_name='notifications')
	# reply, follow, event
	notification_type = models.CharField(max_length=100)
	# username, topic id, event id
	key = models.CharField(max_length=100)
	created_on = models.DateTimeField(auto_now_add=True)

class Broadcast(models.Model):
	text = models.CharField(max_length=2000)



	
	