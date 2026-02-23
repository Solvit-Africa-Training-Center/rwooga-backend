from django.contrib import admin
from django.shortcuts import redirect
from django.contrib import messages
from .models import ServiceCategory, Product, ProductMedia, Feedback, CustomRequest,ControlRequest, Wishlist, WishlistItem, Discount, ProductDiscount


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1


class FeedbackInline(admin.TabularInline):
    model = Feedback
    extra = 0
    readonly_fields = ['client_name', 'rating', 'message', 'created_at']


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_active', 'created_at']  # Removed duplicate 'id'
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'unit_price', 'published', 'created_at']
    list_filter = ['published', 'category', 'created_at']
    search_fields = ['name', 'short_description']
    readonly_fields = ['slug', 'created_at', 'updated_at']  # Removed 'product_volume'
    inlines = [ProductMediaInline, FeedbackInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'category', 'short_description', 'detailed_description')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'currency')
        }),
        ('Dimensions', {
            'fields': ('length', 'width', 'height', 'measurement_unit', 'material')  # Removed 'product_volume'
        }),
        ('Product Variations', {
            'fields': ('available_sizes', 'available_colors', 'available_materials'),  # Removed duplicate
            'description': 'Enter comma-separated values (e.g., Small, Medium, Large)'
        }),
        ('Publishing', {
            'fields': ('published', 'uploaded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    list_display = ['product', 'display_order', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['product__name', 'alt_text']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['product', 'client_name', 'rating', 'published', 'created_at']
    list_filter = ['published', 'rating', 'created_at']
    search_fields = ['client_name', 'message', 'product__name']
    actions = ['make_published', 'make_unpublished']
    
    def make_published(self, request, queryset):
        queryset.update(published=True)
    make_published.short_description = "Publish selected feedback"
    
    def make_unpublished(self, request, queryset):
        queryset.update(published=False)
    make_unpublished.short_description = "Unpublish selected feedback"


@admin.register(CustomRequest)
class CustomRequestAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'title', 'service_category', 'status', 'created_at']
    list_filter = ['status', 'service_category', 'created_at']
    search_fields = ['client_name', 'client_email', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('client_name', 'client_email', 'client_phone')
        }),
        ('Request Details', {
            'fields': ('service_category', 'title', 'description', 'reference_file', 'budget')
        }),
        ('Status & Notes', {
            'fields': ('status',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_in_progress', 'mark_completed', 'mark_cancelled']
    
    def mark_in_progress(self, request, queryset):
        queryset.update(status='IN_PROGRESS')
    mark_in_progress.short_description = "Mark as In Progress"
    
    def mark_completed(self, request, queryset):
        queryset.update(status='COMPLETED')
    mark_completed.short_description = "Mark as Completed"
    
    def mark_cancelled(self, request, queryset):
        queryset.update(status='CANCELLED')
    mark_cancelled.short_description = "Mark as Cancelled"



@admin.register(ControlRequest)
class ControlRequestAdmin(admin.ModelAdmin):
    # ── Columns shown in the changelist ──────────────────────────────────────
    list_display = [
        'status_badge',
        'allow_custom_requests',
        'max_pending_requests',
        'pending_count',
        'disable_reason',
    ]
    list_editable = ['allow_custom_requests', 'max_pending_requests', 'disable_reason']

    # ── Fields shown in the change-form ──────────────────────────────────────
    fieldsets = (
        ('Toggle', {
            'fields': ('allow_custom_requests',),
            'description': (
                'Turn custom-request submissions ON or OFF globally. '
                'Use the <b>Enable / Disable</b> actions below for quick one-click control.'
            ),
        }),
        ('Capacity Settings', {
            'fields': ('max_pending_requests',),
            'description': (
                'Set to 0 to remove the cap. '
                'When the number of PENDING requests equals this value, new submissions are blocked automatically.'
            ),
        }),
        ('Disable Message', {
            'fields': ('disable_reason',),
            'description': 'Optional message shown to customers when submissions are closed.',
        }),
    )

    # ── Bulk actions (work from the changelist checkboxes) ────────────────────
    actions = ['action_enable_requests', 'action_disable_requests']

    # ── Singleton guard ───────────────────────────────────────────────────────
    def has_add_permission(self, request):
        """Only allow adding when no record exists yet (singleton pattern)."""
        return not ControlRequest.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent accidental deletion of the singleton record."""
        return False

    # ── Custom display methods ────────────────────────────────────────────────
    @admin.display(description='Status')
    def status_badge(self, obj):
        from django.utils.html import format_html
        if obj.allow_custom_requests:
            colour, label = '#28a745', ' OPEN'
        else:
            colour, label = '#dc3545', ' CLOSED'
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            colour, label,
        )

    @admin.display(description='Pending Requests')
    def pending_count(self, obj):
        from django.utils.html import format_html
        count = CustomRequest.objects.filter(status='PENDING').count()
        cap = obj.max_pending_requests
        colour = '#dc3545' if (cap and count >= cap) else '#495057'
        return format_html(
            '<span style="color:{};font-weight:bold;">{} / {}</span>',
            colour, count, cap if cap else '∞',
        )

    # ── Quick-action helpers ──────────────────────────────────────────────────
    @admin.action(description=' Enable custom-request submissions')
    def action_enable_requests(self, request, queryset):
        ctrl = ControlRequest.get()
        ctrl.allow_custom_requests = True
        ctrl.save()
        self.message_user(
            request,
            'Custom requests are now ENABLED.',
            messages.SUCCESS,
        )

    @admin.action(description=' Disable custom-request submissions')
    def action_disable_requests(self, request, queryset):
        ctrl = ControlRequest.get()
        ctrl.allow_custom_requests = False
        ctrl.save()
        self.message_user(
            request,
            'Custom requests are now DISABLED.',
            messages.WARNING,
        )

    # ── Override change_view to always redirect to the singleton record ───────
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        ctrl = ControlRequest.get()
        is_open, reason = ControlRequest.requests_are_open()
        pending = CustomRequest.objects.filter(status='PENDING').count()
        extra_context['control_stats'] = {
            'is_open': is_open,
            'reason': reason,
            'pending': pending,
            'max': ctrl.max_pending_requests,
        }
        return super().change_view(request, object_id, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        """Auto-redirect to the singleton edit page when there is exactly one record."""
        ctrl = ControlRequest.get()          # ensure the record exists
        extra_context = extra_context or {}

        # Inject a live summary banner into the changelist
        is_open, reason = ControlRequest.requests_are_open()
        pending = CustomRequest.objects.filter(status='PENDING').count()
        extra_context['live_status'] = {
            'is_open': is_open,
            'reason': reason,
            'pending': pending,
            'max': ctrl.max_pending_requests,
        }
        return super().changelist_view(request, extra_context=extra_context)

class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ['product', 'created_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_item_count', 'created_at']
    search_fields = ['user__full_name', 'user__email']
    readonly_fields = ['created_at']
    inlines = [WishlistItemInline]
    
    def get_item_count(self, obj):
        return obj.items.count()
    get_item_count.short_description = 'Items'


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['wishlist', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['wishlist__user__full_name', 'product__name']
    readonly_fields = ['created_at']


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "discount_type",
        "discount_value",
        "is_active",
        "start_date",
        "end_date",
    )
    list_filter = ("discount_type", "is_active")
    search_fields = ("name",)
    date_hierarchy = "start_date"


@admin.register(ProductDiscount)
class ProductDiscountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "discount",
        "is_valid",
        "created_at",
    )
    list_filter = ("is_valid",)
    search_fields = ("product__name", "discount__name")