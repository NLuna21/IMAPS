# IMAPS_app/models.py

import random
import string
from datetime import date, timedelta
from django.db import models

# -------------------- Supplier --------------------
class Supplier(models.Model):
    SupplierCode = models.CharField(
        max_length=50, 
        primary_key=True,
        help_text="Unique identifier for the supplier (manually given)."
    )
    SupplierName = models.CharField(max_length=255)
    CATEGORY_CHOICES = [
        ('Ingredient', 'Ingredient'),
        ('Packaging', 'Packaging'),
        ('Both', 'Both'),
    ]
    Category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    SocialMedia = models.CharField(max_length=255, blank=True, null=True)
    EmailAddress = models.CharField(max_length=320, blank=True, null=True)
    ContactNumber = models.CharField(max_length=18, blank=True, null=True)
    PointPerson = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.SupplierName} ({self.SupplierCode})"


# -------------------- IngredientsRawMaterials --------------------
class IngredientsRawMaterials(models.Model):
    id = models.AutoField(primary_key=True)  # Use id as primary key (auto-incrementing)
    RawMaterialBatchCode = models.CharField(max_length=50, unique=True, blank=True)
    SupplierCode = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        db_column='SupplierCode'
    )
    RawMaterialName = models.CharField(max_length=255)
    DateDelivered = models.DateField()
    QuantityBought = models.IntegerField(default=0)
    QuantityLeft = models.IntegerField(default=0)
    USECATEGORY_CHOICES = [
        ('WBC', 'WBC'),
        ('GGB', 'GGB'),
        ('Both', 'Both'),
    ]
    UseCategory = models.CharField(max_length=10, choices=USECATEGORY_CHOICES, default="GGB")
    ExpirationDate = models.DateField()
    Status = models.CharField(max_length=15, blank=True)  # auto-generated; not editable via forms
    Cost = models.IntegerField(default=0, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Auto-generate batch code only if it doesn't exist.
        if not self.RawMaterialBatchCode:
            date_str = self.DateDelivered.strftime("%Y%m%d")
            words = self.RawMaterialName.split()
            name_abbrev = ''.join(word[0] for word in words[:3]).upper()
            random_number = self.generate_random_number()  # Generate a 3-digit random number
            self.RawMaterialBatchCode = f"{date_str}-{name_abbrev}-{random_number}"
            # If QuantityLeft hasn't been set, default it to QuantityBought.
            if self.QuantityLeft == 0:
                self.QuantityLeft = self.QuantityBought

        # Auto-compute Status:
        today = date.today()
        # If the ingredient expires within 30 days (or already expired), mark as "Expiring".
        if self.ExpirationDate and self.ExpirationDate <= today + timedelta(days=30):
            self.Status = "Expiring"
        # Otherwise, if QuantityLeft is below threshold (e.g., less than 10), mark as "Low Inventory".
        elif self.QuantityLeft < 10:
            self.Status = "Low Inventory"
        else:
            self.Status = "OK"
        super().save(*args, **kwargs)

    def generate_random_number(self):
        """
        Generate a 3-digit random number.
        """
        return ''.join(random.choices(string.digits, k=3))
    
    def __str__(self):
        return f"{self.RawMaterialBatchCode} - {self.RawMaterialName}"


# -------------------- PackagingRawMaterials --------------------
class PackagingRawMaterials(models.Model):
    id = models.AutoField(primary_key=True)  # Use id as primary key (auto-incrementing)
    PackagingBatchCode = models.CharField(max_length=50, unique=True, blank=True)
    SupplierCode = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        db_column='SupplierCode'
    )
    RawMaterialName = models.CharField(max_length=255)
    QuantityBought = models.IntegerField(default=0)
    QuantityLeft = models.IntegerField(default=0)
    USECATEGORY_CHOICES = [
        ('WBC', 'WBC'),
        ('GGB', 'GGB'),
        ('Both', 'Both'),
    ]
    UseCategory = models.CharField(max_length=10, choices=USECATEGORY_CHOICES)
    Status = models.CharField(max_length=15, blank=True)  # auto-computed
    Cost = models.IntegerField(default=0, blank=True, null=True)
    ContainerSize = models.CharField(max_length=50, blank=True, null=True)
    DateDelivered = models.DateField()
    # The name of the packaging material (for abbreviation purposes)

    def save(self, *args, **kwargs):
        # Generate batch code only if it hasn't been set yet.
        if not self.PackagingBatchCode:
            date_str = self.DateDelivered.strftime("%Y%m%d")
            words = self.RawMaterialName.split()
            name_abbrev = ''.join(word[0] for word in words[:3]).upper()
            container_size = self.ContainerSize if self.ContainerSize else "UNK"
            random_number = ''.join(random.choices(string.digits, k=3))
            self.PackagingBatchCode = f"{date_str}-{name_abbrev}-{container_size}-{random_number}"
            if self.QuantityLeft == 0:
                self.QuantityLeft = self.QuantityBought
        # Auto-compute status based on quantity left.
        if self.QuantityLeft < 10:
            self.Status = "Low Inventory"
        else:
            self.Status = "OK"
        super().save(*args, **kwargs)

    # Removed is_batch_code_invalid and generate_random_number methods as batch code is now immutable once set.
    
    def __str__(self):
        return f"{self.PackagingBatchCode} - {self.RawMaterialName}"


# -------------------- UsedIngredient --------------------
class UsedIngredient(models.Model):
    UsedIngredientBatchCode = models.CharField(max_length=50, primary_key=True, blank=True)
    IngredientRawMaterialBatchCode = models.ForeignKey(
        IngredientsRawMaterials,
        on_delete=models.CASCADE,
        db_column='RawMaterialBatchCode'
    )
    RawMaterialName = models.CharField(max_length=255)
    QuantityUsed = models.IntegerField()
    USECATEGORY_CHOICES = [
        ('WBC', 'WBC'),
        ('GGB', 'GGB'),
        ('Both', 'Both'),
    ]
    UseCategory = models.CharField(max_length=10, choices=USECATEGORY_CHOICES)
    DateUsed = models.DateField()

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
    USEDPackagingBatchCode = models.CharField(max_length=50, primary_key=True, blank=True)
    PackagingRawMaterialBatchCode = models.ForeignKey(
        PackagingRawMaterials,
        on_delete=models.CASCADE,
        db_column='PackagingBatchCode'
    )
    RawMaterialName = models.CharField(max_length=255)
    QuanityUsed = models.IntegerField()
    USECATEGORY_CHOICES = [
        ('WBC', 'WBC'),
        ('GGB', 'GGB'),
        ('Both', 'Both'),
    ]
    UseCategory = models.CharField(max_length=10, choices=USECATEGORY_CHOICES)
    DateUsed = models.DateField()

    def save(self, *args, **kwargs):
        if not self.USEDPackagingBatchCode:
            # Use the DateDelivered from the linked PackagingRawMaterials record
            date_str = self.PackagingRawMaterialBatchCode.DateDelivered.strftime("%Y%m%d")
            words = self.RawMaterialName.split()
            name_abbrev = ''.join(word[0] for word in words[:3]).upper()
            random_number = ''.join(random.choices(string.digits, k=3))
            self.USEDPackagingBatchCode = f"{date_str}-{name_abbrev}-{random_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.USEDPackagingBatchCode} - {self.RawMaterialName}"
