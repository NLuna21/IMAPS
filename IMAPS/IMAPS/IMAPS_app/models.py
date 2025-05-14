import random
import string
from datetime import date, timedelta
from django.db import models

# -------------------- Supplier --------------------
class Supplier(models.Model):
    CHANGE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('deleted', 'Deleted'),
    ]
    change_status = models.CharField(
        max_length=50,                  # bumped to 50 to avoid future length issues
        choices=CHANGE_STATUS_CHOICES,
        default='active',
    )

    SupplierCode = models.CharField(
        max_length=50, 
        primary_key=True,
        help_text="Unique identifier for the supplier (manually given).",
        unique=True
    )
    SupplierName = models.CharField(max_length=255)
    CATEGORY_CHOICES = [
        ('Ingredient', 'Ingredient'),
        ('Packaging', 'Packaging'),
        ('Both', 'Both'),
    ]
    Category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    SocialMedia = models.CharField(max_length=255, blank=True, null=True, default='None')
    EmailAddress = models.CharField(max_length=320, blank=True, null=True, default='None')
    ContactNumber = models.CharField(max_length=20, blank=True, null=True, default='None')
    PointPerson = models.CharField(max_length=255, blank=True, null=True, default='None')

    def __str__(self):
        return f"{self.SupplierName} ({self.SupplierCode})"


# -------------------- IngredientsRawMaterials --------------------
class IngredientsRawMaterials(models.Model):
    CHANGE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('deleted', 'Deleted'),
    ]
    
    id = models.AutoField(primary_key=True)
    RawMaterialBatchCode = models.CharField(max_length=50, unique=True, blank=True)
    SupplierCode = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        db_column='SupplierCode'
    )
    RawMaterialName = models.CharField(max_length=255)
    DateDelivered = models.DateField()
    QuantityBought = models.FloatField(default=0)
    QuantityLeft = models.FloatField(default=0)
    USECATEGORY_CHOICES = [
        ('WBC', 'WBC'),
        ('GGB', 'GGB'),
        ('Both', 'Both'),
    ]
    UseCategory = models.CharField(max_length=10, choices=USECATEGORY_CHOICES, default="GGB")
    ExpirationDate = models.DateField()
    Status = models.CharField(max_length=50, default="Good")
    Cost = models.FloatField(default=0)
    change_status = models.CharField(max_length=10, choices=CHANGE_STATUS_CHOICES, default='active')

    def save(self, *args, **kwargs):
        # Determine if we need to regenerate batch code
        regenerate = False
        if not self.pk:
            regenerate = True
        else:
            old = IngredientsRawMaterials.objects.get(pk=self.pk)
            if old.RawMaterialName != self.RawMaterialName or old.DateDelivered != self.DateDelivered:
                regenerate = True

        if regenerate:
            date_str = self.DateDelivered.strftime("%Y%m%d")
            words = self.RawMaterialName.split()
            name_abbrev = ''.join(word[0] for word in words[:3]).upper()
            random_number = ''.join(random.choices(string.digits, k=3))
            self.RawMaterialBatchCode = f"{date_str}-{name_abbrev}-{random_number}"
            if self.QuantityLeft == 0:
                self.QuantityLeft = self.QuantityBought

        # Auto-compute Status
        today = date.today()
        if self.ExpirationDate and self.ExpirationDate <= today + timedelta(days=30):
            self.Status = "Expiring"
        elif self.QuantityLeft < 10:
            self.Status = "Low Inventory"
        else:
            self.Status = "OK"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.RawMaterialBatchCode} - {self.RawMaterialName}"


# -------------------- PackagingRawMaterials --------------------
class PackagingRawMaterials(models.Model):
    CHANGE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('deleted', 'Deleted'),
    ]
    
    STATUS_CHOICES = [
        ('Low Inventory', 'Low Inventory'),
        ('OK', 'OK'),
    ]
    
    id = models.AutoField(primary_key=True)
    PackagingBatchCode = models.CharField(max_length=50, unique=True, blank=True)
    SupplierCode = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        db_column='SupplierCode'
    )
    RawMaterialName = models.CharField(max_length=255)
    ContainerSize = models.CharField(max_length=50, default="N/A")
    DateDelivered = models.DateField()
    QuantityBought = models.IntegerField(default=0)
    QuantityLeft = models.IntegerField(default=0)
    USECATEGORY_CHOICES = [
        ('WBC', 'WBC'),
        ('GGB', 'GGB'),
        ('Both', 'Both'),
    ]
    UseCategory = models.CharField(max_length=10, choices=USECATEGORY_CHOICES, default="GGB")
    Status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="OK")
    Cost = models.FloatField(default=0)
    change_status = models.CharField(max_length=10, choices=CHANGE_STATUS_CHOICES, default='active')

    def save(self, *args, **kwargs):
        regenerate = False
        if not self.pk:
            regenerate = True
        else:
            old = PackagingRawMaterials.objects.get(pk=self.pk)
            if old.RawMaterialName != self.RawMaterialName or old.ContainerSize != self.ContainerSize or old.DateDelivered != self.DateDelivered:
                regenerate = True

        if regenerate:
            date_str = self.DateDelivered.strftime("%Y%m%d")
            words = self.RawMaterialName.split()
            name_abbrev = ''.join(word[0] for word in words[:3]).upper()
            container = self.ContainerSize or "UNK"
            random_number = ''.join(random.choices(string.digits, k=3))
            self.PackagingBatchCode = f"{date_str}-{name_abbrev}-{container}-{random_number}"
            if self.QuantityLeft == 0:
                self.QuantityLeft = self.QuantityBought

        # ✅ FIX: Ensure QuantityBought > 0 before checking threshold
        try:
            if self.QuantityBought > 0:
                percentage_left = (self.QuantityLeft / self.QuantityBought) * 100
                if percentage_left < 15:
                    self.Status = "Low Inventory"
                else:
                    self.Status = "OK"
            else:
                self.Status = "Low Inventory"
        except ZeroDivisionError:
            self.Status = "Low Inventory"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.PackagingBatchCode} - {self.RawMaterialName}"


# -------------------- UsedIngredient --------------------
class UsedIngredient(models.Model):
    CHANGE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('deleted', 'Deleted'),
    ]
    
    UsedIngredientBatchCode = models.CharField(max_length=50, primary_key=True)
    IngredientRawMaterialBatchCode = models.ForeignKey(
        IngredientsRawMaterials,
        on_delete=models.CASCADE,
        db_column='IngredientRawMaterialBatchCode'
    )
    RawMaterialName = models.CharField(max_length=255)
    QuantityUsed = models.FloatField()
    DateUsed = models.DateField()
    USECATEGORY_CHOICES = [
        ('WBC', 'WBC'),
        ('GGB', 'GGB'),
        ('Both', 'Both'),
    ]
    UseCategory = models.CharField(max_length=10, choices=USECATEGORY_CHOICES)
    change_status = models.CharField(max_length=10, choices=CHANGE_STATUS_CHOICES, default='active')

    def save(self, *args, **kwargs):
        if not self.UsedIngredientBatchCode:
            date_str = self.DateUsed.strftime("%Y%m%d")
            words = self.RawMaterialName.split()
            name_abbrev = ''.join(word[0] for word in words[:3]).upper()
            random_number = ''.join(random.choices(string.digits, k=3))
            self.UsedIngredientBatchCode = f"{date_str}-{name_abbrev}-{random_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.UsedIngredientBatchCode} - {self.RawMaterialName}"


# -------------------- UsedPackaging --------------------
class UsedPackaging(models.Model):
    CHANGE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('deleted', 'Deleted'),
    ]
    
    USEDPackagingBatchCode = models.CharField(max_length=50, primary_key=True, blank=True)
    PackagingRawMaterialBatchCode = models.ForeignKey(
        PackagingRawMaterials,
        on_delete=models.CASCADE,
        db_column='PackagingRawMaterialBatchCode'
    )
    RawMaterialName = models.CharField(max_length=255)
    QuantityUsed = models.IntegerField()
    DateUsed = models.DateField()
    USECATEGORY_CHOICES = [
        ('WBC', 'WBC'),
        ('GGB', 'GGB'),
        ('Both', 'Both'),
    ]
    UseCategory = models.CharField(max_length=10, choices=USECATEGORY_CHOICES)
    change_status = models.CharField(max_length=10, choices=CHANGE_STATUS_CHOICES, default='active')

    def save(self, *args, **kwargs):
        if not self.USEDPackagingBatchCode:
            date_str = self.PackagingRawMaterialBatchCode.DateDelivered.strftime("%Y%m%d")
            words = self.RawMaterialName.split()
            name_abbrev = ''.join(word[0] for word in words[:3]).upper()
            random_number = ''.join(random.choices(string.digits, k=3))
            self.USEDPackagingBatchCode = f"{date_str}-{name_abbrev}-{random_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.USEDPackagingBatchCode} - {self.RawMaterialName}"
