import datetime

from cmubbs.forms import *
from cmubbs.models import *
from django.forms import formset_factory

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

def check_login(user):
	if user is not None:
		if user.is_active:
			return True
	return False

def check_favourite(user, forum, context):
	context['logged_in'] = check_login(user)
	if context['logged_in']:
		if forum.favorited_by.filter(user__exact=user).exists():
			context['favorite'] = True
		else:
			context['favorite'] = False

def check_like(user, topic):
	if user.like.filter(title=topic.title).exists():
		return True
	return False

def check_topic_permission(user, topic):
	forum = topic.forum
	return check_edit_permission(user, forum)

def getPageContent(paginator,page):
	content = None
	try:
		content = paginator.page(page)
	except PageNotAnInteger:
		content = paginator.page(1)
	except EmptyPage:
		content = paginator.page(paginator.num_pages)
	return content

def clean_view_count_history():
	cur_time = datetime.datetime.now().replace(tzinfo=get_current_timezone())-datetime.timedelta(1,0) # clear view session one day ago
	TopicView.objects.filter(created_on__lt=cur_time).delete()
