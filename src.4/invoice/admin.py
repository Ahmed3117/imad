from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(PromoCode)


class InvoiceAdmin(admin.ModelAdmin):
    search_fields = ['student__user__username','sequence']  

admin.site.register(Invoice, InvoiceAdmin)

admin.site.register(BalanceTransaction)