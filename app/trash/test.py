{% extends 'base.html' %}
{% load custom_filters %}
{% load static %}

{% block translationFolder %}data-translation-folder="levels"{% endblock %}
{% block title %}Courses{% endblock %}
{% load custom_filters %}
{% block content %}

<section class="container py-4 card px-4 mt-4">
    <ul class="nav nav-tabs mb-3" id="levelTabs" role="tablist">
        {% for level in levels %}
        <li class="nav-item" role="presentation">
            <button class="nav-link circle-nav {% if forloop.first %}active{% endif %}"
                    id="level-{{ level.id }}-tab"
                    data-mdb-toggle="tab"
                    data-mdb-target="#level-{{ level.id }}"
                    type="button"
                    role="tab"
                    aria-controls="level-{{ level.id }}"
                    aria-selected="{% if forloop.first %}true{% else %}false{% endif %}">
                {{ level.name }}
            </button>
        </li>
        {% endfor %}
    </ul>
    
    

    <!-- Tab Contents -->
    <div class="tab-content" id="levelTabsContent">
        {% for level in levels %}
        <div class="tab-pane fade {% if forloop.first %}show active{% endif %}"
             id="level-{{ level.id }}"
             role="tabpanel"
             aria-labelledby="level-{{ level.id }}-tab">
            <div class="row d-flex align-items-start ">
                <!-- Level Summary Section -->
                <div class="mb-5 col-lg-4 col-md-6 p-3 bg-white shadow rounded text-center gift-card">
                    <!-- Image and Video Icon Container -->
                    <div class="d-flex justify-content-center align-items-center mb-2 position-relative">
                        <img src="{{ level.image.url }}" alt="Level Icon" class="img-fluid" style="width: 150px; height: 150px;">
                        <!-- Video Icon -->
                        <div class="ms-3"> <!-- Add margin to separate the icon from the image -->
                            {% include "courses/partials/level_video.html" with preview_video=level.preview_video %}
                        </div>
                    </div>
                
                    <!-- Level Name -->
                    <p class="fw-bold text-primary mx-2 text-center display-6">{{ level.name }}</p>
                
                    <!-- Level Description -->
                    <span class="mx-2 my-5 text-center">{{ level.description }}</span>
                
                    <!-- Year Limit -->
                    <p class="fw-bold text-primary mt-3">{{ level.year_limit }}</p>
                
                    <!-- Pricing Section -->
                    {% if level.enable_pricing %}
                        {% if level.has_discount %}
                            <div class="card shadow py-2 px-1 gift-price-card">
                                <p class="h6 text-success">🎁 <span data-translate="get_level_better_price">Get the level at a better price!</span> 🎉</p>
                                <p class="price-info">
                                    <span class="old-price">EGP{{ level.price_without_any_discount }}</span>
                                    <span class="discount">-{{ level.discount_percent }}%</span>
                                    <span class="final-price fw-bold">EGP{{ level.final_price_after_discound }}</span>
                                </p>
                            </div>
                        {% else %}
                            <div class="card shadow py-2 px-1">
                                <p class="price-info">
                                    <span class="old-price">EGP{{ level.price_without_any_discount }}</span>
                                </p>
                            </div>
                        {% endif %}
                    {% endif %}
                
                    <!-- Add to Cart Button -->
                    {% if request.user.is_authenticated %}
                        {% if level.enable_pricing %}
                            <a href="#"
                                class="my-3 btn btn-primary add-to-cart {% if level.id in cart_level_ids %}disabled {% endif %}"
                                data-type="level"
                                data-name="{{ level.name }}"
                                data-id="{{ level.id }}">
                                {% if level.id in cart_level_ids %}
                                    <i class="fas fa-check"></i> <span data-translate="added">Added</span>
                                {% else %}
                                    <i class="fas fa-cart-plus"></i> <span data-translate="add_level_to_cart">Add Level to Cart</span>
                                {% endif %}
                            </a>
                        {% endif %}
                    {% else %}
                        <a href="{% url 'accounts:login' %}?next={{ request.path }}" class="btn btn-outline-primary btn-sm">
                            <i class="fas fa-sign-in-alt"></i> <span data-translate="login_to_add">Login to Add to card</span>
                        </a>
                    {% endif %}
                
                    <!-- Level Content -->
                    <div class="text-start p-4 card custom-card mt-3">
                        <h4 class="mb-4 text-center" data-translate="level_content">Content</h4>
                        <ul class="list-unstyled mb-0">
                            {% for content in level.levelcontent %}
                            <li class="mb-2 mx-3 text-secondary">
                                <span class="text-primary me-1">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 16 16">
                                        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
                                        <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z" />
                                    </svg>
                                </span>
                                <span>{{ content.name }}</span>
                            </li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
                

                <!-- Courses and Tracks Section -->
                <div class="col-lg-8 col-md-6 mt-sm-3">
                    <!-- Main Tabs -->
                    <ul class="nav nav-pills mb-2" id="mainTab-{{ level.id }}" role="tablist">
                        {% if level.individual_courses %}
                        <li class="nav-item" role="presentation">
                            <a class="nav-link active px-2 fw-bold"
                               id="individual-{{ level.id }}-tab"
                               data-mdb-toggle="pill"
                               href="#individual-{{ level.id }}"
                               role="tab"
                               aria-selected="true"><span data-translate="individual_courses">Individual Courses</span></a>
                        </li>
                        {% endif %}
                        {% if level.tracks %}
                        <li class="nav-item " role="presentation">
                            <a class="nav-link px-2 fw-bold"
                               id="tracks-{{ level.id }}-tab"
                               data-mdb-toggle="pill"
                               href="#tracks-{{ level.id }}"
                               role="tab"
                               aria-selected="false"><span data-translate="full_tracks">Full Tracks</span></a>
                        </li>
                        {% endif %}
                    </ul>

                    <div class="tab-content" id="mainTabContent-{{ level.id }}">
                        <!-- Individual Courses Tab -->
                        <div class="tab-pane fade show active"
                             id="individual-{{ level.id }}"
                             role="tabpanel">
                            {% for course in level.individual_courses %}
                            {% include "courses/partials/course_card.html" with course=course %}
                            {% endfor %}
                        </div>

                        <!-- Tracks Tab -->
                        {% if level.tracks %}
                        <div class="tab-pane fade my-3"
                             id="tracks-{{ level.id }}"
                             role="tabpanel">
                             <!-- Track Tabs -->
                            <ul class="nav nav-tabs mb-2" id="trackTab-{{ level.id }}" role="tablist">
                                {% for track in level.tracks %}
                                    <li class="nav-item" role="presentation">
                                        <a class="nav-link {% if forloop.first %}active{% endif %}"
                                        id="track-{{ track.id }}-{{ level.id }}-tab"
                                        data-mdb-toggle="tab"
                                        href="{% url 'courses:levels' %}#level-{{ level.id }}-track-{{ track.id }}"
                                        role="tab"
                                        aria-selected="{% if forloop.first %}true{% else %}false{% endif %}">
                                            {{ track.name }}
                                        </a>
                                    </li>
                                {% endfor %}
                            </ul>

                            <div class="tab-content py-3" id="trackTabContent-{{ level.id }}">
                                {% for track in level.tracks %}
                                <div class="tab-pane fade {% if forloop.first %}show active{% endif %}"
                                    id="track-{{ track.id }}-{{ level.id }}"
                                    role="tabpanel">


                                    <div class="card p-3 shadow-sm" style="border: 2px dashed var(--main-color);">
                                        <!-- Description Section -->
                                        <div class="card p-2 card-bg custom-card mb-3">
                                            <p class="text-secondary fw-bold mb-0" data-translate="description">Description:</p>
                                            <span class="px-3">{{ track.description }}</span>
                                            
                                        </div>
                                    
                                        <!-- Buttons Section (Authenticated Users Only) -->
                                        {% if request.user.is_authenticated %}
                                        <div class="d-flex justify-content-end gap-2 my-2">
                                            <!-- Add to Cart Button -->
                                            <a href="#"
                                               class="btn btn-outline-primary btn-sm add-to-cart {% if track.id in cart_track_ids %}disabled{% endif %}"
                                               data-type="track"
                                               data-name="{{ track.name }}"
                                               data-id="{{ track.id }}">
                                                {% if track.id in cart_track_ids %}
                                                    <i class="fas fa-check"></i> <span data-translate="added">Added</span>
                                                {% else %}
                                                    <i class="fas fa-cart-plus"></i> <span data-translate="add_track_to_cart">Add Track to Cart</span>
                                                {% endif %}
                                            </a>
                                    
                                            <!-- Add to Love Button -->
                                            <a href="#"
                                               class="btn btn-sm add-to-love {% if track.id in loved_track_ids %}disabled{% endif %}"
                                               data-type="track"
                                               data-id="{{ track.id }}">
                                                {% if track.id in loved_track_ids %}
                                                    <i class="fas fa-heart"></i>
                                                {% else %}
                                                    <i class="fas fa-heart text-danger"></i>
                                                {% endif %}
                                            </a>
                                            {% if track.preview_video %}
                                                {% include "courses/partials/track_video.html" with preview_video=track.preview_video %}
                                            {% endif %}
                                        </div>
                                        {% else %}
                                        <a href="{% url 'accounts:login' %}?next={{ request.path }}" class="btn btn-outline-primary btn-sm">
                                            <i class="fas fa-sign-in-alt"></i> <span data-translate="login_to_add">Login to Add to card</span>
                                        </a>
                                        {% endif %}
                                    
                                        <!-- Price Section -->
                                        <div class="mt-2">
                                            {% if track.has_discount %}
                                                <div class="d-flex align-items-center gap-2">
                                                    <span class="old-price text-muted text-decoration-line-through">EGP{{ track.price_without_any_discount }}</span>
                                                    <span class="discount text-danger">-{{ track.discount_percent }}%</span>
                                                    <span class="final-price fw-bold text-primary">EGP{{ track.final_price_after_discound }}</span>
                                                </div>
                                            {% else %}
                                                <span class="final-price fw-bold text-primary">EGP{{ track.price_without_any_discount }}</span>
                                            {% endif %}
                                        </div>
                                    </div>
                                    

                                    {% for course in track.courses %}
                                    {% include "courses/partials/course_card.html" with course=course %}
                                    {% endfor %}
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

</section>










<script>
    
    document.addEventListener('DOMContentLoaded', function () {
    
        // Handle "Add to Cart" functionality
        const cartButtons = document.querySelectorAll('.add-to-cart');
        cartButtons.forEach(button => {
            button.addEventListener('click', function (event) {
                event.preventDefault();
                const itemType = button.dataset.type;
                const itemId = button.dataset.id;
    
                if (button.classList.contains('disabled')) return;
    
                fetch('/courses/add-to-cart/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': getCSRFToken(),
                    },
                    body: `item_type=${itemType}&item_id=${itemId}`
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showToast('success', data.message); // Use toast instead of alert
                        button.innerHTML = '<i class="fas fa-check"></i> Added';
                        button.classList.add('disabled');
                        updateCartIcon();
                    } else {
                        showToast('error', data.message); // Use toast for error
                    }
                });
            });
        });
    
        // Handle "Add to Love" (or "Remove from Love") functionality
        const loveButtons = document.querySelectorAll('.add-to-love');
        loveButtons.forEach(button => {
            button.addEventListener('click', function (event) {
                event.preventDefault();
                const itemType = button.dataset.type;
                const itemId = button.dataset.id;
    
                fetch('/courses/add-to-love/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': getCSRFToken(),
                    },
                    body: `item_type=${itemType}&item_id=${itemId}`
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        button.innerHTML = '<i class="fas fa-heart"></i> Loved';
                        button.classList.add('disabled');
                        showToast('success', data.message); // Use toast for success
                    } else if (data.status === 'removed') {
                        button.innerHTML = '<i class="fas fa-heart"></i> Add to Love';
                        button.classList.remove('disabled');
                        showToast('warning', data.message); // Use toast for removal
                    } else {
                        showToast('error', data.message); // Use toast for error
                    }
                });
            });
        });
    
        // Function to update the cart icon
        function updateCartIcon() {
            fetch('/courses/cart-count/')
                .then(response => response.json())
                .then(data => {
                    const cartCountElement = document.querySelector('.cart-count');
                    if (cartCountElement) {
                        cartCountElement.textContent = data.cart_count;
                    }
                });
        }
    
        // Function to get CSRF token
        function getCSRFToken() {
            const csrfToken = document.cookie.match(/csrftoken=([^;]+)/);
            return csrfToken ? csrfToken[1] : '';
        }
    
        // Function to add and display toast messages
        function showToast(type, message) {
            const toastContainer = document.createElement('div');
            toastContainer.classList.add('toast', 'align-items-center', 'fade', 'show', 'm-1', `bg-${type}`);
            toastContainer.setAttribute('role', 'alert');
            toastContainer.setAttribute('aria-live', 'assertive');
            toastContainer.setAttribute('aria-atomic', 'true');
            toastContainer.style.maxWidth = '350px';
    
            // Toast content
            const toastContent = `
                <div class="d-flex">
                    <div class="toast-body">
                        ${getToastIcon(type)} ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            `;
    
            toastContainer.innerHTML = toastContent;
    
            // Append toast to the page
            const toastWrapper = document.querySelector('.toast-wrapper') || createToastWrapper();
            toastWrapper.appendChild(toastContainer);
    
            // Automatically remove the toast after 5 seconds
            setTimeout(() => {
                toastContainer.classList.remove('show');
                setTimeout(() => toastContainer.remove(), 300); // Allow fade-out animation
            }, 5000);
        }
    
        // Function to get the appropriate icon for the toast message type
        function getToastIcon(type) {
            if (type === 'success') {
                return '<i class="fas fa-check-circle me-2"></i>';
            } else if (type === 'error') {
                return '<i class="fas fa-exclamation-circle me-2"></i>';
            } else if (type === 'warning') {
                return '<i class="fas fa-exclamation-triangle me-2"></i>';
            }
            return ''; // Default: no icon
        }
    
        // Create a wrapper for toasts if it doesn't exist
        function createToastWrapper() {
            const wrapper = document.createElement('div');
            wrapper.classList.add('toast-wrapper', 'position-fixed', 'top-0', 'end-0', 'p-3');
            wrapper.style.zIndex = '1055'; // Ensure it appears above other elements
            document.body.appendChild(wrapper);
            return wrapper;
        }
    });
</script>


<script src="{% static 'js/levels.js' %}"></script>
{% endblock %}
<a href="{% url 'courses:levels' %}#level-{{ level.id }}">{{ level.name }}</a>