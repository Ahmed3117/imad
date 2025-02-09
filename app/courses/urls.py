

from django.urls import path
from .views import add_to_cart, add_to_love, cart_count, cart_view, course_detail, courses_view, create_order, debug_location, levels, loved_items, remove_from_cart_course, remove_from_cart_level, remove_from_cart_track, remove_from_love

app_name='courses'

urlpatterns = [
    path('levels/',levels,name='levels'),
    path('<int:course_id>/', course_detail, name='course_detail'),
    path('cart/', cart_view, name='cart'),
    path('add-to-cart/', add_to_cart, name='add_to_cart'),
    path('create-order/', create_order, name='create_order'),
    path('remove-from-cart-course/', remove_from_cart_course, name='remove_from_cart_course'),
    path('remove-from-cart-track/', remove_from_cart_track, name='remove_from_cart_track'),
    path('remove-from-cart-level/', remove_from_cart_level, name='remove_from_cart_level'),
    path('cart-count/', cart_count, name='cart_count'),
    path('courses-view/', courses_view, name='courses_view'),
    path('add-to-love/', add_to_love, name='add_to_love'),
    path('loved-items/', loved_items, name='loved_items'),
    path('remove-from-love/', remove_from_love, name='remove_from_love'),

    path('debug-location/', debug_location, name='debug_location'),
]