from django.urls import path
from . import views

urlpatterns = [
    # medicine seeker
    path('search/', views.medicine_search, name='medicine_search'),
    # pharmacist
    path('my-pharmacy/', views.my_pharmacy, name='my_pharmacy'),
    path('my-medicines/', views.pharmacist_medicines, name='pharmacist_medicines'),
    path('my-medicines/add/', views.medicine_create, name='medicine_create'),
    path('my-medicines/<int:pk>/edit/', views.medicine_edit, name='medicine_edit'),
    path('my-medicines/<int:pk>/status/', views.medicine_status, name='medicine_status'),
    path('my-medicines/<int:pk>/delete/', views.medicine_delete, name='medicine_delete'),
    # admin
    path('manage/pharmacies/', views.admin_pharmacies, name='admin_pharmacies'),
    path('manage/pharmacies/<int:pk>/toggle/', views.pharmacy_toggle, name='pharmacy_toggle'),
    path('manage/medicines/', views.admin_medicines, name='admin_medicines'),
    path('manage/medicines/<int:pk>/edit/', views.admin_medicine_edit, name='admin_medicine_edit'),
    path('manage/medicines/<int:pk>/delete/', views.admin_medicine_delete, name='admin_medicine_delete'),
]
