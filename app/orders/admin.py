from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('get_content_type', 'content_object', 'added_at')  # Make all fields readonly
    fields = ('get_content_type', 'content_object', 'added_at')  # Specify fields to display
    can_delete = False  # Disable delete option

    # Customize content_type display
    def get_content_type(self, obj):
        return obj.content_type.name.split(' | ')[-1].strip() # Return only model_name

    # Hide the 'Add another' button by modifying the formset
    def has_add_permission(self, request, obj=None):
        return False  # Prevent adding new items

    def has_change_permission(self, request, obj=None):
        return False  # Prevent changing existing items

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_id', 'student__username', 'student__first_name', 'student__last_name')  # Search by related fields
    readonly_fields = ('student','order_id', 'created_at', 'total_price')  # Total price should be calculated, not directly editable
    inlines = [OrderItemInline]

    # Calculate total price when saving. We iterate because content_object could have different price attributes
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        total = 0
        for item in obj.items.all():  # obj.items is thanks to related_name in OrderItem model
            try:  # Try standard price field name, expecting a DecimalField or float on the content_object
                total += item.content_object.price
            except AttributeError:
                try:  # Try 'cost' as price attribute name
                    total += item.content_object.cost
                except AttributeError:
                    # Handle gracefully items that don't have cost or price; Log it! Consider custom logic as needed.
                    print(f"Warning: Order Item {item} does not have a 'price' or 'cost' attribute. Check Content Type: {item.content_type}") 
        obj.total_price = total
        obj.save()
        
    # Improve admin display
    def student(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name} ({obj.student.username})"
