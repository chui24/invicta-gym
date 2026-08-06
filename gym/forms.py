from django import forms
from .models import Cliente, Plan, Pago
from django.utils import timezone

TW_INPUT_CLASS = 'w-full bg-black/60 border border-brand-accent/40 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-brand-accent focus:shadow-[0_0_20px_rgba(213,0,249,0.5)] transition-all shadow-inner placeholder-brand-muted/50'
TW_SELECT_CLASS = 'w-full bg-black/60 border border-brand-accent/40 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-brand-accent focus:shadow-[0_0_20px_rgba(213,0,249,0.5)] transition-all shadow-inner'

class RegistroClienteForm(forms.ModelForm):
    # Campos adicionales que no están en el modelo Cliente
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.all(),
        label="Plan de Suscripción",
        widget=forms.Select(attrs={'class': TW_SELECT_CLASS}),
        required=True
    )
    metodo_pago = forms.ChoiceField(
        choices=Pago.METODO_PAGO_CHOICES,
        label="Método de Pago",
        widget=forms.Select(attrs={'class': TW_SELECT_CLASS}),
        required=True
    )
    fecha_inscripcion = forms.DateField(
        label="Fecha de Inscripción",
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={'class': TW_INPUT_CLASS, 'type': 'date'}),
        required=True
    )
    
    # Campo oculto para la foto capturada por webcam
    foto_base64 = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Cliente
        fields = ['cedula', 'nombre', 'correo', 'telefono']
        widgets = {
            'cedula': forms.TextInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Ej. 12345678'}),
            'nombre': forms.TextInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Ej. Juan Pérez'}),
            'correo': forms.EmailInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': TW_INPUT_CLASS, 'placeholder': 'Ej. 0412-1234567'}),
        }

class RenovacionForm(forms.Form):
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.all(),
        label="Plan de Suscripción",
        widget=forms.Select(attrs={'class': TW_SELECT_CLASS}),
        required=True
    )
    metodo_pago = forms.ChoiceField(
        choices=Pago.METODO_PAGO_CHOICES,
        label="Método de Pago",
        widget=forms.Select(attrs={'class': TW_SELECT_CLASS}),
        required=True
    )

class ClienteEditForm(forms.ModelForm):
    foto_base64 = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = Cliente
        fields = ['cedula', 'nombre', 'correo', 'telefono']
        widgets = {
            'cedula': forms.TextInput(attrs={'class': TW_INPUT_CLASS}),
            'nombre': forms.TextInput(attrs={'class': TW_INPUT_CLASS}),
            'correo': forms.EmailInput(attrs={'class': TW_INPUT_CLASS}),
            'telefono': forms.TextInput(attrs={'class': TW_INPUT_CLASS}),
        }

