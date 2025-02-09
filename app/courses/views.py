from django.shortcuts import render

from orders.models import Order, OrderItem
from subscriptions.models import Subscription
from carts.models import CartCourse, CartLevel, CartTrack
from loves.models import LoveCourse, LoveTrack
from .models import CourseTranslation, Level, LevelContentTranslation, LevelTranslation, Session,Track, Course, TrackTranslation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, get_object_or_404, redirect
from decimal import Decimal


def levels(request):
    language = request.GET.get('lang', 'en')  # Default to 'en' if no language is specified

    # Get all levels with their related data
    levels = Level.objects.prefetch_related(
        'courses',
        'tracks',
        'tracks__courses',
        'discountlevel',
        'tracks__discounttrack',
        'courses__coursesessions'
    ).all()

    # Get cart data for the logged-in user
    cart_level_ids = CartLevel.objects.filter(student=request.user).values_list('level_id', flat=True) if request.user.is_authenticated else []
    cart_track_ids = CartTrack.objects.filter(student=request.user).values_list('track_id', flat=True) if request.user.is_authenticated else []
    cart_course_ids = CartCourse.objects.filter(student=request.user).values_list('course_id', flat=True) if request.user.is_authenticated else []

    # Get loved courses and tracks for the logged-in user
    loved_course_ids = LoveCourse.objects.filter(student=request.user).values_list('course_id', flat=True) if request.user.is_authenticated else []
    loved_track_ids = LoveTrack.objects.filter(student=request.user).values_list('track_id', flat=True) if request.user.is_authenticated else []

    # Process each level's data
    levels_data = []
    for level in levels:
        # Translate level name and description
        level_translation = LevelTranslation.objects.filter(level=level, language=language).first()
        level_name = level_translation.translated_name if level_translation else level.name
        level_description = level_translation.translated_description if level_translation else level.description

        # Translate level content
        level_content_data = []
        for content in level.contents.all():
            content_translation = LevelContentTranslation.objects.filter(level_content=content, language=language).first()
            content_name = content_translation.translated_name if content_translation else content.name
            level_content_data.append({"name": content_name})

        # Translate individual courses
        individual_courses = []
        for course in level.courses.filter(track__isnull=True):
            course_translation = CourseTranslation.objects.filter(course=course, language=language).first()
            course_name = course_translation.translated_name if course_translation else course.name
            course_description = course_translation.translated_description if course_translation else course.description
            individual_courses.append({
                'id': course.id,
                'name': course_name,
                'description': course_description,
                'price_without_any_discount': course.price_without_any_discount,
                'discount_percent': course.discount_percent,
                'has_discount': course.has_discount,
                'final_price_after_discound': course.final_price_after_discound,
                'image': course.image,
                'preview_video': course.preview_video,
            })

        # Translate tracks and their courses
        tracks = []
        for track in level.tracks.all():
            track_translation = TrackTranslation.objects.filter(track=track, language=language).first()
            track_name = track_translation.translated_name if track_translation else track.name
            track_description = track_translation.translated_description if track_translation else track.description

            # Translate courses within the track
            courses = []
            for course in track.courses.all():
                course_translation = CourseTranslation.objects.filter(course=course, language=language).first()
                course_name = course_translation.translated_name if course_translation else course.name
                course_description = course_translation.translated_description if course_translation else course.description
                courses.append({
                    'id': course.id,
                    'name': course_name,
                    'description': course_description,
                    'price_without_any_discount': course.price_without_any_discount,
                    'discount_percent': course.discount_percent,
                    'has_discount': course.has_discount,
                    'final_price_after_discound': course.final_price_after_discound,
                    'image': course.image,
                    'preview_video': course.preview_video,
                })

            tracks.append({
                'id': track.id,
                'name': track_name,
                'description': track_description,
                'courses': courses,
                'price_without_any_discount': track.price_without_any_discount,
                'discount_percent': track.discount_percent,
                'has_discount': track.has_discount,
                'final_price_after_discound': track.final_price_after_discound,
                'image': track.image,
                'preview_video': track.preview_video,
            })

        level_data = {
            'name': level_name,
            'id': level.id,
            'description': level_description,
            'image': level.image,
            'preview_video': level.preview_video,
            'year_limit': level.year_limit,
            'enable_pricing': level.enable_pricing,
            'price_without_any_discount': level.price_without_any_discount,
            'discount_percent': level.discount_percent,
            'has_discount': level.has_discount,
            'final_price_after_discound': level.final_price_after_discound,
            'individual_courses': individual_courses,
            'tracks': tracks,
            'levelcontent': level_content_data,
        }
        levels_data.append(level_data)

    context = {
        'levels': levels_data,
        'cart_level_ids': list(cart_level_ids),
        'cart_track_ids': list(cart_track_ids),
        'cart_course_ids': list(cart_course_ids),
        'loved_course_ids': list(loved_course_ids),
        'loved_track_ids': list(loved_track_ids),
    }
    return render(request, 'courses/levels.html', context)





@login_required
def course_detail(request, course_id):
    # Get the course
    course = get_object_or_404(Course, id=course_id)
    
    # Check if the user is subscribed to this course
    try:
        subscription = Subscription.objects.get(student=request.user, course=course)
    except Subscription.DoesNotExist:
        # Redirect or show an error that user is not subscribed
        return redirect('courses:levels')
    
    # Get all sessions for this subscription
    sessions = Session.objects.filter(course=subscription)
    
    # Check if there's a discount
    discount = None
    if hasattr(course, 'discountcourse_set') and course.discountcourse_set.exists():
        discount = course.discountcourse_set.first()
    
    context = {
        'course': course,
        'subscription': subscription,
        'sessions': sessions,
        'discount': discount,
        'total_sessions': sessions.count(),
        'completed_sessions': sessions.filter(is_completed=True).count(),
    }
    
    # Handle session completion
    if request.method == 'POST':
        action = request.POST.get('action')
        session_id = request.POST.get('session_id')
        
        if action == 'mark_completed':
            session = get_object_or_404(Session, id=session_id, course=subscription)
            session.is_completed = True
            session.save()
            
            # Add to completed sessions
            subscription.completed_sessions.add(session)
            
            # Check if all sessions are completed
            if sessions.filter(is_completed=False).count() == 0:
                subscription.status = 'finished'
                subscription.save()
        
        elif action == 'add_url':
            session = get_object_or_404(Session, id=session_id, course=subscription)
            session_url = request.POST.get('session_url')
            session.session_url = session_url
            session.save()
        
        return redirect('courses:course_detail', course_id=course.id)
    
    return render(request, 'courses/course_detail.html', context)

@login_required
def add_to_cart(request):
    """Add courses, tracks, or levels to the cart."""
    if request.method == 'POST':
        item_type = request.POST.get('item_type')
        item_id = request.POST.get('item_id')

        if item_type == 'course':
            course = get_object_or_404(Course, id=item_id)
            CartCourse.objects.get_or_create(student=request.user, course=course)
            message = f"Course '{course.name}' added to cart!"
        
        elif item_type == 'track':
            track = get_object_or_404(Track, id=item_id)
            CartTrack.objects.get_or_create(student=request.user, track=track)
            message = f"Track '{track.name}' added to cart!"
        
        elif item_type == 'level':
            level = get_object_or_404(Level, id=item_id)
            CartLevel.objects.get_or_create(student=request.user, level=level)
            message = f"Level '{level.name}' added to cart!"
        
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid item type'})

        return JsonResponse({'status': 'success', 'message': message})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def cart_view(request):
    language = request.GET.get('lang', 'en')  # Default to 'en' if no language is specified

    # Fetching cart items for the logged-in user
    cart_courses = CartCourse.objects.filter(student=request.user)
    cart_tracks = CartTrack.objects.filter(student=request.user)
    cart_levels = CartLevel.objects.filter(student=request.user)

    # Translate cart items
    translated_cart_courses = []
    for cart_course in cart_courses:
        course_translation = CourseTranslation.objects.filter(course=cart_course.course, language=language).first()
        translated_cart_courses.append({
            'id': cart_course.course.id,
            'name': course_translation.translated_name if course_translation else cart_course.course.name,
            'description': course_translation.translated_description if course_translation else cart_course.course.description,
            'price_without_any_discount': cart_course.course.price_without_any_discount,
            'discount_percent': cart_course.course.discount_percent,
            'has_discount': cart_course.course.has_discount,
            'final_price_after_discound': cart_course.course.final_price_after_discound,
            'image': cart_course.course.image,
        })

    translated_cart_tracks = []
    for cart_track in cart_tracks:
        track_translation = TrackTranslation.objects.filter(track=cart_track.track, language=language).first()
        translated_cart_tracks.append({
            'id': cart_track.track.id,
            'name': track_translation.translated_name if track_translation else cart_track.track.name,
            'description': track_translation.translated_description if track_translation else cart_track.track.description,
            'price_without_any_discount': cart_track.track.price_without_any_discount,
            'discount_percent': cart_track.track.discount_percent,
            'has_discount': cart_track.track.has_discount,
            'final_price_after_discound': cart_track.track.final_price_after_discound,
            'image': cart_track.track.image,
        })

    translated_cart_levels = []
    for cart_level in cart_levels:
        level_translation = LevelTranslation.objects.filter(level=cart_level.level, language=language).first()
        translated_cart_levels.append({
            'id': cart_level.level.id,
            'name': level_translation.translated_name if level_translation else cart_level.level.name,
            'description': level_translation.translated_description if level_translation else cart_level.level.description,
            'price_without_any_discount': cart_level.level.price_without_any_discount,
            'discount_percent': cart_level.level.discount_percent,
            'has_discount': cart_level.level.has_discount,
            'final_price_after_discound': cart_level.level.final_price_after_discound,
            'image': cart_level.level.image,
        })

    # Fetch pending orders
    pending_orders = Order.objects.filter(student=request.user, status='pending')

    # Calculating total prices ensuring all are Decimal
    total_courses = sum(Decimal(cart_course.course.final_price_after_discound) for cart_course in cart_courses if cart_course.course)
    total_tracks = sum(Decimal(cart_track.track.final_price_after_discound) for cart_track in cart_tracks if cart_track.track)
    total_levels = sum(Decimal(cart_level.level.final_price_after_discound) for cart_level in cart_levels if cart_level.level)

    # Total price calculation
    total_price = total_courses + total_tracks + total_levels

    # Calculate total price for each pending order
    for order in pending_orders:
        order.total_price = order.calculate_total_price()
        order.save()

    # Preparing context
    context = {
        'cart_courses': translated_cart_courses,
        'cart_tracks': translated_cart_tracks,
        'cart_levels': translated_cart_levels,
        'total_price': total_price,
        'pending_orders': pending_orders,
    }

    return render(request, 'courses/cart.html', context)






@csrf_exempt
@login_required
def create_order(request):
    if request.method == 'POST':
        try:
            # Create a new order
            order = Order.objects.create(student=request.user)

            # Get cart items
            cart_courses = CartCourse.objects.filter(student=request.user)
            cart_tracks = CartTrack.objects.filter(student=request.user)
            cart_levels = CartLevel.objects.filter(student=request.user)

            # Add items to the order
            for cart_course in cart_courses:
                if cart_course.course:
                    ct = ContentType.objects.get_for_model(cart_course.course)
                    OrderItem.objects.create(order=order, content_type=ct, object_id=cart_course.course.id)
            for cart_track in cart_tracks:
                if cart_track.track:
                    ct = ContentType.objects.get_for_model(cart_track.track)
                    OrderItem.objects.create(order=order, content_type=ct, object_id=cart_track.track.id)
            for cart_level in cart_levels:
                if cart_level.level:
                    ct = ContentType.objects.get_for_model(cart_level.level)
                    OrderItem.objects.create(order=order, content_type=ct, object_id=cart_level.level.id)

            # Clear the cart
            cart_courses.delete()
            cart_tracks.delete()
            cart_levels.delete()

            # Calculate the total price for the new order
            total_price = order.calculate_total_price()
            order.total_price = total_price
            order.save()

            # Return the order details as JSON
            return JsonResponse({
                'status': 'success',
                'message': 'Order created successfully.',
                'order_id': order.order_id,
                'total_price': total_price,
                'items': [{'name': item.content_object.name, 'price': item.content_object.final_price_after_discound} for item in order.items.all()]
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@login_required
def remove_from_cart_course(request):
    """Remove a course from the cart."""
    if request.method == 'POST':
        cart_item_id = request.POST.get('item_id')
        cart_item = get_object_or_404(CartCourse, id=cart_item_id, student=request.user)
        cart_item.delete()
        return JsonResponse({'status': 'success', 'message': 'Course removed from cart!'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def remove_from_cart_track(request):
    """Remove a track from the cart."""
    if request.method == 'POST':
        cart_item_id = request.POST.get('item_id')
        cart_item = get_object_or_404(CartTrack, id=cart_item_id, student=request.user)
        cart_item.delete()
        return JsonResponse({'status': 'success', 'message': 'Track removed from cart!'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def remove_from_cart_level(request):
    """Remove a level from the cart."""
    if request.method == 'POST':
        cart_item_id = request.POST.get('item_id')
        cart_item = get_object_or_404(CartLevel, id=cart_item_id, student=request.user)
        cart_item.delete()
        return JsonResponse({'status': 'success', 'message': 'Level removed from cart!'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def courses_view(request):
    cart_course_ids = CartCourse.objects.filter(student=request.user).values_list('course_id', flat=True)
    cart_track_ids = CartTrack.objects.filter(student=request.user).values_list('track_id', flat=True)
    cart_level_ids = CartLevel.objects.filter(student=request.user).values_list('level_id', flat=True)

    context = {
        'courses': Course.objects.all(),
        'tracks': Track.objects.all(),
        'levels': Level.objects.all(),
        'cart_course_ids': list(cart_course_ids),
        'cart_track_ids': list(cart_track_ids),
        'cart_level_ids': list(cart_level_ids),
    }
    return render(request, 'courses.html', context)

@login_required
def cart_count(request):
    cart_count = CartCourse.objects.filter(student=request.user).count() + \
                 CartTrack.objects.filter(student=request.user).count() + \
                 CartLevel.objects.filter(student=request.user).count()
    return JsonResponse({'cart_count': cart_count})

@login_required
def add_to_love(request):
    """Handle adding/removing loved items (courses/tracks)"""
    if request.method == 'POST':
        item_type = request.POST.get('item_type')
        item_id = int(request.POST.get('item_id'))
        student = request.user

        if item_type == 'course':
            course = get_object_or_404(Course, id=item_id)
            # Check if course is already loved
            love, created = LoveCourse.objects.get_or_create(student=student, course=course)
            if not created:  # If already exists, remove it
                love.delete()
                return JsonResponse({'status': 'removed', 'message': 'Course removed from Loved List.'})
            return JsonResponse({'status': 'success', 'message': 'Course added to Loved List.'})

        elif item_type == 'track':
            track = get_object_or_404(Track, id=item_id)
            # Check if track is already loved
            love, created = LoveTrack.objects.get_or_create(student=student, track=track)
            if not created:  # If already exists, remove it
                love.delete()
                return JsonResponse({'status': 'removed', 'message': 'Track removed from Loved List.'})
            return JsonResponse({'status': 'success', 'message': 'Track added to Loved List.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


@login_required
def loved_items(request):
    language = request.GET.get('lang', 'en')  # Default to 'en' if no language is specified

    # Fetch loved items for the logged-in user
    loved_courses = LoveCourse.objects.select_related('course').filter(student=request.user)
    loved_tracks = LoveTrack.objects.select_related('track').filter(student=request.user)

    # Translate loved items
    translated_loved_courses = []
    for loved_course in loved_courses:
        course_translation = CourseTranslation.objects.filter(course=loved_course.course, language=language).first()
        final_price_after_discount = loved_course.course.price_without_any_discount
        if loved_course.course.has_discount:
            discount_factor = Decimal(1) - (Decimal(loved_course.course.discount_percent) / Decimal(100))
            final_price_after_discount = loved_course.course.price_without_any_discount * discount_factor

        translated_loved_courses.append({
            'id': loved_course.course.id,
            'preview_video': loved_course.course.preview_video,
            'name': course_translation.translated_name if course_translation else loved_course.course.name,
            'description': course_translation.translated_description if course_translation else loved_course.course.description,
            'price_without_any_discount': loved_course.course.price_without_any_discount,
            'discount_percent': loved_course.course.discount_percent,
            'has_discount': loved_course.course.has_discount,
            'final_price_after_discount': final_price_after_discount,
            'image': loved_course.course.image,
            'level': loved_course.course.level,
            'sessions': loved_course.course.coursesessions.all(),
        })

    translated_loved_tracks = []
    for loved_track in loved_tracks:
        track_translation = TrackTranslation.objects.filter(track=loved_track.track, language=language).first()
        final_price_after_discount = loved_track.track.price_without_any_discount
        if loved_track.track.has_discount:
            discount_factor = Decimal(1) - (Decimal(loved_track.track.discount_percent) / Decimal(100))
            final_price_after_discount = loved_track.track.price_without_any_discount * discount_factor

        translated_loved_tracks.append({
            'id': loved_track.track.id,
            'name': track_translation.translated_name if track_translation else loved_track.track.name,
            'description': track_translation.translated_description if track_translation else loved_track.track.description,
            'price_without_any_discount': loved_track.track.price_without_any_discount,
            'discount_percent': loved_track.track.discount_percent,
            'has_discount': loved_track.track.has_discount,
            'final_price_after_discount': final_price_after_discount,
            'image': loved_track.track.image,
            'level': loved_track.track.level,
            'preview_video': loved_track.track.preview_video,
        })

    # Get cart items to disable "Add to Cart" buttons
    cart_course_ids = CartCourse.objects.filter(student=request.user).values_list('course_id', flat=True)
    cart_track_ids = CartTrack.objects.filter(student=request.user).values_list('track_id', flat=True)

    context = {
        'loved_courses': translated_loved_courses,
        'loved_tracks': translated_loved_tracks,
        'cart_course_ids': cart_course_ids,
        'cart_track_ids': cart_track_ids,
    }
    return render(request, 'courses/loved_items.html', context)

@csrf_exempt
def remove_from_love(request):
    """Remove a course or track from the loved list."""
    if request.method == 'POST' and request.user.is_authenticated:
        item_type = request.POST.get('item_type')
        item_id = request.POST.get('item_id')

        try:
            if item_type == 'course':
                # Remove the course from the loved list
                LoveCourse.objects.filter(student=request.user, course_id=item_id).delete()
            elif item_type == 'track':
                # Remove the track from the loved list
                LoveTrack.objects.filter(student=request.user, track_id=item_id).delete()
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid item type'})

            return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})





from django.http import JsonResponse

def debug_location(request):
    return JsonResponse({
        'is_egypt': request.is_egypt,
        'ip': request.META.get('REMOTE_ADDR'),
        'x_forwarded_for': request.META.get('HTTP_X_FORWARDED_FOR', '')
    })