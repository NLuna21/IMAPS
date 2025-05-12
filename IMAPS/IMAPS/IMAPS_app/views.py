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
    UsedPackaging,
    ChangeLog
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
def suppliers_list(request):
    suppliers = Supplier.objects.filter(change_status='active')
    create_form = SupplierForm()
    return render(request, 'suppliers.html', {
        'suppliers': suppliers,
        'create_form': create_form,
    })

def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
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
            form.save()
        else:
            messages.error(request, "Supplier update error: " +
                           "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]))
    return redirect('suppliers_list')

def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        
        # Instead of deleting, mark as deleted and log the change
        supplier.change_status = 'deleted'
        supplier.save()
        
        ChangeLog.objects.create(
            table_name='Supplier',
            column='change_status',
            prev='active',
            new='deleted'
        )
    return redirect('suppliers_list')

##########################
#  INGREDIENTS RAW MATERIALS  #
##########################
def ingredients_list(request):
    ingredients = IngredientsRawMaterials.objects.filter(change_status='active')
    used_ings = UsedIngredient.objects.all()
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
            # Create the new record
            new_record = form.save(commit=False)
            raw_material_name = new_record.RawMaterialName
            use_category = new_record.UseCategory
            
            # Set initial QuantityLeft to QuantityBought for the new record
            new_record.QuantityLeft = new_record.QuantityBought
            new_record.save()
            
            if use_category == 'Both':
                # For Both, only consider other Both records
                both_records = IngredientsRawMaterials.objects.filter(
                    RawMaterialName=raw_material_name,
                    change_status='active',
                    UseCategory='Both'  # Only Both records
                )
                
                # Calculate totals for Both category only
                total_bought = (
                    both_records.aggregate(total=Sum('QuantityBought'))['total'] or 0
                )
                total_used = UsedIngredient.objects.filter(
                    RawMaterialName=raw_material_name,
                    UseCategory='Both'  # Only Both usage
                ).aggregate(total=Sum('QuantityUsed'))['total'] or 0
                
                new_quantity_left = max(total_bought - total_used, 0)
                # Update all categories
                all_records = IngredientsRawMaterials.objects.filter(
                    RawMaterialName=raw_material_name,
                    change_status='active'
                )
                all_records.update(QuantityLeft=new_quantity_left)
                
            else:
                # For WBC or GGB, include quantities from Both category
                both_records = IngredientsRawMaterials.objects.filter(
                    RawMaterialName=raw_material_name,
                    change_status='active',
                    UseCategory='Both'
                )
                category_records = IngredientsRawMaterials.objects.filter(
                    RawMaterialName=raw_material_name,
                    change_status='active',
                    UseCategory=use_category
                )
                
                # Calculate totals including Both category
                both_bought = both_records.aggregate(total=Sum('QuantityBought'))['total'] or 0
                category_bought = category_records.aggregate(total=Sum('QuantityBought'))['total'] or 0
                total_bought = both_bought + category_bought
                
                both_used = UsedIngredient.objects.filter(
                    RawMaterialName=raw_material_name,
                    UseCategory='Both'
                ).aggregate(total=Sum('QuantityUsed'))['total'] or 0
                
                category_used = UsedIngredient.objects.filter(
                    RawMaterialName=raw_material_name,
                    UseCategory=use_category
                ).aggregate(total=Sum('QuantityUsed'))['total'] or 0
                
                total_used = both_used + category_used
                
                new_quantity_left = max(total_bought - total_used, 0)
                # Only update the specific category records
                category_records.update(QuantityLeft=new_quantity_left)

            # Log the creation
            ChangeLog.objects.create(
                table_name='IngredientsRawMaterials',
                column='QuantityLeft',
                prev='0',
                new=str(new_quantity_left),
                item_pk=new_record.pk,
                item_name=f"{raw_material_name} ({use_category})"
            )
        else:
            messages.error(request, "Ingredient creation error: " +
                         "; ".join([f"{field}: {', '.join(errors)}" 
                                  for field, errors in form.errors.items()]))
    return redirect('ingredients_list')

def ingredients_update(request, pk):
    ingredient = get_object_or_404(IngredientsRawMaterials, pk=pk, change_status='active')
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = IngredientsRawMaterialsUpdateForm(request.POST, instance=ingredient)
        if form.is_valid():
            print("Form is valid")  # Debug print
            # Get the cleaned form data
            cleaned_data = form.cleaned_data
            print("Cleaned data:", cleaned_data)  # Debug print
            
            # Store old values before update
            old_values = {
                'RawMaterialName': ingredient.RawMaterialName,
                'SupplierCode': ingredient.SupplierCode,
                'DateDelivered': ingredient.DateDelivered,
                'QuantityBought': ingredient.QuantityBought,
                'UseCategory': ingredient.UseCategory,
                'ExpirationDate': ingredient.ExpirationDate,
                'Status': ingredient.Status,
                'Cost': ingredient.Cost,
                'change_status': ingredient.change_status
            }
            print("Old values:", old_values)  # Debug print
            
            # Save the form
            updated = form.save(commit=False)
            updated.change_status = 'active'  # Ensure status remains active
            updated.save()
            
            # Compare old and new values from the form data
            for field, old_value in old_values.items():
                if field in cleaned_data:
                    new_value = cleaned_data[field]
                    print(f"Comparing {field}: old={old_value}, new={new_value}")  # Debug print
                    # Special handling for foreign key fields
                    if field == 'SupplierCode':
                        old_value = str(old_value)
                        new_value = str(new_value)
                    # Compare and log if different
                    if str(old_value) != str(new_value):
                        print(f"Creating log for {field}")  # Debug print
                        ChangeLog.objects.create(
                            table_name='ingredients_raw_materials',
                            column=field,
                            prev=str(old_value),
                            new=str(new_value),
                            item_pk=pk,
                            item_name=updated.RawMaterialName
                        )
            
            # recompute QuantityLeft across all batches
            batches = IngredientsRawMaterials.objects.filter(
                RawMaterialName=updated.RawMaterialName,
                change_status='active'
            )
            total_bought = batches.aggregate(total=Sum('QuantityBought'))['total'] or 0
            total_used = UsedIngredient.objects.filter(
                RawMaterialName=updated.RawMaterialName
            ).aggregate(total=Sum('QuantityUsed'))['total'] or 0
            new_left = max(total_bought - total_used, 0)
            
            # Log QuantityLeft change if it changed
            old_quantity_left = ingredient.QuantityLeft
            if old_quantity_left != new_left:
                print(f"Creating log for QuantityLeft")  # Debug print
                ChangeLog.objects.create(
                    table_name='ingredients_raw_materials',
                    column='QuantityLeft',
                    prev=str(old_quantity_left),
                    new=str(new_left),
                    item_pk=pk,
                    item_name=updated.RawMaterialName
                )
            
            batches.update(QuantityLeft=new_left)
        else:
            print("Form errors:", form.errors)  # Debug print
            messages.error(request, "Ingredient update error: " +
                           "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]))
    return redirect('ingredients_list')

def ingredients_delete(request, pk):
    ingredient = get_object_or_404(IngredientsRawMaterials, pk=pk)

    if request.method == "POST":
        if request.POST.get("password") != PASSWORD:
            return HttpResponse("Incorrect password", status=403)

        raw_name = ingredient.RawMaterialName        # ① remember the family
        
        # Instead of deleting, mark as deleted and log the change
        ingredient.change_status = 'deleted'
        ingredient.save()
        
        ChangeLog.objects.create(
            table_name='IngredientsRawMaterials',
            column='change_status',
            prev='active',
            new='deleted'
        )

        # ③–④ recalc QuantityLeft across the survivors (only active records)
        batches = IngredientsRawMaterials.objects.filter(
            RawMaterialName=raw_name,
            change_status='active'  # Only consider active records
        )
        if batches.exists():
            total_bought = batches.aggregate(t=Sum("QuantityBought"))["t"] or 0
            total_used   = UsedIngredient.objects.filter(
                               RawMaterialName=raw_name
                           ).aggregate(t=Sum("QuantityUsed"))["t"] or 0
            new_left = max(total_bought - total_used, 0)
            batches.update(QuantityLeft=new_left)

    return redirect("ingredients_list")



def used_ingredients_create(request):
    if request.method == 'POST':
        form = UsedIngredientForm(request.POST)
        if form.is_valid():
            used_ing = form.save()
            # Get all ingredient records for the same raw material name.
            qs = IngredientsRawMaterials.objects.filter(RawMaterialName=used_ing.RawMaterialName)
            total_left = sum(record.QuantityLeft for record in qs)
            new_total = total_left - used_ing.QuantityUsed
            if new_total < 0:
                new_total = 0
            # Update all records with this new total so they show the same remaining balance.
            for record in qs:
                record.QuantityLeft = new_total
                record.save()
        else:
            messages.error(request, "Used ingredient creation error: " +
                           "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]))
            pass
    return redirect('ingredients_list')

def used_ingredients_create(request):
    if request.method == "POST":
        form = UsedIngredientForm(request.POST)
        if form.is_valid():
            # 1️⃣  Save later so we can fill-in RawMaterialName automatically
            used_ing = form.save(commit=False)
            used_ing.RawMaterialName = (
                used_ing.IngredientRawMaterialBatchCode.RawMaterialName
            )
            used_ing.save()                  # now the UsedIngredient row exists

            # 2️⃣  Recompute the shared running balance for this ingredient
            batches = IngredientsRawMaterials.objects.filter(
                RawMaterialName=used_ing.RawMaterialName
            )
            current_balance = (
                batches.first().QuantityLeft if batches.exists() else 0
            )
            new_balance = max(current_balance - used_ing.QuantityUsed, 0)

            # 3️⃣  Propagate the new balance to every sibling batch in one query
            batches.update(QuantityLeft=new_balance)
        else:
            messages.error(
                request,
                "Used ingredient creation error: "
                + "; ".join(
                    f"{field}: {', '.join(errs)}"
                    for field, errs in form.errors.items()
                ),
            )
    return redirect("ingredients_list")

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
        ingredient = used_ing.IngredientRawMaterialBatchCode
        ingredient.QuantityLeft += used_ing.QuantityUsed
        ingredient.save()
        used_ing.delete()
    return redirect('ingredients_list')

##############################
#  PACKAGING RAW MATERIALS  #
##############################
def packaging_list(request):
    materials = PackagingRawMaterials.objects.filter(change_status='active')
    used_packs = UsedPackaging.objects.all()
    create_form = PackagingRawMaterialsForm()
    used_pack_create_form = UsedPackagingForm()
    context = {
        'materials': materials,
        'used_packs': used_packs,
        'create_form': create_form,
        'used_pack_create_form': used_pack_create_form,
    }
    return render(request, 'packaging.html', context)



def packaging_create(request):
    if request.method == 'POST':
        form = PackagingRawMaterialsForm(request.POST)
        if form.is_valid():
            # Create the new record
            new_record = form.save(commit=False)
            raw_material_name = new_record.RawMaterialName
            container_size = new_record.ContainerSize
            use_category = new_record.UseCategory
            
            # Set initial QuantityLeft to QuantityBought for the new record
            new_record.QuantityLeft = new_record.QuantityBought
            new_record.save()
            
            if use_category == 'Both':
                # For Both, only consider Both records (including the new one)
                both_records = PackagingRawMaterials.objects.filter(
                    RawMaterialName=raw_material_name,
                    ContainerSize=container_size,
                    change_status='active',
                    UseCategory='Both'  # Only Both records
                )
                
                # Calculate totals for Both category only
                total_bought = (
                    both_records.aggregate(total=Sum('QuantityBought'))['total'] or 0
                )
                total_used = UsedPackaging.objects.filter(
                    RawMaterialName=raw_material_name,
                    PackagingRawMaterialBatchCode__ContainerSize=container_size,
                    UseCategory='Both'  # Only Both usage
                ).aggregate(total=Sum('QuantityUsed'))['total'] or 0
                
                new_quantity_left = max(total_bought - total_used, 0)
                
                # Only update Both records
                both_records.update(QuantityLeft=new_quantity_left)
            else:
                # For WBC or GGB, include quantities from Both category
                both_records = PackagingRawMaterials.objects.filter(
                    RawMaterialName=raw_material_name,
                    ContainerSize=container_size,
                    change_status='active',
                    UseCategory='Both'
                )
                category_records = PackagingRawMaterials.objects.filter(
                    RawMaterialName=raw_material_name,
                    ContainerSize=container_size,
                    change_status='active',
                    UseCategory=use_category
                )
                
                # Calculate totals including Both category
                both_bought = both_records.aggregate(total=Sum('QuantityBought'))['total'] or 0
                category_bought = category_records.aggregate(total=Sum('QuantityBought'))['total'] or 0
                total_bought = both_bought + category_bought
                
                both_used = UsedPackaging.objects.filter(
                    RawMaterialName=raw_material_name,
                    PackagingRawMaterialBatchCode__ContainerSize=container_size,
                    UseCategory='Both'
                ).aggregate(total=Sum('QuantityUsed'))['total'] or 0
                
                category_used = UsedPackaging.objects.filter(
                    RawMaterialName=raw_material_name,
                    PackagingRawMaterialBatchCode__ContainerSize=container_size,
                    UseCategory=use_category
                ).aggregate(total=Sum('QuantityUsed'))['total'] or 0
                
                total_used = both_used + category_used
                
                new_quantity_left = max(total_bought - total_used, 0)
                # Only update the specific category records
                category_records.update(QuantityLeft=new_quantity_left)

            # Log the creation
            ChangeLog.objects.create(
                table_name='PackagingRawMaterials',
                column='QuantityLeft',
                prev='0',
                new=str(new_quantity_left),
                item_pk=new_record.pk,
                item_name=f"{raw_material_name} - {container_size} ({use_category})"
            )
        else:
            messages.error(request, "Packaging creation error: " +
                         "; ".join([f"{field}: {', '.join(errors)}" 
                                  for field, errors in form.errors.items()]))
    return redirect('packaging_list')

def packaging_update(request, pk):
    material = get_object_or_404(PackagingRawMaterials, pk=pk, change_status='active')
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = PackagingRawMaterialsUpdateForm(request.POST, instance=material)
        if form.is_valid():
            print("Form is valid")  # Debug print
            # Get the cleaned form data
            cleaned_data = form.cleaned_data
            print("Cleaned data:", cleaned_data)  # Debug print
            
            # Store old values before update
            old_values = {
                'RawMaterialName': material.RawMaterialName,
                'SupplierCode': material.SupplierCode,
                'ContainerSize': material.ContainerSize,
                'DateDelivered': material.DateDelivered,
                'QuantityBought': material.QuantityBought,
                'UseCategory': material.UseCategory,
                'Status': material.Status,
                'Cost': material.Cost,
                'change_status': material.change_status
            }
            print("Old values:", old_values)  # Debug print
            
            # Save the form
            updated = form.save(commit=False)
            updated.change_status = 'active'  # Ensure status remains active
            updated.save()
            
            # Compare old and new values from the form data
            for field, old_value in old_values.items():
                if field in cleaned_data:
                    new_value = cleaned_data[field]
                    print(f"Comparing {field}: old={old_value}, new={new_value}")  # Debug print
                    # Special handling for foreign key fields
                    if field == 'SupplierCode':
                        old_value = str(old_value)
                        new_value = str(new_value)
                    # Compare and log if different
                    if str(old_value) != str(new_value):
                        print(f"Creating log for {field}")  # Debug print
                        ChangeLog.objects.create(
                            table_name='packaging',
                            column=field,
                            prev=str(old_value),
                            new=str(new_value),
                            item_pk=pk,
                            item_name=updated.RawMaterialName
                        )
            
            # recompute QuantityLeft across all packaging batches
            batches = PackagingRawMaterials.objects.filter(
                RawMaterialName=updated.RawMaterialName,
                change_status='active'
            )
            total_bought = batches.aggregate(total=Sum('QuantityBought'))['total'] or 0
            total_used = UsedPackaging.objects.filter(
                RawMaterialName=updated.RawMaterialName
            ).aggregate(total=Sum('QuantityUsed'))['total'] or 0
            new_left = max(total_bought - total_used, 0)
            
            # Log QuantityLeft change if it changed
            old_quantity_left = material.QuantityLeft
            if old_quantity_left != new_left:
                print(f"Creating log for QuantityLeft")  # Debug print
                ChangeLog.objects.create(
                    table_name='packaging',
                    column='QuantityLeft',
                    prev=str(old_quantity_left),
                    new=str(new_left),
                    item_pk=pk,
                    item_name=updated.RawMaterialName
                )
            
            batches.update(QuantityLeft=new_left)
        else:
            print("Form errors:", form.errors)  # Debug print
            messages.error(request, "Packaging update error: " +
                           "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]))
    return redirect('packaging_list')

def packaging_delete(request, pk):
    packaging = get_object_or_404(PackagingRawMaterials, pk=pk)

    if request.method == "POST":
        if request.POST.get("password") != PASSWORD:
            return HttpResponse("Incorrect password", status=403)

        raw_name = packaging.RawMaterialName          # ① remember the family
        
        # Instead of deleting, mark as deleted and log the change
        packaging.change_status = 'deleted'
        packaging.save()
        
        ChangeLog.objects.create(
            table_name='PackagingRawMaterials',
            column='change_status',
            prev='active',
            new='deleted'
        )

        # ③ – ④ recalc QuantityLeft across remaining batches (only active records)
        batches = PackagingRawMaterials.objects.filter(
            RawMaterialName=raw_name,
            change_status='active'  # Only consider active records
        )
        if batches.exists():
            total_bought = batches.aggregate(t=Sum("QuantityBought"))["t"] or 0
            total_used   = UsedPackaging.objects.filter(
                               RawMaterialName=raw_name
                           ).aggregate(t=Sum("QuantityUsed"))["t"] or 0
            new_left = max(total_bought - total_used, 0)
            batches.update(QuantityLeft=new_left)

    return redirect("packaging_list")


def used_packaging_create(request):
    if request.method == 'POST':
        form = UsedPackagingForm(request.POST)
        if form.is_valid():
            # --- 1. Save but let us tweak fields first -----------------------
            used_pack = form.save(commit=False)

            used_pack.RawMaterialName = (
                used_pack.PackagingRawMaterialBatchCode.RawMaterialName
            )
            used_pack.change_status = 'active'  # Set default change_status
            used_pack.save()  # now the row is persisted

            # --- 2. Recompute the running balance ---------------------------
            # Every batch for this packaging material mirrors the *same* balance,
            # so read QuantityLeft from any one of them (first()).
            batches = PackagingRawMaterials.objects.filter(
                RawMaterialName=used_pack.RawMaterialName
            )
            current_balance = batches.first().QuantityLeft if batches.exists() else 0
            new_balance = max(current_balance - used_pack.QuantityUsed, 0)

            batches.update(QuantityLeft=new_balance)
        else:
            messages.error(
                request,
                "Used packaging creation error: " +
                "; ".join(f"{field}: {', '.join(errs)}"
                          for field, errs in form.errors.items())
            )
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
        packaging = used_pack.PackagingRawMaterialBatchCode
        packaging.QuantityLeft += used_pack.QuantityUsed
        packaging.save()
        used_pack.delete()
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
        Category__in=['Packaging', 'Both'],
        change_status='active'  # Only show active suppliers
    ).values('SupplierCode', 'SupplierName')
    return JsonResponse({'suppliers': list(suppliers)}, safe=False)

def supplier_list_ingredients(request):
    suppliers = Supplier.objects.filter(
        Category__in=['Ingredient', 'Both'],
        change_status='active'  # Only show active suppliers
    ).values('SupplierCode', 'SupplierName')
    return JsonResponse({'suppliers': list(suppliers)}, safe=False)

from django.shortcuts import render, redirect
from django.contrib   import messages

def change_log_create(request):
    if request.method == 'POST':
        table_name = request.POST.get('table_name')
        column = request.POST.get('column')
        prev = request.POST.get('prev')
        new = request.POST.get('new')
        item_pk = request.POST.get('item_pk')
        item_name = request.POST.get('item_name')

        if not (table_name and column):
            messages.error(request, "Missing table_name or column.")
        else:
            ChangeLog.objects.create(
                table_name=table_name,
                column=column,
                prev=prev,
                new=new,
                item_pk=item_pk,
                item_name=item_name
            )
    # return to wherever you came from; or default to ingredients history
    return redirect(request.META.get('HTTP_REFERER', 'history_ingredients_list'))

def history_ingredients_list(request):
    """
    Read‐only view: all ChangeLog entries for ingredients.
    """
    logs = ChangeLog.objects.filter(
        table_name='ingredients_raw_materials'
    ).order_by('-date')
    return render(request, 'history_ingredients_list.html', {'logs': logs})

def history_packaging_list(request):
    """
    Read‐only view: all ChangeLog entries for packaging.
    """
    logs = ChangeLog.objects.filter(
        table_name='packaging'
    ).order_by('-date')
    return render(request, 'history_packaging_list.html', {'logs': logs})
