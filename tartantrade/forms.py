from django import forms

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from tartantrade.models import Item, Profile, Auction, ReportItem, RatingItem

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('picture',)
        widgets = {
            'picture': forms.FileInput(attrs={'id':'id_profile_picture'})
        }
        label = {
            'picture':'Upload Image'
        }


class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ('curr_price','start_price','end_time')

class ReportForm(forms.ModelForm):
    class Meta:
        model = ReportItem
        fields = ('reason',)
        widgets = {
            'reason': forms.Textarea(attrs={'id':'id_reason_text', 'rows':'3'}),
        }

class RatingForm(forms.ModelForm):
    class Meta:
        model = RatingItem
        fields = ['rating', 'rating_message']
        labels = {
            'rating': 'Rating (1-5)',
            'rating_message': 'Message'
        }
        widgets = {
            'rating': forms.NumberInput(attrs={
                'min': 1, 'max': 5, 'class': 'form-control'
            }),
            'rating_message': forms.Textarea(attrs={
                'rows': 2, 'class': 'form-control'
            }),
        }

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'description', 'condition', 'categories', 'picture', 'content_type', 'price', 'pickup_location']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'condition': forms.TextInput(attrs={'class': 'form-control'}),
            'categories': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'pickup_location': forms.TextInput(attrs={'class': 'form-control'}),
            'content_type': forms.HiddenInput(),
        }
