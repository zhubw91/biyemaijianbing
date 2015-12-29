from django.db import models

from django.contrib.auth.models import User

class Forum(models.Model):
	name = models.CharField(max_length=100)
	description = models.CharField(max_length=500)

class ForumModerator(models.Model):
	forum = models.ForeignKey(Forum)
	user = models.ForeignKey(User)

class Thread(models.Model):
	user = models.ForeignKey(User)
	forum = models.ForeignKey(Forum)
	view_count = models.IntegerField(default=0)
	like_count = models.IntegerField(default=0)
	dislike_count = models.IntegerField(default=0)
	tags = ManyToManyField('Tag')

class Post(models.Model):
	text = models.CharField(max_length=1000)
	created_on = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User)
	thread = models.ForeignKey(Thread)
	reply_to = models.ManyToManyField('Post', related_name='reply_by')


class UserInfo(models.Model):
	user = models.OneToOneField(User)
	gender = models.IntegerField(default=0)
	bio = models.CharField(max_length=420)
	user_group = models.IntegerField(default=0)
	age = models.IntegerField(default=0)
	follows = models.ManyToManyField('UserInfo', related_name='followed_by')
	email = models.CharField(max_length=200,default="")
	
class Tag(models.Model):
	name = models.CharField(max_length=100)

class Event(models.Model):
	name = models.CharField(max_length=100)
	description = models.CharField(max_length=1000)
	start_time = models.DateTimeField()
	end_time = models.DateTimeField()
	# Desired number of attendance
	attend_num = models.IntegerField(default=0)
	create_user = models.ForeignKey(User)
	poly = models.PolygonField()
	objects = models.GeoManager()
	participants = models.ManyToManyField('User', RELATED_NAME='participates')


class VoteQuestion(models.Model):
	name = models.CharField(max_length=100)
	description = models.CharField(max_length=1000) 

class VoteChoice(models.Model):
	vote_question = models.ForeignKey(VoteQuestion)
	choice_text = models.CharField(max_length=400)
	votes = models.IntegerField(default=0)



