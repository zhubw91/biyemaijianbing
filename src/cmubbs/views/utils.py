from cmubbs.forms import *
from cmubbs.models import *

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import linebreaks

def check_login(user):
	if user is not None:
		if user.is_active:
			return True
	return False

def check_favourite(user, forum):
	if check_login(user):
		if forum.favorited_by.filter(user__exact=user).exists():
			return True
		else:
			return False

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
	
def getPageContent(paginator,page):
	content = None
	try:
		content = paginator.page(page)
	except PageNotAnInteger:
		content = paginator.page(1)
	except EmptyPage:
		content = paginator.page(paginator.num_pages)
	return content

def clean_font_tag(text):
    font_tag = 'b|/b|i|/i|big|/big|small|/small|strike|/strike|u|/u|mark|/mark'
    text = re.sub(r'<('+font_tag+')>',r'{__BiYeMaiJianBing__\1__/__}',text)
    text_0 = strip_tags(text)
    while text_0 != text:
        text = text_0
        text_0 = strip_tags(text)
    text = re.sub(r'{__BiYeMaiJianBing__('+font_tag+')__/__}',r'<\1>',text)
    text = linebreaks(text)
    return text