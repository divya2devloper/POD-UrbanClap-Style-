import re
from django import forms
from .models import UserProfile, PhotographerProfile, PortfolioItem

class WhatsAppForm(forms.ModelForm):
    # ... (rest of WhatsAppForm)
    class Meta:
        model = UserProfile
        fields = ['whatsapp_number']
        widgets = {
            'whatsapp_number': forms.TextInput(attrs={
                'placeholder': '+91 98765 43210',
                'class': 'w-full h-14 bg-white border-2 border-slate-100 rounded-2xl px-6 font-600 focus:border-green-500 focus:ring-4 focus:ring-green-500/10 outline-none transition-all',
                'id': 'whatsapp_number_input'
            })
        }

    def clean_whatsapp_number(self):
        number = self.cleaned_data.get('whatsapp_number')
        if not number:
            raise forms.ValidationError("WhatsApp number is required.")
        
        # Remove spaces and dashes
        number = number.replace(" ", "").replace("-", "")
        
        # Validate format (e.g. +919876543210 or 9876543210)
        # We prefer international format with +
        if not re.match(r'^\+?\d{10,15}$', number):
            raise forms.ValidationError("Invalid format. Use international format (e.g. +919876543210).")
        
        return number

class PhotographerProfileForm(forms.ModelForm):
    class Meta:
        model = PhotographerProfile
        fields = ['bio', 'experience_years', 'categories', 'specialties', 'profile_picture', 'max_travel_radius', 'is_available']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500', 'rows': 4}),
            'categories': forms.CheckboxSelectMultiple(),
            'specialties': forms.TextInput(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500'}),
            'experience_years': forms.NumberInput(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500'}),
            'max_travel_radius': forms.NumberInput(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'w-6 h-6 rounded-lg border-slate-300 text-blue-600 focus:ring-blue-500'}),
            'profile_picture': forms.FileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-600 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'}),
        }


class PortfolioItemForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = ['category', 'image']
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500'}),
            'image': forms.FileInput(attrs={'class': 'w-full p-4 rounded-2xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500'}),
        }
