from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from datetime import date

from .models import User, MedicineDonation, MedicineRequest


def get_user_dashboard_redirect(user):
    """Direct each user role strictly to their respective authorized dashboard."""
    if not user.is_authenticated:
        return redirect('login')
    if user.is_superuser:
        return redirect('admin_dashboard')
    elif user.role == 'NGO':
        if getattr(user, 'is_verified_ngo', False):
            return redirect('ngo_dashboard')
        return redirect('ngo_pending_approval')
    else:
        return redirect('dashboard')


def home(request):
    total_donated = MedicineDonation.objects.count()
    verified_ngos = User.objects.filter(role='NGO').count()
    cities_covered = MedicineDonation.objects.values('city').distinct().count()

    context = {
        'total_donated': max(total_donated, 1),
        'verified_ngos': max(verified_ngos, 1),
        'cities_covered': max(cities_covered, 1),
    }
    return render(request, 'home.html', context)


@never_cache
def register_view(request):
    if request.user.is_authenticated:
        return get_user_dashboard_redirect(request.user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'DONOR')
        phone = request.POST.get('phone', '').strip()
        ngo_name = request.POST.get('ngo_name', '').strip()
        address = request.POST.get('address', '').strip()
        ngo_reg_number = request.POST.get('ngo_reg_number', '').strip()

        context = {
            'username': username,
            'email': email,
            'phone': phone,
            'role': role,
            'ngo_name': ngo_name,
            'address': address,
            'ngo_reg_number': ngo_reg_number,
        }

        if not username or not password:
            context['error'] = 'Username and password are required.'
            return render(request, 'register.html', context)

        # Prevent duplicate username (case-insensitive check)
        if User.objects.filter(username__iexact=username).exists():
            context['error'] = f"Username '{username}' is already taken. Please choose another username."
            return render(request, 'register.html', context)

        # If email is provided, check duplicate email
        if email and User.objects.filter(email__iexact=email).exists():
            context['error'] = f"An account with email '{email}' already exists. Please login instead or use a different email."
            return render(request, 'register.html', context)

        if role == 'NGO' and not ngo_name:
            context['error'] = 'NGO / Hospital Legal Name is required for NGO accounts.'
            return render(request, 'register.html', context)

        # Institutional Gate: NGOs start as unverified until Admin reviews their credentials
        is_verified_ngo = False if role == 'NGO' else True
        ngo_status = 'PENDING' if role == 'NGO' else 'APPROVED'

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                role=role,
                phone=phone,
                address=address,
                ngo_name=ngo_name,
                ngo_reg_number=ngo_reg_number,
                is_verified_ngo=is_verified_ngo,
                ngo_verification_status=ngo_status
            )
        except Exception as e:
            context['error'] = f"Error creating account: {str(e)}"
            return render(request, 'register.html', context)

        if role == 'NGO':
            messages.info(
                request,
                "NGO registration submitted successfully! In compliance with healthcare standards, your institutional credentials are under administrative review."
            )
        else:
            messages.success(request, f"Welcome to MediShare, {username}! Your account has been created. Please log in.")

        return redirect('login')

    return render(request, 'register.html')


@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return get_user_dashboard_redirect(request.user)

    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not login_input or not password:
            return render(
                request,
                'login.html',
                {'error': 'Please enter both username/email and password.', 'login_input': login_input}
            )

        # Step 1: Check if input matches an existing user's email
        user = None
        user_by_email = User.objects.filter(email__iexact=login_input).first()
        if user_by_email:
            user = authenticate(request, username=user_by_email.username, password=password)

        # Step 2: Try direct authentication by username
        if not user:
            user = authenticate(request, username=login_input, password=password)

        # Step 3: Try case-insensitive username match if direct auth failed
        if not user:
            user_by_username = User.objects.filter(username__iexact=login_input).first()
            if user_by_username:
                user = authenticate(request, username=user_by_username.username, password=password)

        if user:
            login(request, user)
            return get_user_dashboard_redirect(user)

        return render(
            request,
            'login.html',
            {'error': 'Invalid username/email or password. Please check your credentials.', 'login_input': login_input}
        )

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
@never_cache
def dashboard(request):
    # Restrict: Admins and NGOs must only access their respective dashboards
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    if request.user.role != 'DONOR':
        return redirect('ngo_dashboard')

    donations = MedicineDonation.objects.filter(
        donor=request.user
    )

    total = donations.count()

    pending = donations.filter(
        status='PENDING'
    ).count()

    approved = donations.filter(
        status='APPROVED'
    ).count()

    distributed = donations.filter(
        status='DISTRIBUTED'
    ).count()

    return render(request, 'dashboard.html', {
        'donations': donations,
        'total': total,
        'pending': pending,
        'approved': approved,
        'distributed': distributed,
    })


@login_required
@never_cache
def add_donation(request):
    # Restrict: Only Donors can donate medicines
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    if request.user.role != 'DONOR':
        return redirect('ngo_dashboard')

    if request.method == 'POST':
        packaging_condition = request.POST.get('packaging_condition', 'SEALED_BLISTER')
        is_opened = request.POST.get('is_opened') == 'on' or packaging_condition == 'OPENED_DAMAGED'

        # Clinical Safety Rule: Opened/unsealed medicines are strictly rejected
        if is_opened or packaging_condition == 'OPENED_DAMAGED':
            messages.error(
                request,
                "Clinical Safety Restriction: Opened, unsealed, or damaged medicines cannot be accepted for redistribution in compliance with healthcare regulations."
            )
            return render(request, 'add_donation.html')

        batch_number = request.POST.get('batch_number', '').strip()
        manufacturer = request.POST.get('manufacturer', '').strip()
        storage_conditions = request.POST.get('storage_conditions', 'ROOM_TEMPERATURE')
        prescription_required = request.POST.get('prescription_required') == 'on'
        authenticity_declared = request.POST.get('authenticity_declared') == 'on'

        image = request.FILES.get('image')

        MedicineDonation.objects.create(
            donor=request.user,
            medicine_name=request.POST['medicine_name'],
            quantity=request.POST['quantity'],
            expiry_date=request.POST['expiry_date'],
            city=request.POST['city'],
            batch_number=batch_number,
            manufacturer=manufacturer,
            packaging_condition=packaging_condition,
            is_opened=is_opened,
            storage_conditions=storage_conditions,
            prescription_required=prescription_required,
            authenticity_declared=authenticity_declared,
            status='PENDING',
            image=image
        )

        messages.success(request, "Medicine submitted successfully and queued for clinical safety verification.")
        return redirect('dashboard')

    return render(request, 'add_donation.html')


@login_required
@never_cache
def ngo_pending_approval(request):
    # Restrict: Only unverified NGOs view the pending review page
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    if request.user.role != 'NGO':
        return redirect('dashboard')
    if getattr(request.user, 'is_verified_ngo', False):
        return redirect('ngo_dashboard')
    return render(request, 'ngo_pending_approval.html')


@login_required
@never_cache
def ngo_dashboard(request):
    # Restrict: Only NGOs can access NGO dashboard
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    if request.user.role != 'NGO':
        return redirect('dashboard')
    if not getattr(request.user, 'is_verified_ngo', False):
        messages.warning(request, "Access restricted: Your NGO verification is currently under review.")
        return redirect('ngo_pending_approval')

    donations = MedicineDonation.objects.filter(
        status='APPROVED'
    )

    for d in donations:

        if d.expiry_date:
            d.days_left = (
                d.expiry_date - date.today()
            ).days
        else:
            d.days_left = 0

        d.user_request = MedicineRequest.objects.filter(
            ngo=request.user,
            donation=d
        ).first()

    expiring_count = sum(
        1 for d in donations
        if 0 < d.days_left <= 7
    )

    city_count = len(
        set(d.city for d in donations)
    )

    return render(request, 'ngo_dashboard.html', {
        'donations': donations,
        'expiring_count': expiring_count,
        'city_count': city_count
    })


@login_required
@never_cache
def request_medicine(request, id):
    # Restrict: Only verified NGOs can request medicines
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    if request.user.role != 'NGO':
        return redirect('dashboard')
    if not getattr(request.user, 'is_verified_ngo', False):
        messages.error(request, "Access restricted: Only verified NGOs can request medicines.")
        return redirect('ngo_pending_approval')

    donation = get_object_or_404(
        MedicineDonation,
        id=id
    )

    if donation.expiry_date < date.today():

        messages.error(
            request,
            "Expired medicine."
        )

        return redirect('ngo_dashboard')

    if request.method == 'POST':

        try:
            req_qty = int(
                request.POST.get('quantity')
            )

        except (TypeError, ValueError):

            messages.error(
                request,
                "Enter a valid quantity."
            )

            return redirect('ngo_dashboard')

        if req_qty <= 0:

            messages.error(
                request,
                "Quantity must be greater than 0."
            )

            return redirect('ngo_dashboard')

        if req_qty > donation.quantity:

            messages.error(
                request,
                f"Only {donation.quantity} medicines are available."
            )

            return redirect('ngo_dashboard')

        MedicineRequest.objects.create(
            ngo=request.user,
            donation=donation,
            quantity=req_qty,
            reason=request.POST.get('reason', ''),
            status='REQUESTED'
        )

        donation.quantity -= req_qty
        donation.save()

        messages.success(
            request,
            "Medicine requested successfully."
        )

        return redirect('ngo_dashboard')

    return render(
        request,
        'request_form.html',
        {'donation': donation}
    )


@login_required
@never_cache
def admin_dashboard(request):
    # Restrict: Only Superusers/Admins can access admin dashboard
    if not request.user.is_superuser:
        if request.user.role == 'NGO':
            return redirect('ngo_dashboard')
        return redirect('dashboard')

    donations = MedicineDonation.objects.all()
    requests = MedicineRequest.objects.all()

    # 🏛️ Institutional NGO Verification Queries
    pending_ngos = User.objects.filter(role='NGO', is_verified_ngo=False, ngo_verification_status='PENDING')
    verified_ngos = User.objects.filter(role='NGO', is_verified_ngo=True)

    return render(request, 'admin_dashboard.html', {
        'donations': donations,
        'requests': requests,
        'pending_requests': requests.filter(
            status='REQUESTED'
        ).count(),
        'approved_requests': requests.filter(
            status='APPROVED'
        ).count(),
        'pending_ngos': pending_ngos,
        'pending_ngos_count': pending_ngos.count(),
        'verified_ngos': verified_ngos,
    })


@login_required
def approve_ngo(request, user_id):
    if not request.user.is_superuser:
        return get_user_dashboard_redirect(request.user)

    ngo_user = get_object_or_404(User, id=user_id, role='NGO')
    ngo_user.is_verified_ngo = True
    ngo_user.ngo_verification_status = 'APPROVED'
    ngo_user.save()
    messages.success(
        request,
        f"Institution '{ngo_user.ngo_name or ngo_user.username}' successfully verified! Marketplace medicine requests are now unlocked."
    )
    return redirect('admin_dashboard')


@login_required
def reject_ngo(request, user_id):
    if not request.user.is_superuser:
        return get_user_dashboard_redirect(request.user)

    ngo_user = get_object_or_404(User, id=user_id, role='NGO')
    ngo_user.is_verified_ngo = False
    ngo_user.ngo_verification_status = 'REJECTED'
    ngo_user.save()
    messages.warning(
        request,
        f"NGO registration for '{ngo_user.ngo_name or ngo_user.username}' was rejected."
    )
    return redirect('admin_dashboard')


@login_required
def approve_request(request, id):
    if not request.user.is_superuser:
        return get_user_dashboard_redirect(request.user)

    req = get_object_or_404(
        MedicineRequest,
        id=id
    )

    if req.donation.expiry_date < date.today():
        req.status = 'REJECTED'
    else:
        req.status = 'APPROVED'

    req.save()

    return redirect('admin_dashboard')


@login_required
def reject_request(request, id):
    if not request.user.is_superuser:
        return get_user_dashboard_redirect(request.user)

    req = get_object_or_404(
        MedicineRequest,
        id=id
    )

    req.status = 'REJECTED'
    req.save()

    return redirect('admin_dashboard')


@login_required
def track_request(request, id):
    req = get_object_or_404(
        MedicineRequest,
        id=id
    )

    # Restrict: Only the requesting NGO, the donor, or admin can track this request
    if not request.user.is_superuser and req.ngo != request.user and req.donation.donor != request.user:
        return get_user_dashboard_redirect(request.user)

    return render(
        request,
        'track.html',
        {'req': req}
    )


@login_required
def mark_packed(request, id):
    if not request.user.is_superuser:
        return get_user_dashboard_redirect(request.user)

    req = get_object_or_404(
        MedicineRequest,
        id=id
    )

    req.status = 'PACKED'
    req.save()

    return redirect('admin_dashboard')


@login_required
def mark_out_for_delivery(request, id):
    if not request.user.is_superuser:
        return get_user_dashboard_redirect(request.user)

    req = get_object_or_404(
        MedicineRequest,
        id=id
    )

    req.status = 'OUT_FOR_DELIVERY'
    req.save()

    return redirect('admin_dashboard')


@login_required
def mark_delivered(request, id):
    if not request.user.is_superuser:
        return get_user_dashboard_redirect(request.user)

    req = get_object_or_404(
        MedicineRequest,
        id=id
    )

    req.status = 'DELIVERED'
    req.save()

    return redirect('admin_dashboard')


@login_required
def approve_donation(request, id):
    if not request.user.is_superuser:
        return get_user_dashboard_redirect(request.user)

    donation = get_object_or_404(
        MedicineDonation,
        id=id
    )

    donation.status = 'APPROVED'
    donation.save()

    return redirect('admin_dashboard')


@login_required
def reject_donation(request, id):
    if not request.user.is_superuser:
        return get_user_dashboard_redirect(request.user)

    donation = get_object_or_404(
        MedicineDonation,
        id=id
    )

    donation.status = 'REJECTED'
    donation.save()

    return redirect('admin_dashboard')


@login_required
def donation_receipt(request, id):
    donation = get_object_or_404(MedicineDonation, id=id)

    # Permission check: Only the donor of this donation or an admin can access receipt
    if donation.donor != request.user and not request.user.is_superuser:
        return get_user_dashboard_redirect(request.user)

    ngo_request = MedicineRequest.objects.filter(donation=donation).first()

    return render(request, 'donation_receipt.html', {
        'donation': donation,
        'ngo_request': ngo_request,
    })
