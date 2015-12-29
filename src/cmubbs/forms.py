from django import forms

import datetime
import re
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.template import loader, Context
from django.utils.html import strip_tags
from cmubbs.models import *


def clean_font_tag(text):
    font_tag = 'b|/b|i|/i|big|/big|small|/small|strike|/strike|u|/u|mark|/mark'
    text = re.sub(r'<('+font_tag+')>',r'{__BiYeMaiJianBing__\1__/__}',text)
    text_0 = strip_tags(text)
    while text_0 != text:
        text = text_0
        text_0 = strip_tags(text)
    text = re.sub(r'{__BiYeMaiJianBing__('+font_tag+')__/__}',r'<\1>',text)
    return text


class RegistrationForm(forms.Form):
    username = forms.CharField(max_length = 20, 
                               widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password1 = forms.CharField(max_length = 200, 
                                label='Password', 
                                widget = forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password2 = forms.CharField(max_length = 200, 
                                label='Confirm Password',  
                                widget = forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}))
    email = forms.CharField(max_length = 200,
                            label='E-mail',
                            widget=forms.TextInput(attrs={'placeholder': 'E-mail'}))

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()

        # Confirms that the two password fields match
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords did not match.")

        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__exact=username):
            raise forms.ValidationError("Username is already taken.")

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if '@' not in email:
            raise forms.ValidationError("Invalid email address.")
        if User.objects.filter(email__exact=email):
            raise forms.ValidationError("E-mail address is already registered.")
        return email

class PasswordForm(forms.Form):
    password1 = forms.CharField(max_length = 200, 
                                label='New Password', 
                                widget = forms.PasswordInput(attrs={'placeholder': 'New Password'}))
    password2 = forms.CharField(max_length = 200, 
                                label='Confirm New Password',  
                                widget = forms.PasswordInput(attrs={'placeholder': 'Confirm New Password'}))

    def clean(self):
        cleaned_data = super(PasswordForm, self).clean()

        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords did not match.")

        return cleaned_data

class ModeratorForm(forms.Form):

    username = forms.CharField(max_length = 20, 
                               label='Username',
                               widget=forms.TextInput(attrs={'placeholder': 'Add a moderator.'}))

    def __init__(self,*args,**kwargs):
        self.forum_name = kwargs.pop('forum_name')
        super(ModeratorForm,self).__init__(*args,**kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not User.objects.filter(username__exact=username).exists():
             raise forms.ValidationError("No user has this username. Check the username.")
        user = User.objects.get(username=username)
        
        if user.userinfo.manages.filter(name=self.forum_name).exists():
            raise forms.ValidationError("The user is already the moderator of this forum.")
        return username

class ParticipantForm(forms.Form):

    username = forms.CharField(max_length = 20, 
                               label='Username',
                               widget=forms.TextInput(attrs={'placeholder': 'Add a participant.'}))

    def __init__(self,*args,**kwargs):
        self.event = kwargs.pop('event')
        super(ParticipantForm,self).__init__(*args,**kwargs)

    def clean(self):
        cleaned_data = super(ParticipantForm, self).clean()
        if len(self.event.participants.all()) >= self.event.max_participants:
            raise forms.ValidationError("Exceed participants limit.")
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not User.objects.filter(username__exact=username).exists():
             raise forms.ValidationError("No user has this username. Check the username.")
        user = User.objects.get(username=username)
        
        if self.event.participants.filter(user__exact=user).exists():
            raise forms.ValidationError("The user is already participating this event.")
        return username

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)

class UserInfoForm(forms.ModelForm):
    class Meta:
        model = UserInfo

        fields = ('gender', 'bio', 'birth')
        widgets = {'birth': forms.widgets.DateInput(attrs={'class':'form-control birth_form', 'type':'date'})}


class UserImgForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = ('image',)
        widgets = {'image' : forms.FileInput(attrs={'required':True})}


class ForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ('name', 'description')

class CreatePostForm(forms.Form):
    post_title = forms.CharField(max_length=50, widget=forms.widgets.TextInput(attrs={'class':'form-control'}))
    post_body = forms.CharField(max_length=1000, required=False, widget=forms.widgets.Textarea(attrs={'class':'form-control', 'id':'post-body'}))
    plain_text = forms.BooleanField(initial=False, required=False, widget=forms.widgets.CheckboxInput(attrs={'id':'plain-text-checked', 'style':'display:none'}))

    def __init__(self,*args,**kwargs):
        if 'description_required' in kwargs:
            self.description_required = kwargs.pop('description_required')
        else:
            self.description_required = True
        super(CreatePostForm,self).__init__(*args,**kwargs)

    def clean_post_body(self):
        post_body = self.cleaned_data['post_body']

        plain_text = self.cleaned_data.get('plain_text')
        if not plain_text:
            post_body = clean_font_tag(post_body)

        if self.description_required and not post_body:
            raise forms.ValidationError('Topic content is required.')

        return post_body

class EventSplitDateTimeWidget(forms.widgets.SplitDateTimeWidget):
    def __init__(self, attrs=None, date_type=None, time_type=None):
        widgets = (forms.widgets.DateInput(attrs={'type' : 'date'}), forms.widgets.TimeInput(attrs={'type' : 'time'}, format="%H:%M"))
        super(forms.widgets.SplitDateTimeWidget, self).__init__(widgets, attrs)

class EventForm(forms.Form):
    title = forms.CharField(max_length=50, widget=forms.widgets.TextInput(attrs={'class':'form-control'}))
    description = forms.CharField(max_length=1000, widget=forms.widgets.Textarea(attrs={'class':'form-control'}))
    max_participants = forms.IntegerField(min_value=1, max_value=1000, label='Max Participants', widget=forms.widgets.NumberInput(attrs={'class':'form-control'}))
    formatted_address = forms.CharField(max_length=500, widget=forms.widgets.TextInput(attrs={'class':'form-control', 'readonly': True}))
    lat = forms.FloatField(widget=forms.widgets.HiddenInput(attrs={'id':'lat'}))
    lng = forms.FloatField(widget=forms.widgets.HiddenInput(attrs={'id':'lng'}))
    start = forms.DateTimeField(widget=EventSplitDateTimeWidget(attrs={'class':'form-control'}))
    end = forms.DateTimeField(widget=EventSplitDateTimeWidget(attrs={'class':'form-control'}))
    public = forms.BooleanField(initial=False, required=False, label='Make this event public and allow all users to RSVP.')

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        self.user = kwargs.pop('user', None)
        self.forum = kwargs.pop('forum', None)
        _initial = kwargs.pop('initial', {})
        if self.event is not None:    
            _initial.update(model_to_dict(self.event.topic,('title',)))
            _initial.update(model_to_dict(self.event.location,('formatted_address','lat','lng',)))
            _initial.update(model_to_dict(self.event.time_period,('start','end',)))
            _initial.update(model_to_dict(self.event,('description','public','max_participants',)))
        
        super(EventForm, self).__init__(initial=_initial, *args, **kwargs)

    def clean_max_participants(self):
        max_participants = self.cleaned_data.get('max_participants')
        if self.event is not None and max_participants < len(self.event.participants.all()):
            raise forms.ValidationError("Max number of participants should not be less than the current participants number.")
        return max_participants

    def clean_lat(self):
        lat = self.cleaned_data.get('lat')
        if lat < -90 or lat > 90:
            raise forms.ValidationError("Latitude out of range.")
        if lat < -85 or lat > 85:
            raise forms.ValidationError("Latitude out of range of Google Map.")
        return lat

    def clean_lng(self):
        lng = self.cleaned_data.get('lng')
        if lng < -180 or lng > 180:
            raise forms.ValidationError("Longitude out of range.")
        return lng

    def clean_end(self):
        start_date = self.cleaned_data.get('start')
        end_date = self.cleaned_data.get('end')
        if end_date < start_date:
            raise forms.ValidationError("End time should not be earlier than start time.")
        return end_date
        
    def save(self):
        if self.event is not None:
            self.event.topic.title = self.cleaned_data['title']
            self.event.topic.save()

            self.event.description=self.cleaned_data['description']
            self.event.public=self.cleaned_data['public']
            self.event.max_participants=self.cleaned_data['max_participants']
            self.event.save()

            self.event.location.lat = self.cleaned_data['lat']
            self.event.location.lng = self.cleaned_data['lng']
            self.event.location.formatted_address = self.cleaned_data['formatted_address']
            self.event.location.save()

            self.event.time_period.start = self.cleaned_data['start']
            self.event.time_period.end = self.cleaned_data['end']
            self.event.time_period.save()

            return self.event
        else:
            if self.user is None or self.forum is None:
                raise Exception('Lack parameters: should set either user and forum or event.')
            new_topic = Topic(title=self.cleaned_data['title'], user = self.user, forum = self.forum)
            new_topic.save()

            tag = get_object_or_404(Tag, name='Event')
            new_topic.tags.add(tag)
            new_topic.save()

            new_event = Event(topic=new_topic, description=self.cleaned_data['description'], public=self.cleaned_data['public'], max_participants=self.cleaned_data['max_participants'])
            new_event.save()

            new_location = Location(event=new_event, lat=self.cleaned_data['lat'], lng=self.cleaned_data['lng'], formatted_address=self.cleaned_data['formatted_address'])
            new_location.save()

            new_time_period = TimePeriod(event=new_event, start=self.cleaned_data['start'], end=self.cleaned_data['end'])
            new_time_period.save()

            return new_event

class EventApplicationForm(forms.Form):
    message = forms.CharField(max_length=200, required=True, widget=forms.widgets.Textarea(attrs={'required':True, 'class':'form-control', 'placeholder':'Write your reason to apply for this event...'}))

class ReplyPostForm(forms.Form):
    reply_body = forms.CharField(max_length=1000, required=True, widget=forms.widgets.Textarea(attrs={'class':'form-control', 'id':'reply-body', 'required':True}))
    plain_text = forms.BooleanField(initial=False, required=False, widget=forms.widgets.CheckboxInput(attrs={'id':'plain-text-checked', 'style':'display:none'}))
    def clean_reply_body(self):
        reply_body = self.cleaned_data['reply_body']
        plain_text = self.cleaned_data.get('plain_text')
        if not plain_text:
            reply_body = clean_font_tag(reply_body)
        return reply_body

class MessageForm(forms.Form):
    message_body = forms.CharField(max_length=500, required=True, widget=forms.widgets.Textarea(attrs={'class':'form-control', 'rows':3, 'autofocus':True, 'required':True}))

class SearchKeyForm(forms.Form):
    key_words = forms.CharField(max_length=50, required=False, widget=forms.widgets.TextInput(attrs={'class':'form-control'}))

class ReplyCommentForm(forms.Form):
    reply_comment_body = forms.CharField(max_length=1000, required=True, widget=forms.widgets.Textarea(attrs={'class':'form-control', 'required':True},))

class AppendTopicForm(forms.Form):
    append_topic_body = forms.CharField(max_length=1000, required=True, widget=forms.widgets.Textarea(attrs={'class':'form-control', 'required':True}))


class AdvancedSearchForm(forms.Form):
    start_date = forms.DateField(initial=None,required = False, widget=forms.widgets.DateInput(attrs={'class':'form-control', 'type':'date'}))
    end_date = forms.DateField(initial=datetime.date.today,required = False, widget=forms.widgets.DateInput(attrs={'class':'form-control', 'type':'date'}))
    author = forms.CharField(max_length=10, required = False, widget=forms.widgets.TextInput(attrs={'class':'form-control', 'style' : 'width: 50%;'}))
    title = forms.CharField(max_length=10, required = False, widget=forms.widgets.TextInput(attrs={'class':'form-control', 'style' : 'width: 50%;'}))
    content = forms.CharField(max_length=50, required = False, widget=forms.widgets.TextInput(attrs={'class':'form-control', 'style' : 'width: 50%;'}))

    def clean_end_date(self):
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')
        if end_date < start_date:
            raise forms.ValidationError("End time should not be earlier than start time.")
        return end_date

class PollForm(forms.Form):
    question = forms.CharField(max_length=200,required = True,widget=forms.widgets.TextInput(attrs={'class':'form-control', 'style' : 'width: 50%;'}))
    is_multiple = forms.BooleanField(initial=False, required=False, label='Allow multiple choices.')

    def clean_question(self):
        question = self.cleaned_data.get('question')
        if len(question) == 0 :
            raise forms.ValidationError("Must has a question.")
        if len(question) > 200:
            raise forms.ValidationError("Question too long!(should within 200 characters)")
        return question

class PostImageForm(forms.Form):
    image = forms.ImageField() 

class MessageToForm(forms.Form):
    text = forms.CharField(max_length=100, required = True, widget=forms.widgets.TextInput(attrs={'class':'form-control','placeholder': 'Username'}))

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if len(text) == 0:
            raise forms.ValidationError("Can not be empty.")
        if not User.objects.filter(username__exact=text).exists():
            raise forms.ValidationError("No user has this username. Check the username.")
        return text

class BroadcastForm(forms.Form):
    text = forms.CharField(max_length=1000, required = True, widget=forms.widgets.Textarea(attrs={'class':'form-control','rows':10}))

    def clean_text(self):
        return self.cleaned_data.get('text')
