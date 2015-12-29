from django.contrib.auth import authenticate, login, logout

from utils import *

def user_login(request):
	username = request.POST['username']
	password = request.POST['password']
	user = authenticate(username=username, password=password)
	if check_login(user):
		login(request, user)
		return JsonResponse({'login_successful':True})
	return JsonResponse({'login_successful':False})

@login_required
def user_logout(request):
	logout(request)
	return HttpResponse()

@transaction.atomic
def user_register(request):
	context = {}
	form = RegistrationForm(request.POST)
	if not form.is_valid():
		itemTemplate = loader.get_template('userauth/register_errors.html')
		html =  itemTemplate.render({'form':form}).replace('\n','') 
		context['register_successful'] = False
		context['html'] = html
		return JsonResponse(context)
	new_user = User.objects.create_user(username=form.cleaned_data['username'], \
										password=form.cleaned_data['password1'], \
										email=form.cleaned_data['email'])
	new_user.save()
	new_user_info = UserInfo(user=new_user)
	new_user_info.save()
	new_user = authenticate(username=form.cleaned_data['username'], \
							password=form.cleaned_data['password1'])
	login(request, new_user)
	context['register_successful'] = True
	return JsonResponse(context)




