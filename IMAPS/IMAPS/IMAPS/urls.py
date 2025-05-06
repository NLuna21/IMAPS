"""
URL configuration for IMAPS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# IMAPS/urls.py
from django.contrib import admin
from django.urls import path
from IMAPS_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.packaging_list, name='home'),

    # Suppliers
    path('suppliers/', views.suppliers_list, name='suppliers_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/update/<str:pk>/', views.supplier_update, name='supplier_update'),
    path('suppliers/delete/<str:pk>/', views.supplier_delete, name='supplier_delete'),

    # Ingredients
    path('ingredients/', views.ingredients_list, name='ingredients_list'),
    path('ingredients/create/', views.ingredients_create, name='ingredients_create'),
    path('ingredients/update/<str:pk>/', views.ingredients_update, name='ingredients_update'),
    path('ingredients/delete/<str:pk>/', views.ingredients_delete, name='ingredients_delete'),

    # Packaging
    path('packaging/', views.packaging_list, name='packaging_list'),
    path('packaging/create/', views.packaging_create, name='packaging_create'),
    path('packaging/update/<str:pk>/', views.packaging_update, name='packaging_update'),
    path('packaging/delete/<str:pk>/', views.packaging_delete, name='packaging_delete'),


    # Used Ingredients
    path('used-ingredients/', views.ingredients_list, name='used_ingredients_list'),
    path('used-ingredients/create/', views.used_ingredients_create, name='used_ingredients_create'),
    path('used-ingredients/update/<str:pk>/', views.used_ingredients_update, name='used_ingredients_update'),
    path('used-ingredients/delete/<str:pk>/', views.used_ingredients_delete, name='used_ingredients_delete'),

    # Used Packaging
    path('used-packaging/', views.packaging_list, name='used_packaging_list'),
    path('used-packaging/create/', views.used_packaging_create, name='used_packaging_create'),
    path('used-packaging/update/<str:pk>/', views.used_packaging_update, name='used_packaging_update'),
    path('used-packaging/delete/<str:pk>/', views.used_packaging_delete, name='used_packaging_delete'),

    # Report Summary
    path('report-summary/', views.report_summary, name='report_summary'),

    
    path('api/suppliers/ingredients', views.supplier_list_ingredients, name='supplier_list_ingredients'),
    path('api/suppliers/packaging', views.supplier_list_packaging, name='supplier_list_packaging'),

]
