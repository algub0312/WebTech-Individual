from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Homepage
    path('', views.home, name='home'),

    # Pet pages
    path('pets/', views.PetListView.as_view(), name='pets'),
    path('pet/<int:pk>/<slug:slug>/', views.PetDetailView.as_view(), name='pet_detail'),

    # Information pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('success-stories/', views.success_stories, name='success_stories'),

    # Adoption
    path('adoption/process/', views.adoption_process, name='adoption_process'),
    path('adoption/apply/', views.adoption_application, name='adoption_application'),
    path('adoption/apply/<int:pet_id>/', views.adoption_application, name='adoption_application_pet'),

    # If you kept a custom site login, keep its name distinct:
    path('login/', auth_views.LoginView.as_view(
        template_name='shelter/login.html',
        redirect_authenticated_user=True
    ), name='site_login'),

    # Gate (what your "Apply" buttons should link to)
    path('adoption/start/', views.adoption_gate, name='adoption_gate'),
    path('adoption/start/<int:pet_id>/', views.adoption_gate, name='adoption_gate_pet'),

    # Account area
    path('register/', views.register, name='register'),
    path('logout/', views.custom_logout, name='logout'),
    path('account/', views.account, name='account'),
    path('account/applications/', views.user_applications, name='user_applications'),
    path('account/edit/', views.edit_profile, name='edit_profile'),

    # Admin Dashboard URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/applications/', views.admin_applications, name='admin_applications'),
    path('admin-dashboard/applications/<int:application_id>/', views.admin_application_detail, name='admin_application_detail'),
    path('admin-dashboard/applications/<int:application_id>/update-status/', views.admin_update_application_status, name='admin_update_application_status'),
    path('admin-dashboard/applications/<int:application_id>/update-notes/', views.admin_update_application_notes, name='admin_update_application_notes'),
    path('admin-dashboard/pets/', views.admin_pets, name='admin_pets'),
    path('admin-dashboard/contacts/', views.admin_contacts, name='admin_contacts'),
    path('admin-dashboard/contacts/<int:contact_id>/', views.admin_contact_detail, name='admin_contact_detail'),
    path('admin-dashboard/contacts/<int:contact_id>/update-status/', views.admin_update_contact_status, name='admin_update_contact_status'),
    path('admin-dashboard/api/stats/', views.admin_stats_api, name='admin_stats_api'),
]