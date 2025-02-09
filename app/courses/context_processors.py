from carts.models import CartCourse, CartTrack, CartLevel

def cart_content(request):
    if request.user.is_authenticated:
        cart_courses = CartCourse.objects.filter(student=request.user)
        cart_tracks = CartTrack.objects.filter(student=request.user)
        cart_levels = CartLevel.objects.filter(student=request.user)
        cart_count = cart_courses.count() + cart_tracks.count() + cart_levels.count()
        
        return {
            'cart_courses': cart_courses,
            'cart_tracks': cart_tracks,
            'cart_levels': cart_levels,
            'cart_count': cart_count,
        }
    return {'cart_courses': [], 'cart_tracks': [], 'cart_levels': [], 'cart_count': 0}


