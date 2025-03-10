from django.shortcuts import render, redirect,HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages 
from django.shortcuts import render, redirect
from .forms import ProfileRegistrationForm
from .models import *
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random
from django.views import View
from django.contrib.auth.forms import PasswordResetForm
from django.http import HttpRequest
from django.conf import settings
from django.core.mail import send_mail
import razorpay
import pkg_resources
from django.urls import reverse
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.db.models import Count
from datetime import datetime, date
# from django.contrib.auth.views import PasswordResetView
# from django.urls import reverse_lazy 

def home(request):
    return render(request, 'index.html')



def register(request):
    print("Request method:", request.method)  # Debug print
    if request.method == 'POST':
        # Retrieve form data directly
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password1 = request.POST.get('password1')
        
        # Directly create and save the new user (bypassing validation)
        user = Profile.objects.create_user(username=username, email=email, password=password1, phone_number=phone_number)
        
        # Notify the user of a successful registration
        messages.success(request, 'Registration successful. You can now log in.')
        return redirect('login')


    return render(request, 'register.html')

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome, {username}! You have successfully logged in.')
                return redirect('profile')  # Replace 'profile' with the name of your profile page view
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


@login_required
def profile_view(request:HttpRequest):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile.html')
    else:
        form = ProfileForm(instance=request.user)
    
    return render(request, 'profile.html', {'user': request.user})


@login_required
def profile_edit_view(request):
    user = request.user

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Update user attributes based on received data
            for field in ['username', 'email', 'phone_number', 'address', 'child_name', 
                          'whatsapp_number', 'gender', 'date_of_birth', 'disability', 
                          'disability_description', 'upi_number']:  # Include upi_number
                if field in data:
                    if field == 'disability':
                        user.disability = data['disability'] == 'yes'
                    else:
                        setattr(user, field, data[field])

            # Save user instance
            user.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({
        'username': user.username,
        'email': user.email,
        'phone_number': user.phone_number,
        'address': user.address,
        'child_name': user.child_name,
        'whatsapp_number': user.whatsapp_number,
        'gender': user.gender,
        'date_of_birth': user.date_of_birth,
        'disability': user.disability,
        'disability_description': user.disability_description,
        'upi_number': user.upi_number, 
    })
    
def bookup(request):
        return render(request, 'bookup.html')

def check_token_limit(request):
    date_str = request.GET.get('date')
    if date_str:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Check if the selected date is in the past
        if date_obj < date.today():
            return JsonResponse({'error': 'You cannot select a past date for booking.'}, status=400)
        
        # Check if the selected date is on a weekend (Saturday or Sunday)
        if date_obj.weekday() >= 5:
            return JsonResponse({'error': 'Bookings cannot be made on weekends (Saturday and Sunday).'}, status=400)
        
        # Check if the selected date is a leave day
        leave_objects = Leave.objects.filter(date=date_obj)
        if leave_objects.exists():
            # Retrieve the first leave reason if multiple entries are found
            leave_reason = leave_objects.first().reason
            return JsonResponse({'error': f'Bookings cannot be made on this date. '}, status=400)
        
        # Check token limit for the selected date
        token_count = Booking.objects.filter(appointment_date=date_obj).count()
        if token_count >= 8:
            return JsonResponse({'token_count': token_count, 'error': 'All tokens for the selected day are booked. Please choose another day.'})
        
        return JsonResponse({'token_count': token_count})
    
    return JsonResponse({'error': 'Invalid date'}, status=400)

class BookingCreateView(View):
    def get(self, request):
        return render(request, 'bookup.html', {'razorpay_key_id': settings.RAZORPAY_KEY_ID})

    def post(self, request):
        vaccinations = request.POST.get('vaccination')
        appointment_date = request.POST.get('date')

        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to book a vaccination.")
            return redirect('login')

        # Check if the required fields are filled
        if not vaccinations or not appointment_date:
            messages.error(request, "Please fill in all required fields.")
            return redirect('book_vaccination')

        # Get the user's profile
        profile = request.user

        # Check daily token count for the selected date
        appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        daily_bookings = Booking.objects.filter(appointment_date=appointment_date_obj)

        if daily_bookings.count() >= 30:
            messages.error(request, "All tokens for the selected day are booked. Please choose another day.")
            return redirect('book_vaccination')

        # Assign the next available token number
        token_number = daily_bookings.count() + 1

        # Create a new booking entry
        booking = Booking.objects.create(
            patient=profile,
            vaccinations=vaccinations,
            appointment_date=appointment_date,
            token_number=token_number,
            appointment_fee=700.00  # Adjust as needed
        )

        # Create a Razorpay client instance
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Create a Razorpay order
        payment = client.order.create({
            'amount': 70000,  # Amount in paise
            'currency': 'INR',
            'payment_capture': '1'  # Auto capture
        })

        booking.razorpay_order_id = payment['id']
        booking.save()

        # Redirect to a success page or send a success message
        messages.success(request, "Your booking has been created successfully!")
        return redirect('success')


def success(request):
    booking = Booking.objects.filter(patient=request.user).latest('id')
    return render(request, 'success.html', {'booking': booking})

def about(request):
     return render(request, 'about.html')
 
@login_required
def history(request):
    bookings = Booking.objects.filter(patient=request.user)
    return render(request, 'history.html', {'bookings': bookings})
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        try:
            booking = Booking.objects.get(id=booking_id, patient=request.user)
            booking.status = 'Cancelled'  # Update the status
            booking.save()
            messages.success(request, 'Booking cancelled successfully.')
        except Booking.DoesNotExist:
            messages.error(request, 'Booking not found or you do not have permission to cancel it.')
    return redirect('history')  

#admin side
def admin_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        print(f"Username entered: {username}, Password entered: {password}")

        user = authenticate(request, username=username, password=password)
        print(f"Authenticated user: {user}")

        if user is not None and user.is_staff:
            login(request, user)
            return redirect(reverse('dashboard'))  # Update this with your actual dashboard URL name
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'adminside/admin_login.html')
   
def dashboard(request):
    # Pie chart data: Count of bookings per vaccination type
    vaccine_data = Booking.objects.values('vaccinations').annotate(count=Count('id')).order_by('-count')

    # Bar chart data: Count of registered patients this month
    current_month = datetime.now().month
    registered_this_month = Profile.objects.filter(date_joined__month=current_month).count()

    # Prepare data for charts
    vaccine_labels = [entry['vaccinations'] for entry in vaccine_data]
    vaccine_counts = [entry['count'] for entry in vaccine_data]

    return render(request,'adminside/dashboard.html', {
        'vaccine_labels': vaccine_labels,
        'vaccine_counts': vaccine_counts,
        'registered_this_month': registered_this_month,
    }) 
def patients(request):
     patients_list = Profile.objects.all()
     return render(request, 'adminside/patients.html', {'patients': patients_list})
 
@login_required
def toggle_block_patient(request, patient_id):
    patient = get_object_or_404(Profile, id=patient_id)

    # Toggle the is_active field
    patient.is_active = not patient.is_active
    patient.save()

    # Redirect back to the patients list
    return redirect('patients') 
def  patient_details(request, patient_id):
    patient = get_object_or_404(Profile, id=patient_id)
    return render(request, 'adminside/patientdetails.html', {'patient': patient}) 

def bookings(request):
    bookings_list = Booking.objects.all().order_by('appointment_date')
    paginator = Paginator(bookings_list, 5)

    # Get the current page number from the request (default to 1 if not specified)
    page_number = request.GET.get('page', 1)

    # Get the relevant page of bookings
    page_obj = paginator.get_page(page_number)

    return render(request, 'adminside/bookings.html', {'page_obj': page_obj})
def filter_bookings(request):
    status = request.GET.get('status', '')
    bookings = Booking.objects.all()

    if status:
        bookings = bookings.filter(status=status)

    paginator = Paginator(bookings, 10)  # Show 10 bookings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'adminside/bookings.html', {'page_obj': page_obj, 'status': status})
@require_POST
def update_booking_status(request):
    booking_id = request.POST.get('booking_id')
    new_status = request.POST.get('new_status')
    booking = get_object_or_404(Booking, id=booking_id)

    # Update the booking status based on the selected option
    if new_status == 'Refunded':
        booking.status = 'Refunded'
    elif new_status == 'Completed':
        booking.status = 'Completed'

    booking.save()

    # Redirect back to the bookings list or desired page
    return redirect('bookings') 
def admin_logout(request):
    if request.user.is_authenticated and request.user.is_staff:  # Ensure only admins can access this
        logout(request)
        messages.success(request, "You have successfully logged out.")
    return redirect(reverse('admin_login'))

def notification(request):
    # Filter bookings with the status 'Cancelled' or 'Refunded'
    cancelled_and_refunded_bookings = Booking.objects.filter(
        Q(status='Cancelled') | Q(status='Refunded')
    ).order_by('appointment_date')  # Optional: Order by date

    # Create a paginator object
    paginator = Paginator(cancelled_and_refunded_bookings, 6)  # Show 6 bookings per page

    # Get the page number from the query parameter
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the template with the context
    return render(request, 'adminside/notification.html', {'page_obj': page_obj})

@require_POST
def refund_booking(request):
    booking_id = request.POST.get('booking_id')
    
    try:
        booking = Booking.objects.get(id=booking_id)
        booking.status = 'Refunded'
        booking.save()

        # Send email notification to the user
        subject = 'Booking Refunded'
        message = f'Dear {booking.patient.child_name},\n\nYour booking for {booking.vaccinations} on {booking.appointment_date} has been cancelled. The booking has been refunded successfully .\n\nThank you!'
        recipient_email = booking.patient.email  # Adjust this field based on your model

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [recipient_email],
            fail_silently=False,
        )

        # messages.success(request, 'The booking has been refunded successfully. An email notification has been sent to the user.')

    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found.')
    
    return redirect('notification')

@require_POST
def refund_booking1(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)

        # Check if booking is refundable
        if booking.status == 'Completed' or booking.status == 'Refunded':
            return JsonResponse({'status': 'error', 'message': 'Booking cannot be refunded.'})

        # Update the booking status to "Refunded"
        booking.status = 'Refunded'
        booking.save()

        # Send email notification to the user
        subject = 'Booking Refunded'
        message = f'Dear {booking.patient.child_name},\n\nYour booking for {booking.vaccinations} on {booking.appointment_date} has been cancelled. The booking has been refunded successfully.\n\nThank you!'
        recipient_email = booking.patient.email  # Adjust this field based on your model

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [recipient_email],
            fail_silently=False,
        )

        # Return a success response
        return JsonResponse({'status': 'success', 'message': 'Booking refunded successfully.'})

    except Booking.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Booking not found.'})
def process_refund(request, booking_id):
    if request.method == 'POST':
        try:
            # Get the booking object using booking_id
            booking = Booking.objects.get(id=booking_id)

            # Check if the booking status allows a refund
            if booking.status != 'Refunded' and booking.status != 'Completed':
                # Refund logic: update the status and other relevant fields
                booking.status = 'Refunded'
                booking.save()

                return JsonResponse({'status': 'success'}, status=200)

            return JsonResponse({'status': 'error', 'message': 'Refund not applicable.'}, status=400)

        except Booking.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Booking not found.'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405) 
        
         
def leave(request):
    # Ensure the leaves are being passed correctly to the template
    leaves = Leave.objects.all().order_by('date')  # Ordering might help if you want to display in a specific order
    return render(request, 'adminside/leave.html', {'leaves': leaves})


def leave_details(request, leave_id):
    try:
        # Get the leave object using the leave_id
        leave = Leave.objects.get(id=leave_id)
        
        # Query all bookings for that leave date
        bookings = Booking.objects.filter(appointment_date=leave.date)

        # Serialize the bookings to JSON (you could use custom fields if needed)
        bookings_data = list(bookings.values('patient__child_name', 'vaccinations', 'appointment_date', 'status'))

        # Return the bookings data as a JSON response
        return JsonResponse({'bookings': bookings_data})
    except Leave.DoesNotExist:
        return JsonResponse({'error': 'Leave not found'}, status=404)

def add_leave(request):
    if request.method == "POST":
        # Get data from the form
        leave_date = request.POST.get('leave_date')
        leave_reason = request.POST.get('leave_reason')

        # Create and save the new leave instance
        leave = Leave(date=leave_date, reason=leave_reason)
        leave.save()

        # Add a success message
        messages.success(request, "Leave has been added successfully.")
        
        # Redirect back to the leave page to refresh the list
        return redirect('leave')

    # If the method is not POST, redirect to the leave page
    return redirect('leave')