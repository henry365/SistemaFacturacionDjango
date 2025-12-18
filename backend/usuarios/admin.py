from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin personalizado para el modelo User"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'empresa', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('rol', 'is_active', 'is_staff', 'empresa', 'date_joined', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'empresa__nombre')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Información Adicional', {
            'fields': ('rol', 'telefono', 'empresa')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Información Adicional', {
            'fields': ('rol', 'telefono', 'empresa')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions')

# Mejorar admin de grupos
admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Admin mejorado para grupos/roles"""
    list_display = ('name', 'permisos_count', 'usuarios_count')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    
    def permisos_count(self, obj):
        return obj.permissions.count()
    permisos_count.short_description = 'Permisos'
    
    def usuarios_count(self, obj):
        return obj.user_set.count()
    usuarios_count.short_description = 'Usuarios'
