from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_cost', 'price_at_purchase')
    fields = ('product', 'quantity', 'price_at_purchase', 'total_cost')

    def total_cost(self, obj):
        return f"{obj.total_cost} RWF"
    total_cost.short_description = "Line Total"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'discount', 'discount_amount', 'get_subtotal', 'get_total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'id')
    readonly_fields = ('id', 'discount_amount', 'get_subtotal', 'get_total', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    actions = ['apply_discounts']

    def get_subtotal(self, obj):
        return f"{obj.subtotal} RWF"
    get_subtotal.short_description = "Subtotal"

    def get_total(self, obj):
        return f"{obj.total_amount} RWF"
    get_total.short_description = "Total"

    def apply_discounts(self, request, queryset):
        for order in queryset:
            order.apply_discount()
        self.message_user(request, f"Discounts applied to {queryset.count()} order(s).")
    apply_discounts.short_description = "Apply discounts to selected orders"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price_at_purchase', 'get_total_cost')
    search_fields = ('order__id', 'product__name')
    readonly_fields = ('id', 'price_at_purchase', 'get_total_cost')

    def get_total_cost(self, obj):
        return f"{obj.total_cost} RWF"
    get_total_cost.short_description = "Line Total"