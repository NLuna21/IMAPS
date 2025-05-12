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
def suppliers_list(request):
    suppliers = Supplier.objects.all()
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
        supplier.delete()
    return redirect('suppliers_list')

##########################
#  INGREDIENTS RAW MATERIALS  #
##########################
def ingredients_list(request):
    ingredients = IngredientsRawMaterials.objects.all()
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
            existing_batch = form.cleaned_data.get('existing_batch')
            quantity_bought = form.cleaned_data.get('QuantityBought')
            if existing_batch and existing_batch != 'None':
                try:
                    # Get the existing record (assumed to be unique by batch code)
                    existing_record = IngredientsRawMaterials.objects.get(RawMaterialBatchCode=existing_batch)
                    
                    # Create a new record but don’t save yet:
                    new_record = form.save(commit=False)
                    # The new record’s QuantityLeft should be just its own QuantityBought
                    # before combining; then we compute the new total:
                    new_record.QuantityLeft = new_record.QuantityBought
                    new_record.save()
                    
                    # Now compute the combined quantity left:
                    combined = existing_record.QuantityLeft + new_record.QuantityLeft
                    # Update both records to show the same combined total.
                    existing_record.QuantityLeft = combined
                    existing_record.save()
                    
                    new_record.QuantityLeft = combined
                    new_record.save()
                except IngredientsRawMaterials.DoesNotExist:
                    form.save()
            else:
                form.save()
        else:
            messages.error(request, "Ingredient creation error: " +
                           "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]))
            pass
    return redirect('ingredients_list')

def ingredients_update(request, pk):
    ingredient = get_object_or_404(IngredientsRawMaterials, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = IngredientsRawMaterialsUpdateForm(request.POST, instance=ingredient)
        if form.is_valid():
            updated = form.save()   # persists DateDelivered, ExpirationDate, etc.
            # recompute QuantityLeft across all batches
            batches = IngredientsRawMaterials.objects.filter(
                RawMaterialName=updated.RawMaterialName
            )
            total_bought = batches.aggregate(total=Sum('QuantityBought'))['total'] or 0
            total_used   = UsedIngredient.objects.filter(
                RawMaterialName=updated.RawMaterialName
            ).aggregate(total=Sum('QuantityUsed'))['total'] or 0
            new_left = max(total_bought - total_used, 0)
            batches.update(QuantityLeft=new_left)
            return redirect('ingredients_list')
    else:
        # GET → prepopulate form (including date widget)
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

        raw_name = ingredient.RawMaterialName        # ① remember the family
        ingredient.delete()                          # ② remove the row

        # ③–④ recalc QuantityLeft across the survivors
        batches = IngredientsRawMaterials.objects.filter(RawMaterialName=raw_name)
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
    materials = PackagingRawMaterials.objects.all()
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
            existing_batch = form.cleaned_data.get('existing_batch')
            quantity_bought = form.cleaned_data.get('QuantityBought')
            if existing_batch and existing_batch != 'None':
                try:
                    # Get the existing packaging record by its batch code.
                    existing_record = PackagingRawMaterials.objects.get(PackagingBatchCode=existing_batch)
                    
                    # Create a new record from the form but do not save yet.
                    new_record = form.save(commit=False)
                    
                    # Override the following fields with the values from the existing record.
                    new_record.ContainerSize = existing_record.ContainerSize
                    new_record.RawMaterialName = existing_record.RawMaterialName
                    new_record.UseCategory = existing_record.UseCategory
                    # Ensure the new record's QuantityLeft starts as its own QuantityBought.
                    new_record.QuantityLeft = new_record.QuantityBought
                    new_record.save()
                    
                    # Calculate the combined available quantity.
                    combined_quantity = existing_record.QuantityLeft + new_record.QuantityLeft
                    # Update both records to share the new combined quantity.
                    existing_record.QuantityLeft = combined_quantity
                    existing_record.save()
                    
                    new_record.QuantityLeft = combined_quantity
                    new_record.save()
                except PackagingRawMaterials.DoesNotExist:
                    form.save()
            else:
                form.save()
        else:
            messages.error(request, "Packaging creation error: " +
            "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]))
            pass
    return redirect('packaging_list')

def packaging_update(request, pk):
    material = get_object_or_404(PackagingRawMaterials, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = PackagingRawMaterialsUpdateForm(request.POST, instance=material)
        if form.is_valid():
            updated = form.save()   # persists DateDelivered, ContainerSize, etc.
            # recompute QuantityLeft across all packaging batches
            batches = PackagingRawMaterials.objects.filter(
                RawMaterialName=updated.RawMaterialName
            )
            total_bought = batches.aggregate(total=Sum('QuantityBought'))['total'] or 0
            total_used   = UsedPackaging.objects.filter(
                RawMaterialName=updated.RawMaterialName
            ).aggregate(total=Sum('QuantityUsed'))['total'] or 0
            new_left = max(total_bought - total_used, 0)
            batches.update(QuantityLeft=new_left)
            return redirect('packaging_list')
    else:
        # GET → prepopulate form
        form = PackagingRawMaterialsUpdateForm(instance=material)

    return render(request, 'packaging_update.html', {
        'form': form,
        'material': material
    })

def packaging_delete(request, pk):
    packaging = get_object_or_404(PackagingRawMaterials, pk=pk)

    if request.method == "POST":
        if request.POST.get("password") != PASSWORD:
            return HttpResponse("Incorrect password", status=403)

        raw_name = packaging.RawMaterialName          # ① remember the family
        packaging.delete()                            # ② remove the row

        # ③ – ④ recalc QuantityLeft across remaining batches
        batches = PackagingRawMaterials.objects.filter(RawMaterialName=raw_name)
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
            # Auto-fill the name from the selected batch
            used_pack.RawMaterialName = (
                used_pack.PackagingRawMaterialBatchCode.RawMaterialName
            )
            used_pack.save()                      # now the row is persisted

            # --- 2. Recompute the running balance ---------------------------
            # Every batch for this packaging material mirrors the *same* balance,
            # so read QuantityLeft from any one of them (first()).
            batches = PackagingRawMaterials.objects.filter(
                RawMaterialName=used_pack.RawMaterialName
            )
            current_balance = batches.first().QuantityLeft if batches.exists() else 0
            new_balance = max(current_balance - used_pack.QuantityUsed, 0)

            # Update all sibling batches to reflect the new balance in one go
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
