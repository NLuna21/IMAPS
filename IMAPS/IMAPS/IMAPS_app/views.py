# IMAPS_app/views.py

from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum
from django.contrib import messages
from .models import (
    Supplier,
    IngredientsRawMaterials,
    PackagingRawMaterials,
    UsedIngredient,
    UsedPackaging
)
from .forms import (
    SupplierForm,
    IngredientsRawMaterialsForm,
    PackagingRawMaterialsForm,
    UsedIngredientForm,
    UsedPackagingForm,
    # New update forms that include fields that were previously excluded:
    IngredientsRawMaterialsUpdateForm,
    PackagingRawMaterialsUpdateForm
)

PASSWORD = "test123"

#####################
#      SUPPLIERS    #
#####################
import re
from django.shortcuts import render
from .models import Supplier
from .forms import SupplierForm

def suppliers_list(request):
    # Fetch only active and newly modified suppliers
    suppliers = Supplier.objects.filter(change_status__in=["active", "new_modified"])

    # Prepare a splitter to handle both commas and semicolons
    splitter = re.compile(r"[;,]")
    for sup in suppliers:
        # Convert each delimited string into a clean list
        sup.sm_list      = [s.strip() for s in splitter.split(sup.SocialMedia or '')    if s.strip()]
        sup.email_list   = [s.strip() for s in splitter.split(sup.EmailAddress or '')    if s.strip()]
        sup.contact_list = [s.strip() for s in splitter.split(sup.ContactNumber or '')  if s.strip()]
        sup.pp_list      = [s.strip() for s in splitter.split(sup.PointPerson or '')    if s.strip()]

    create_form = SupplierForm()
    return render(request, 'suppliers.html', {
        'suppliers': suppliers,
        'create_form': create_form,
    })

def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)

            splitter = re.compile(r'[;,]')

            # Re-join each of your array-style inputs back into a single string
            for field in ('SocialMedia', 'EmailAddress', 'ContactNumber'):
                raw_list = request.POST.getlist(f'{field}[]')
                clean    = [s.strip() for s in raw_list if s.strip()]
                setattr(supplier, field, '; '.join(clean))

            # PointPerson is a single field on your form, so just pull from cleaned_data
            supplier.PointPerson = form.cleaned_data.get('PointPerson', '').strip()
            
            # Get the use category from the form
            use_category = request.POST.get('UseCategory')
            
            # Set the appropriate category based on use category
            if use_category == 'Ingredients':
                supplier.Category = 'Ingredients'
            elif use_category == 'Packaging':  
                supplier.Category = 'Packaging'
            elif use_category == 'Both':
                supplier.Category = 'Both'
            
            supplier.save()
        else:
            messages.error(request, "Supplier creation error: " +
                           "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]))
    return redirect('suppliers_list')

def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            supplier = form.save(commit=False)
            
            # Get the use category from the form
            use_category = request.POST.get('UseCategory')
            
            # Set the appropriate category based on use category
            if use_category == 'Ingredients':
                supplier.Category = 'Ingredients'
            elif use_category == 'Packaging':
                supplier.Category = 'Packaging'
            elif use_category == 'Both':
                supplier.Category = 'Both'
            
                        # 3) Re-join your multi-input fields
            splitter = re.compile(r'[;,]')
            for field in ('SocialMedia','EmailAddress','ContactNumber'):
                raw_list = request.POST.getlist(f'{field}[]')
                clean    = [s.strip() for s in raw_list if s.strip()]
                setattr(supplier, field, '; '.join(clean))

            supplier.PointPerson = request.POST.get('PointPerson', '').strip()


            # 4) Mark it modified and persist
            supplier.change_status = 'active'
            supplier.save()
        else:
            msg = "Supplier update error: " + "; ".join(
                f"{fld}: {', '.join(errs)}"
                  for fld, errs in form.errors.items()
            )
            messages.error(request, msg)


    return redirect('suppliers_list')

def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        supplier.delete()
    return redirect('suppliers_list')

##########################
#  INGREDIENTS RAW MATERIALS  #
##########################
def ingredients_list(request):
    # Get all ingredients, ordered by date delivered (newest first)
    # and then by ID (newest first) for same-day entries
    ingredients = IngredientsRawMaterials.objects.filter(change_status='active').order_by('-DateDelivered', '-id')
    
    # Calculate total quantity available for each ingredient
    for ing in ingredients:
        # Get all records with same name
        matching_records = IngredientsRawMaterials.objects.filter(
            RawMaterialName=ing.RawMaterialName
        )
        
        if ing.UseCategory in ['GGB', 'WBC']:
            # For GGB/WBC: Get same category total + Both total
            same_category_total = matching_records.filter(
                UseCategory=ing.UseCategory
            ).aggregate(total=Sum('QuantityLeft'))['total'] or 0
            
            both_total = matching_records.filter(
                UseCategory='Both'
            ).aggregate(total=Sum('QuantityLeft'))['total'] or 0
            
            ing.TotalQuantityAvailable = same_category_total + both_total
            
        elif ing.UseCategory == 'Both':
            # For Both: Only show Both total
            both_total = matching_records.filter(
                UseCategory='Both'
            ).aggregate(total=Sum('QuantityLeft'))['total'] or 0
            
            ing.TotalQuantityAvailable = both_total
    
    # Get only active used ingredients
    used_ings = UsedIngredient.objects.filter(change_status='active')
    create_form = IngredientsRawMaterialsForm()
    used_ing_create_form = UsedIngredientForm()
    context = {
        'ingredients': ingredients,
        'used_ings': used_ings,
        'create_form': create_form,
        'used_ing_create_form': used_ing_create_form,
    }
    return render(request, 'ingredients.html', context)


def ingredients_create(request):
    if request.method == 'POST':
        form = IngredientsRawMaterialsForm(request.POST)
        if form.is_valid():
            # Simply save the new record with QuantityLeft = QuantityBought
            new_record = form.save(commit=False)
            new_record.QuantityLeft = new_record.QuantityBought  # Initial quantity left is same as bought
            new_record.save()
        else:
            messages.error(request, "Ingredient creation error: " +
                           "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]))
    return redirect('ingredients_list')

def ingredients_update(request, pk):
    ingredient = get_object_or_404(IngredientsRawMaterials, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = IngredientsRawMaterialsUpdateForm(request.POST, instance=ingredient)
        if form.is_valid():
            # Calculate used quantity for this specific batch
            total_used = UsedIngredient.objects.filter(
                IngredientRawMaterialBatchCode=ingredient
            ).aggregate(total=Sum('QuantityUsed'))['total'] or 0
            
            # Update only this record
            updated = form.save(commit=False)
            updated.QuantityLeft = max(updated.QuantityBought - total_used, 0)
            updated.save()
            
            return redirect('ingredients_list')
    else:
        form = IngredientsRawMaterialsUpdateForm(instance=ingredient)

    return render(request, 'ingredients_update.html', {
        'form': form,
        'ingredient': ingredient
    })

def ingredients_delete(request, pk):
    ingredient = get_object_or_404(IngredientsRawMaterials, pk=pk)

    if request.method == "POST":
        if request.POST.get("password") != PASSWORD:
            return HttpResponse("Incorrect password", status=403)

        # Get the details before deleting
        raw_name = ingredient.RawMaterialName
        use_category = ingredient.UseCategory
        
        # Delete the record
        ingredient.delete()

        # Find matching records with same name
        matching_records = IngredientsRawMaterials.objects.filter(
            RawMaterialName=raw_name
        )
        
        if matching_records.exists():
            if use_category in ['GGB', 'WBC']:
                # For GGB/WBC: Update only records of the same category
                same_category_records = matching_records.filter(UseCategory=use_category)
                
                # Calculate total from same category records
                same_category_total = same_category_records.aggregate(total=Sum('QuantityBought'))['total'] or 0
                
                # Get total from 'Both' records if they exist
                both_total = matching_records.filter(
                    UseCategory='Both'
                ).aggregate(total=Sum('QuantityBought'))['total'] or 0
                
                # Update all records of the same category with combined total
                final_total = same_category_total + both_total
                same_category_records.update(QuantityLeft=final_total)
                
            elif use_category == 'Both':
                # For Both: Update all categories
                # Update Both records
                both_records = matching_records.filter(UseCategory='Both')
                both_total = both_records.aggregate(total=Sum('QuantityBought'))['total'] or 0
                both_records.update(QuantityLeft=both_total)
                
                # Update GGB records if they exist
                ggb_records = matching_records.filter(UseCategory='GGB')
                if ggb_records.exists():
                    ggb_total = ggb_records.aggregate(total=Sum('QuantityBought'))['total'] or 0
                    ggb_records.update(QuantityLeft=ggb_total + both_total)
                
                # Update WBC records if they exist
                wbc_records = matching_records.filter(UseCategory='WBC')
                if wbc_records.exists():
                    wbc_total = wbc_records.aggregate(total=Sum('QuantityBought'))['total'] or 0
                    wbc_records.update(QuantityLeft=wbc_total + both_total)

    return redirect("ingredients_list")



def used_ingredients_create(request):
    if request.method == "POST":
        try:
            form = UsedIngredientForm(request.POST)
            if form.is_valid():
                used_ing = form.save(commit=False)
                used_ing.RawMaterialName = used_ing.IngredientRawMaterialBatchCode.RawMaterialName
                used_ing.change_status = 'active'
                
                # Get the quantity to subtract and use category
                quantity_to_subtract = used_ing.QuantityUsed
                use_category = used_ing.UseCategory
                raw_material_name = used_ing.RawMaterialName
                date_used = used_ing.DateUsed
                selected_material = used_ing.IngredientRawMaterialBatchCode

                # First try to subtract from the selected material
                if date_used < selected_material.DateDelivered:
                    return JsonResponse({
                        "status": "error",
                        "message": f"Date Used ({date_used}) cannot be before the Date Delivered ({selected_material.DateDelivered}) of the selected material."
                    }, status=400)

                # Check if selected material has enough quantity
                if selected_material.QuantityLeft >= quantity_to_subtract:
                    # If it has enough, just subtract from it
                    selected_material.QuantityLeft -= quantity_to_subtract
                    selected_material.save()
                    
                    used_ing.save()
                    return JsonResponse({
                        "status": "success",
                        "message": "Used ingredient record created successfully"
                    })
                
                # If we get here, we need to use cascading logic for remaining quantity
                # First subtract what we can from selected material
                amount_from_selected = min(quantity_to_subtract, selected_material.QuantityLeft)
                remaining_to_subtract = quantity_to_subtract - amount_from_selected
                
                if amount_from_selected > 0:
                    selected_material.QuantityLeft -= amount_from_selected
                    selected_material.save()
                    
                    # Create record for amount from selected material
                    UsedIngredient.objects.create(
                        IngredientRawMaterialBatchCode=selected_material,
                        RawMaterialName=raw_material_name,
                        QuantityUsed=amount_from_selected,
                        DateUsed=date_used,
                        UseCategory=use_category,
                        change_status='active'
                    )
                
                # Get available materials based on use category for remaining quantity
                available_materials = []
                if use_category == 'Both':
                    # For 'Both', only get 'Both' materials ordered by oldest first
                    available_materials = IngredientsRawMaterials.objects.filter(
                        RawMaterialName=raw_material_name,
                        UseCategory='Both',
                        change_status='active',
                        QuantityLeft__gt=0
                    ).exclude(id=selected_material.id).order_by('DateDelivered', 'id')
                else:
                    # For 'GGB' or 'WBC', get materials of same category first, then 'Both'
                    same_category_materials = IngredientsRawMaterials.objects.filter(
                        RawMaterialName=raw_material_name,
                        UseCategory=use_category,
                        change_status='active',
                        QuantityLeft__gt=0
                    ).exclude(id=selected_material.id).order_by('DateDelivered', 'id')
                    
                    both_materials = IngredientsRawMaterials.objects.filter(
                        RawMaterialName=raw_material_name,
                        UseCategory='Both',
                        change_status='active',
                        QuantityLeft__gt=0
                    ).exclude(id=selected_material.id).order_by('DateDelivered', 'id')
                    
                    available_materials = list(same_category_materials) + list(both_materials)
                
                # Validate date used against all materials
                for material in available_materials:
                    if date_used < material.DateDelivered:
                        return JsonResponse({
                            "status": "error",
                            "message": f"Date Used ({date_used}) cannot be before the Date Delivered ({material.DateDelivered}) of any material being subtracted from."
                        }, status=400)
                
                # Calculate total available quantity
                total_available = sum(material.QuantityLeft for material in available_materials)
                
                if total_available < remaining_to_subtract:
                    return JsonResponse({
                        "status": "error",
                        "message": f"Cannot subtract remaining {remaining_to_subtract} units. Only {total_available} units available across all applicable inventories."
                    }, status=400)
                
                # Perform the cascading subtraction for remaining quantity
                for material in available_materials:
                    if remaining_to_subtract <= 0:
                        break
                        
                    amount_from_this_material = min(remaining_to_subtract, material.QuantityLeft)
                    material.QuantityLeft -= amount_from_this_material
                    material.save()
                    
                    remaining_to_subtract -= amount_from_this_material
                    
                    # Create a used ingredient record for this subtraction
                    if amount_from_this_material > 0:
                        UsedIngredient.objects.create(
                            IngredientRawMaterialBatchCode=material,
                            RawMaterialName=raw_material_name,
                            QuantityUsed=amount_from_this_material,
                            DateUsed=date_used,
                            UseCategory=use_category,
                            change_status='active'
                        )
                
                return JsonResponse({
                    "status": "success",
                    "message": "Used ingredient records created successfully"
                })
            else:
                return JsonResponse({
                    "status": "error",
                    "message": "Validation failed",
                    "errors": {field: str(errors[0]) for field, errors in form.errors.items()}
                }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    return redirect('ingredients_list')

def used_ingredients_update(request, pk):
    used_ing = get_object_or_404(UsedIngredient, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = UsedIngredientForm(request.POST, instance=used_ing)
        if form.is_valid():
            form.save()
        else:
            messages.error(request, "Used ingredient update error: " +
                           "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]))
    return redirect('ingredients_list')

def used_ingredients_delete(request, pk):
    used_ing = get_object_or_404(UsedIngredient, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        
        try:
            # Add the quantity back to the ingredient
            ingredient = used_ing.IngredientRawMaterialBatchCode
            ingredient.QuantityLeft += used_ing.QuantityUsed
            ingredient.save()
            
            # Mark as deleted instead of actually deleting
            used_ing.change_status = 'deleted'
            used_ing.save()
            
            return JsonResponse({
                "status": "success",
                "message": "Used ingredient record deleted successfully"
            })
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Error deleting used ingredient record: {str(e)}"
            }, status=500)
    return redirect('ingredients_list')

##############################
#  PACKAGING RAW MATERIALS  #
##############################
def packaging_list(request):
    # Get all active packaging materials, ordered by date delivered (newest first)
    # and then by ID (newest first) for same-day entries
    materials = PackagingRawMaterials.objects.filter(change_status='active').order_by('-DateDelivered', '-id')
    
    # Calculate total quantity available for each packaging material
    for mat in materials:
        # Get all records with same name and container size
        matching_records = PackagingRawMaterials.objects.filter(
            RawMaterialName=mat.RawMaterialName,
            ContainerSize=mat.ContainerSize,
            change_status='active'
        )
        
        if mat.UseCategory in ['GGB', 'WBC']:
            # For GGB/WBC: Get same category total + Both total
            same_category_total = matching_records.filter(
                UseCategory=mat.UseCategory
            ).aggregate(total=Sum('QuantityLeft'))['total'] or 0
            
            both_total = matching_records.filter(
                UseCategory='Both'
            ).aggregate(total=Sum('QuantityLeft'))['total'] or 0
            
            mat.TotalQuantityAvailable = same_category_total + both_total
            
        elif mat.UseCategory == 'Both':
            # For Both: Only show Both total
            both_total = matching_records.filter(
                UseCategory='Both'
            ).aggregate(total=Sum('QuantityLeft'))['total'] or 0
            
            mat.TotalQuantityAvailable = both_total
    
    # Get only active used packaging, ordered by date used (newest first)
    # and then by batch code (newest first) for same-day entries
    used_packaging = UsedPackaging.objects.filter(change_status='active').order_by('-DateUsed', '-USEDPackagingBatchCode')
    create_form = PackagingRawMaterialsForm()
    used_packaging_create_form = UsedPackagingForm()
    context = {
        'materials': materials,
        'used_packaging': used_packaging,
        'create_form': create_form,
        'used_packaging_create_form': used_packaging_create_form,
    }
    return render(request, 'packaging.html', context)



def packaging_create(request):
    if request.method == 'POST':
        form = PackagingRawMaterialsForm(request.POST)
        if form.is_valid():
            # Simply save the new record with QuantityLeft = QuantityBought
            new_record = form.save(commit=False)
            new_record.QuantityLeft = new_record.QuantityBought  # Initial quantity left is same as bought
            new_record.save()
        else:
            messages.error(request, "Packaging creation error: " +
            "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]))
    return redirect('packaging_list')

def packaging_update(request, pk):
    material = get_object_or_404(PackagingRawMaterials, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return JsonResponse({
                "status": "error",
                "message": "Incorrect password"
            }, status=403)
            
        form = PackagingRawMaterialsUpdateForm(request.POST, instance=material)
        if form.is_valid():
            try:
                # Calculate used quantity for this specific batch
                total_used = UsedPackaging.objects.filter(
                    PackagingRawMaterialBatchCode=material
                ).aggregate(total=Sum('QuantityUsed'))['total'] or 0
                
                # Update only this record
                updated = form.save(commit=False)
                updated.QuantityLeft = max(updated.QuantityBought - total_used, 0)
                updated.save()
                
                return JsonResponse({
                    "status": "success",
                    "message": "Packaging material updated successfully"
                })
            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Error updating packaging material: {str(e)}"
                }, status=500)
        else:
            errors = {field: error[0] for field, error in form.errors.items()}
            return JsonResponse({
                "status": "error",
                "message": "Form validation failed",
                "errors": errors
            }, status=400)
    
    return JsonResponse({
        "status": "error",
        "message": "Invalid request method"
    }, status=405)

def packaging_delete(request, pk):
    packaging = get_object_or_404(PackagingRawMaterials, pk=pk)

    if request.method == "POST":
        if request.POST.get("password") != PASSWORD:
            return HttpResponse("Incorrect password", status=403)

        # Instead of deleting, mark as deleted
        packaging.change_status = 'deleted'
        packaging.save()

    return redirect("packaging_list")


def used_packaging_create(request):
    if request.method == "POST":
        try:
            form = UsedPackagingForm(request.POST)
            if form.is_valid():
                used_pack = form.save(commit=False)
                used_pack.RawMaterialName = used_pack.PackagingRawMaterialBatchCode.RawMaterialName
                used_pack.change_status = 'active'
                
                # Get the quantity to subtract and use category
                quantity_to_subtract = used_pack.QuantityUsed
                use_category = used_pack.UseCategory
                container_size = used_pack.PackagingRawMaterialBatchCode.ContainerSize
                raw_material_name = used_pack.RawMaterialName
                date_used = used_pack.DateUsed
                selected_material = used_pack.PackagingRawMaterialBatchCode

                # First try to subtract from the selected material
                if date_used < selected_material.DateDelivered:
                    return JsonResponse({
                        "status": "error",
                        "message": f"Date Used ({date_used}) cannot be before the Date Delivered ({selected_material.DateDelivered}) of the selected material."
                    }, status=400)

                # Check if selected material has enough quantity
                if selected_material.QuantityLeft >= quantity_to_subtract:
                    # If it has enough, just subtract from it
                    selected_material.QuantityLeft -= quantity_to_subtract
                    selected_material.save()
                    
                    used_pack.save()
                    return JsonResponse({
                        "status": "success",
                        "message": "Used packaging record created successfully"
                    })
                
                # If we get here, we need to use cascading logic for remaining quantity
                # First subtract what we can from selected material
                amount_from_selected = min(quantity_to_subtract, selected_material.QuantityLeft)
                remaining_to_subtract = quantity_to_subtract - amount_from_selected
                
                if amount_from_selected > 0:
                    selected_material.QuantityLeft -= amount_from_selected
                    selected_material.save()
                    
                    # Create record for amount from selected material
                    UsedPackaging.objects.create(
                        PackagingRawMaterialBatchCode=selected_material,
                        RawMaterialName=raw_material_name,
                        QuantityUsed=amount_from_selected,
                        DateUsed=date_used,
                        UseCategory=use_category,
                        change_status='active'
                    )
                
                # Get available materials based on use category for remaining quantity
                available_materials = []
                if use_category == 'Both':
                    # For 'Both', only get 'Both' materials ordered by oldest first
                    available_materials = PackagingRawMaterials.objects.filter(
                        RawMaterialName=raw_material_name,
                        ContainerSize=container_size,
                        UseCategory='Both',
                        change_status='active',
                        QuantityLeft__gt=0
                    ).exclude(id=selected_material.id).order_by('DateDelivered', 'id')
                else:
                    # For 'GGB' or 'WBC', get materials of same category first, then 'Both'
                    same_category_materials = PackagingRawMaterials.objects.filter(
                        RawMaterialName=raw_material_name,
                        ContainerSize=container_size,
                        UseCategory=use_category,
                        change_status='active',
                        QuantityLeft__gt=0
                    ).exclude(id=selected_material.id).order_by('DateDelivered', 'id')
                    
                    both_materials = PackagingRawMaterials.objects.filter(
                        RawMaterialName=raw_material_name,
                        ContainerSize=container_size,
                        UseCategory='Both',
                        change_status='active',
                        QuantityLeft__gt=0
                    ).exclude(id=selected_material.id).order_by('DateDelivered', 'id')
                    
                    available_materials = list(same_category_materials) + list(both_materials)
                
                # Validate date used against all materials
                for material in available_materials:
                    if date_used < material.DateDelivered:
                        return JsonResponse({
                            "status": "error",
                            "message": f"Date Used ({date_used}) cannot be before the Date Delivered ({material.DateDelivered}) of any material being subtracted from."
                        }, status=400)
                
                # Calculate total available quantity
                total_available = sum(material.QuantityLeft for material in available_materials)
                
                if total_available < remaining_to_subtract:
                    return JsonResponse({
                        "status": "error",
                        "message": f"Cannot subtract remaining {remaining_to_subtract} units. Only {total_available} units available across all applicable inventories."
                    }, status=400)
                
                # Perform the cascading subtraction for remaining quantity
                for material in available_materials:
                    if remaining_to_subtract <= 0:
                        break
                        
                    amount_from_this_material = min(remaining_to_subtract, material.QuantityLeft)
                    material.QuantityLeft -= amount_from_this_material
                    material.save()
                    
                    remaining_to_subtract -= amount_from_this_material
                    
                    # Create a used packaging record for this subtraction
                    if amount_from_this_material > 0:
                        UsedPackaging.objects.create(
                            PackagingRawMaterialBatchCode=material,
                            RawMaterialName=raw_material_name,
                            QuantityUsed=amount_from_this_material,
                            DateUsed=date_used,
                            UseCategory=use_category,
                            change_status='active'
                        )
                
                return JsonResponse({
                    "status": "success",
                    "message": "Used packaging records created successfully"
                })
            else:
                return JsonResponse({
                    "status": "error",
                    "message": "Validation failed",
                    "errors": {field: str(errors[0]) for field, errors in form.errors.items()}
                }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    return redirect('packaging_list')

def used_packaging_update(request, pk):
    used_pack = get_object_or_404(UsedPackaging, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = UsedPackagingForm(request.POST, instance=used_pack)
        if form.is_valid():
            form.save()
        else:
            messages.error(request, "Used packaging update error: " +
                           "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]))
    return redirect('packaging_list')

def used_packaging_delete(request, pk):
    used_pack = get_object_or_404(UsedPackaging, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        
        try:
            # Add the quantity back to the packaging
            packaging = used_pack.PackagingRawMaterialBatchCode
            packaging.QuantityLeft += used_pack.QuantityUsed
            packaging.save()
            
            # Mark as deleted instead of actually deleting
            used_pack.change_status = 'deleted'
            used_pack.save()
            
            return JsonResponse({
                "status": "success",
                "message": "Used packaging record deleted successfully"
            })
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Error deleting used packaging record: {str(e)}"
            }, status=500)
    return redirect('packaging_list')

##########################
#     REPORT SUMMARY      #
##########################
def report_summary(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    used_ing = []
    used_pack = []
    exp_ing = []

    if start_date and end_date:
        # total used
        used_ing = (UsedIngredient.objects
                    .filter(DateUsed__range=[start_date, end_date])
                    .values('RawMaterialName')
                    .annotate(total_used=Sum('QuantityUsed')))
        used_pack = (UsedPackaging.objects
                     .filter(DateUsed__range=[start_date, end_date])
                     .values('RawMaterialName')
                     .annotate(total_used=Sum('QuantityUsed')))

        # calculate expired and remaining
        # sum up quantity left at the moment of expiry
        expired_qs = (IngredientsRawMaterials.objects
                     .filter(ExpirationDate__range=[start_date, end_date])
                     .values('RawMaterialName')
                     .annotate(expired_qty=Sum('QuantityLeft')))

        # sum up quantity left outside that expiry window
        remaining_qs = (IngredientsRawMaterials.objects
                       .exclude(ExpirationDate__range=[start_date, end_date])
                       .values('RawMaterialName')
                       .annotate(remaining_qty=Sum('QuantityLeft')))

        # merge the two querysets into exp_ing list of dicts
        exp_ing = []
        # build a map for remaining
        rem_map = {r['RawMaterialName']: r['remaining_qty'] for r in remaining_qs}
        for e in expired_qs:
            name = e['RawMaterialName']
            exp_qty = e['expired_qty']
            rem_qty = rem_map.get(name, 0)
            exp_ing.append({
                'RawMaterialName': name,
                'expired_qty': exp_qty,
                'remaining_qty': rem_qty
            })
    return render(request, 'report_summary.html', {
        'used_ing': used_ing,
        'used_pack': used_pack,
        'exp_ing': exp_ing,
        'start_date': start_date,
        'end_date': end_date,
    })

def supplier_list_packaging(request):
    suppliers = Supplier.objects.filter(
        Category__in=['Packaging', 'Both']
    ).values('SupplierCode', 'SupplierName')
    return JsonResponse({'suppliers': list(suppliers)}, safe=False)

def supplier_list_ingredients(request):
    suppliers = Supplier.objects.filter(
        Category__in=['Ingredient', 'Both']
    ).values('SupplierCode', 'SupplierName')
    return JsonResponse({'suppliers': list(suppliers)}, safe=False)

# IMAPS_app/views.py

from django.shortcuts import render
from auditlog.models import LogEntry

def audit_log_list(request):
    entries = (
        LogEntry.objects
        .select_related('content_type')
        .order_by('-timestamp')[:100]
    )
    return render(request, 'audit_log_list.html', {'entries': entries})
