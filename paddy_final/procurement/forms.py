"""
Forms for CropConnect
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Farmer, LandDetails, SlotBooking, Crop, Slot, Procurement


def validate_aadhaar_form(value):
    """Validate Aadhaar: 12 digits."""
    clean = ''.join(str(value).split())
    if len(clean) != 12 or not clean.isdigit():
        raise forms.ValidationError('Aadhaar must be exactly 12 digits.')
    return value


def validate_land_area(value):
    """Land area must be positive and reasonable (max 1000 acres)."""
    if value <= 0 or value > 1000:
        raise forms.ValidationError('Land area must be between 0.01 and 1000 acres.')
    return value


class FarmerRegistrationForm(UserCreationForm):
    """Farmer registration with Aadhaar and bank details."""
    aadhaar = forms.CharField(
        max_length=14,
        widget=forms.TextInput(attrs={
            'placeholder': 'XXXX XXXX XXXX',
            'pattern': r'\d{4}\s?\d{4}\s?\d{4}',
            'class': 'form-control'
        }),
        validators=[validate_aadhaar_form]
    )
    bank_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    bank_account_no = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    bank_ifsc = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. SBIN0001234'}))
    survey_no = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    total_area_acres = forms.DecimalField(
        max_digits=8, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
        validators=[validate_land_area]
    )
    village = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    mandal = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    district = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.CharField(max_length=100, initial='Andhra Pradesh', widget=forms.TextInput(attrs={'class': 'form-control'}))
    pincode = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'class': 'form-control', 'pattern': '[0-9]{6}'}))
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if 'password' in field and self.fields[field].widget.attrs.get('class') is None:
                self.fields[field].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.FARMER
        if commit:
            user.save()
            farmer = Farmer.objects.create(
                user=user,
                aadhaar=''.join(self.cleaned_data['aadhaar'].split()),
                bank_name=self.cleaned_data['bank_name'],
                bank_account_no=self.cleaned_data['bank_account_no'],
                bank_ifsc=self.cleaned_data['bank_ifsc'].upper(),
                village=self.cleaned_data['village'],
                mandal=self.cleaned_data['mandal'],
                district=self.cleaned_data['district'],
                state=self.cleaned_data['state'],
                pincode=self.cleaned_data['pincode'],
            )
            LandDetails.objects.create(
                farmer=farmer,
                survey_no=self.cleaned_data['survey_no'],
                total_area_acres=self.cleaned_data['total_area_acres'],
                village=self.cleaned_data['village'],
                mandal=self.cleaned_data['mandal'],
                district=self.cleaned_data['district'],
            )
        return user


class SlotBookingForm(forms.ModelForm):
    """Farmer slot booking with calendar date selection."""
    crop = forms.ModelChoiceField(
        queryset=Crop.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Select Crop'
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text='Select any date (day / month / year)'
    )
    estimated_quintals = forms.DecimalField(
        max_digits=8, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'})
    )

    class Meta:
        model = SlotBooking
        fields = ('estimated_quintals',)

    def clean(self):
        cleaned = super().clean()
        crop = cleaned.get('crop')
        date = cleaned.get('date')
        if not crop:
            raise forms.ValidationError('Please select a crop.')
        if not date:
            raise forms.ValidationError('Please select a date.')
        return cleaned


class ProcurementValidationForm(forms.ModelForm):
    """Officer form to validate weight."""
    actual_weight_quintals = forms.DecimalField(
        max_digits=8, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'})
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta:
        model = Procurement
        fields = ('actual_weight_quintals', 'remarks')


class MSPUpdateForm(forms.ModelForm):
    """Admin form to update MSP."""
    msp_per_quintal = forms.DecimalField(
        max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )

    class Meta:
        model = Crop
        fields = ('msp_per_quintal',)
