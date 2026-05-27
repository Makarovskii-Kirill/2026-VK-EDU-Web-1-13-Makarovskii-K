from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch
from django.utils.html import format_html
from core.models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False  
    verbose_name = 'Профиль'
    fields = ('avatar_preview', 'avatar', 'bio', 'location', 'birth_date')
    readonly_fields = ('avatar_preview',)

    def avatar_preview(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return format_html(
                '<img src="{}" width="50" height="50" '
                'style="border-radius: 50%;" />',
                obj.avatar.url
            )
        return '-'
    avatar_preview.short_description = 'Текущий аватар'


class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'avatar_preview', 'bio', 'location', 'birth_date']
    list_select_related = ['user', ]
    search_fields = ['user__username', 'user__email', 'location']
    list_filter = ['location', 'birth_date']
    raw_id_fields = ['user', ]
    readonly_fields = ['avatar_preview', ]
    fieldsets = (
        ('Основная информация', {'fields': ('user', 'bio')}),
        ('Дополнительно', {'fields': ('avatar_preview', 'avatar', 'location', 'birth_date'), 'classes': ('collapse', )})
    )

    def avatar_preview(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return format_html(
                '<img src="{}" width="50" height="50" '
                'style="border-radius: 50%;" />',
                obj.avatar.url
            )
        return '-'
    
    avatar_preview.short_description = 'Фото аватара'