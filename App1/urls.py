from django.urls import path
# from .views import forgetpassword
from django.contrib.auth.views import LogoutView
from . import views 
from .views import *

urlpatterns = [
    
    # USER
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('bookup/', views.bookup, name='bookup'),
    path('check_token_limit/', views.check_token_limit, name='check_token_limit'),
    path('book_vaccination/', BookingCreateView.as_view(), name='book_vaccination'),
    path('success', views.success, name='success'),
    path('about/', views.about, name='about'),
    path('history', views.history, name='history'),
    path('cancel_booking/<int:booking_id>/', cancel_booking, name='cancel_booking'),
    path('logout/', LogoutView.as_view(), name='logout'),
    # path('forgetpassword', views.forgetpassword, name='forgetpassword'),
    
    
    
    
    # ADMIN
    path('admin_login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('patients/', views.patients, name='patients'),
    path('patients/toggle_block/<int:patient_id>/', toggle_block_patient, name='toggle_block_patient'),
    path('patients/<int:patient_id>/', views.patient_details, name='patient_details'),
    path('bookings/', views.bookings, name='bookings'), 
    path('update_booking_status/', update_booking_status, name='update_booking_status'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),
    path('notification/', views.notification, name='notification'),
    path('refund/', refund_booking, name='refund_booking'),
]
 
 
    

