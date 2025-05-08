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
    IngredientsRawMaterialsUpdateForm,
    PackagingRawMaterialsUpdateForm
)

PASSWORD = "test123"

# ================= SUPPLIERS =================

def suppliers_list(request):
    suppliers = Supplier.objects.filter(change_status__in=["active", "new_modified"])
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
            messages.error(request,
                "Supplier creation error: " +
                "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            )
    return redirect('suppliers_list')

def supplier_update(request, pk):
    old = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = SupplierForm(request.POST)
        if form.is_valid():
            old.change_status = "old_modified"
            old.save()
            new = form.save(commit=False)
            new.change_status = "new_modified"
            new.save()
        else:
            messages.error(request,
                "Supplier update error: " +
                "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            )
    return redirect('suppliers_list')

def supplier_delete(request, pk):
    obj = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        obj.change_status = "deleted"
        obj.save()
    return redirect('suppliers_list')


# =============== INGREDIENTS ===============

def ingredients_list(request):
    ingredients = IngredientsRawMaterials.objects.filter(change_status__in=["active", "new_modified"])
    used_ings = UsedIngredient.objects.filter(change_status__in=["active", "new_modified"])
    return render(request, 'ingredients.html', {
        'ingredients': ingredients,
        'used_ings': used_ings,
        'create_form': IngredientsRawMaterialsForm(),
        'used_ing_create_form': UsedIngredientForm(),
    })

def ingredients_create(request):
    if request.method == 'POST':
        form = IngredientsRawMaterialsForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            messages.error(request,
                "Ingredient creation error: " +
                "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            )
    return redirect('ingredients_list')

def ingredients_update(request, pk):
    old = get_object_or_404(IngredientsRawMaterials, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = IngredientsRawMaterialsUpdateForm(request.POST)
        if form.is_valid():
            old.change_status = "old_modified"
            old.save()
            new = form.save(commit=False)
            new.change_status = "new_modified"
            new.save()
        else:
            messages.error(request,
                "Ingredient update error: " +
                "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            )
    return redirect('ingredients_list')

def ingredients_delete(request, pk):
    obj = get_object_or_404(IngredientsRawMaterials, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        obj.change_status = "deleted"
        obj.save()
    return redirect('ingredients_list')


# ============= USED INGREDIENTS =============

def used_ingredients_create(request):
    if request.method == 'POST':
        form = UsedIngredientForm(request.POST)
        if form.is_valid():
            used = form.save(commit=False)
            used.RawMaterialName = used.IngredientRawMaterialBatchCode.RawMaterialName
            used.save()
            batches = IngredientsRawMaterials.objects.filter(RawMaterialName=used.RawMaterialName)
            new_bal = max(batches.first().QuantityLeft - used.QuantityUsed, 0) if batches.exists() else 0
            batches.update(QuantityLeft=new_bal)
        else:
            messages.error(request,
                "Used ingredient creation error: " +
                "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            )
    return redirect('ingredients_list')

def used_ingredients_update(request, pk):
    old = get_object_or_404(UsedIngredient, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = UsedIngredientForm(request.POST)
        if form.is_valid():
            old.change_status = "old_modified"
            old.save()
            new = form.save(commit=False)
            new.RawMaterialName = new.IngredientRawMaterialBatchCode.RawMaterialName
            new.change_status = "new_modified"
            new.save()
        else:
            messages.error(request,
                "Used ingredient update error: " +
                "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            )
    return redirect('ingredients_list')

def used_ingredients_delete(request, pk):
    obj = get_object_or_404(UsedIngredient, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        obj.change_status = "deleted"
        obj.save()
    return redirect('ingredients_list')


# =============== PACKAGING ===============

def packaging_list(request):
    mats = PackagingRawMaterials.objects.filter(change_status__in=["active", "new_modified"])
    used = UsedPackaging.objects.filter(change_status__in=["active", "new_modified"])
    return render(request, 'packaging.html', {
        'materials': mats,
        'used_packs': used,
        'create_form': PackagingRawMaterialsForm(),
        'used_pack_create_form': UsedPackagingForm(),
    })

def packaging_create(request):
    if request.method == 'POST':
        form = PackagingRawMaterialsForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            messages.error(request,
                "Packaging creation error: " +
                "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            )
    return redirect('packaging_list')

def packaging_update(request, pk):
    old = get_object_or_404(PackagingRawMaterials, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = PackagingRawMaterialsUpdateForm(request.POST)
        if form.is_valid():
            old.change_status = "old_modified"
            old.save()
            new = form.save(commit=False)
            new.change_status = "new_modified"
            new.save()
            batches = PackagingRawMaterials.objects.filter(RawMaterialName=new.RawMaterialName)
            bought = batches.aggregate(total=Sum('QuantityBought'))['total'] or 0
            used_sum = UsedPackaging.objects.filter(RawMaterialName=new.RawMaterialName).aggregate(total=Sum('QuantityUsed'))['total'] or 0
            batches.update(QuantityLeft=max(bought-used_sum,0))
        else:
            messages.error(request,
                "Packaging update error: " +
                "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            )
    return redirect('packaging_list')

def packaging_delete(request, pk):
    obj = get_object_or_404(PackagingRawMaterials, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        obj.change_status = "deleted"
        obj.save()
    return redirect('packaging_list')


# ============ USED PACKAGING ============

def used_packaging_create(request):
    if request.method == 'POST':
        form = UsedPackagingForm(request.POST)
        if form.is_valid():
            used = form.save(commit=False)
            used.RawMaterialName = used.PackagingRawMaterialBatchCode.RawMaterialName
            used.save()
            batches = PackagingRawMaterials.objects.filter(RawMaterialName=used.RawMaterialName)
            new_bal = max(batches.first().QuantityLeft - used.QuantityUsed, 0) if batches.exists() else 0
            batches.update(QuantityLeft=new_bal)
        else:
            messages.error(request,
                "Used packaging creation error: " +
                "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            )
    return redirect('packaging_list')

def used_packaging_update(request, pk):
    old = get_object_or_404(UsedPackaging, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        form = UsedPackagingForm(request.POST)
        if form.is_valid():
            old.change_status = "old_modified"
            old.save()
            new = form.save(commit=False)
            new.RawMaterialName = new.PackagingRawMaterialBatchCode.RawMaterialName
            new.change_status = "new_modified"
            new.save()
        else:
            messages.error(request,
                "Used packaging update error: " +
                "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            )
    return redirect('packaging_list')

def used_packaging_delete(request, pk):
    obj = get_object_or_404(UsedPackaging, pk=pk)
    if request.method == 'POST':
        if request.POST.get('password') != PASSWORD:
            return HttpResponse("Incorrect password", status=403)
        obj.change_status = "deleted"
        obj.save()
    return redirect('packaging_list')


# ============ REPORT SUMMARY ============

def report_summary(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    used_ing = []
    used_pack = []
    exp_ing = []

    if start_date and end_date:
        used_ing = UsedIngredient.objects.filter(
            DateUsed__range=[start_date, end_date],
            change_status__in=["active","new_modified"]
        ).values('RawMaterialName').annotate(total_used=Sum('QuantityUsed'))
        used_pack = UsedPackaging.objects.filter(
            DateUsed__range=[start_date, end_date],
            change_status__in=["active","new_modified"]
        ).values('RawMaterialName').annotate(total_used=Sum('QuantityUsed'))
        expired_qs = IngredientsRawMaterials.objects.filter(
            ExpirationDate__range=[start_date, end_date],
            change_status__in=["active","new_modified"]
        ).values('RawMaterialName').annotate(expired_qty=Sum('QuantityLeft'))
        remaining_qs = IngredientsRawMaterials.objects.exclude(
            ExpirationDate__range=[start_date, end_date]
        ).filter(change_status__in=["active","new_modified"]).values('RawMaterialName').annotate(remaining_qty=Sum('QuantityLeft'))
        rem_map = {r['RawMaterialName']: r['remaining_qty'] for r in remaining_qs}
        for e in expired_qs:
            exp_ing.append({
                'RawMaterialName': e['RawMaterialName'],
                'expired_qty': e['expired_qty'],
                'remaining_qty': rem_map.get(e['RawMaterialName'], 0)
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
        change_status__in=["active","new_modified"],
        Category__in=['Packaging','Both']
    ).values('SupplierCode','SupplierName')
    return JsonResponse({'suppliers': list(suppliers)}, safe=False)


def supplier_list_ingredients(request):
    suppliers = Supplier.objects.filter(
        change_status__in=["active","new_modified"],
        Category__in=['Ingredient','Both']
    ).values('SupplierCode','SupplierName')
    return JsonResponse({'suppliers': list(suppliers)}, safe=False)
