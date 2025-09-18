from django.contrib import admin
from .models import CustomDesignRequest, Order,Rating

admin.site.register(CustomDesignRequest)
admin.site.register(Order)
admin.site.register(Rating)