# IMAPS_app/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Supplier,
    IngredientsRawMaterials,
    PackagingRawMaterials,
    UsedIngredient,
    UsedPackaging
)

class SupplierForm(forms.ModelForm):
    Category = forms.ChoiceField(
        choices=Supplier.CATEGORY_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label="Supplier Type"
    )
    
    class Meta:
        model = Supplier
        fields = '__all__'

class IngredientsRawMaterialsForm(forms.ModelForm):
    UseCategory = forms.ChoiceField(
        choices=IngredientsRawMaterials.USECATEGORY_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label="Use Type"
    )
    existing_batch = forms.ChoiceField(
        choices=[],
        required=False,
        label="Existing Raw Material Batch Code",
        widget=forms.Select
    )
    
    class Meta:
        model = IngredientsRawMaterials
        exclude = ['QuantityLeft', 'RawMaterialBatchCode','Status']
        widgets = {
            'DateDelivered': forms.DateInput(attrs={'type': 'date'}),
            'ExpirationDate': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter suppliers by category (ingredients)
        self.fields['SupplierCode'].queryset = Supplier.objects.filter(Category__in=['Ingredient', 'Both'])
        batches = IngredientsRawMaterials.objects.values_list('RawMaterialBatchCode', flat=True)
        choices = [('None', 'None')]
        choices += [(batch, batch) for batch in batches]
        self.fields['existing_batch'].choices = choices
    
    def clean(self):
        cleaned_data = super().clean()
        date_delivered = cleaned_data.get("DateDelivered")
        expiration_date = cleaned_data.get("ExpirationDate")
        if date_delivered and expiration_date and expiration_date < date_delivered:
            raise ValidationError("Expiration date cannot be before the delivery date.")
        return cleaned_data

class PackagingRawMaterialsForm(forms.ModelForm):
    UseCategory = forms.ChoiceField(
        choices=PackagingRawMaterials.USECATEGORY_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label="Use Type"
    )
    existing_batch = forms.ChoiceField(
        choices=[],
        required=False,
        label="Existing Packaging Batch Code (to add quantity left)",
        widget=forms.Select
    )
    
    class Meta:
        model = PackagingRawMaterials
        exclude = ['QuantityLeft', 'PackagingBatchCode','Status']
        widgets = {
            'DateDelivered': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter suppliers by category (packaging)
        self.fields['SupplierCode'].queryset = Supplier.objects.filter(Category__in=['Packaging', 'Both'])
        batches = PackagingRawMaterials.objects.values_list('PackagingBatchCode', flat=True)
        choices = [('None', 'None')]
        choices += [(batch, batch) for batch in batches]
        self.fields['existing_batch'].choices = choices

class UsedIngredientForm(forms.ModelForm):
    UseCategory = forms.ChoiceField(
        choices=UsedIngredient.USECATEGORY_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label="Use Category"
    )
    
    class Meta:
        model = UsedIngredient
        exclude = ['UsedIngredientBatchCode', 'RawMaterialName']
        widgets = {
            'DateUsed': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date_used = cleaned_data.get("DateUsed")
        ingredient = cleaned_data.get("IngredientRawMaterialBatchCode")
        if ingredient and date_used:
            if date_used < ingredient.DateDelivered:
                raise ValidationError("Date Used cannot be before the Date Delivered of the ingredient batch.")
        return cleaned_data

class UsedPackagingForm(forms.ModelForm):
    class Meta:
        model = UsedPackaging
        exclude = ['USEDPackagingBatchCode']
        widgets = {
            'DateUsed': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date_used = cleaned_data.get("DateUsed")
        packaging = cleaned_data.get("PackagingRawMaterialBatchCode")
        if packaging and date_used:
            if date_used < packaging.DateDelivered:
                raise ValidationError("Date Used cannot be before the Date Delivered.")
        return cleaned_data

# --- New Update Forms for Ingredients and Packaging ---

class IngredientsRawMaterialsUpdateForm(forms.ModelForm):
    UseCategory = forms.ChoiceField(
        choices=IngredientsRawMaterials.USECATEGORY_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label="Use Type"
    )
    
    class Meta:
        model = IngredientsRawMaterials
        fields = ['SupplierCode', 'RawMaterialName', 'DateDelivered', 'QuantityBought', 'QuantityLeft', 'UseCategory', 'ExpirationDate', 'Status', 'Cost']
        widgets = {
            'DateDelivered': forms.DateInput(attrs={'type': 'date'}),
            'ExpirationDate': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        qty_bought = cleaned_data.get('QuantityBought')
        qty_left = cleaned_data.get('QuantityLeft')
        if qty_bought is not None and qty_left is not None:
            if qty_left > qty_bought:
                raise ValidationError("Quantity Left cannot be greater than Quantity Bought.")
        return cleaned_data

class PackagingRawMaterialsUpdateForm(forms.ModelForm):
    UseCategory = forms.ChoiceField(
        choices=PackagingRawMaterials.USECATEGORY_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label="Use Type"
    )
    
    class Meta:
        model = PackagingRawMaterials
        fields = ['SupplierCode', 'RawMaterialName', 'ContainerSize', 'DateDelivered', 'QuantityBought', 'QuantityLeft', 'UseCategory', 'Status', 'Cost']
        widgets = {
            'DateDelivered': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        qty_bought = cleaned_data.get('QuantityBought')
        qty_left = cleaned_data.get('QuantityLeft')
        if qty_bought is not None and qty_left is not None:
            if qty_left > qty_bought:
                raise ValidationError("Quantity Left cannot be greater than Quantity Bought.")
        return cleaned_data
