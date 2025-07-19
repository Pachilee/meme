from django.contrib import admin
from .models import CustomUser, UserList, ListItem
from django.contrib.auth.admin import UserAdmin

# Register your models here.
admin.site.register(CustomUser, UserAdmin)

#display a list within a list 
class ListItemInline(admin.TabularInline):
    model = ListItem

@admin.register(UserList)
class UserListAdmin(admin.ModelAdmin):
    inlines = [ListItemInline]

@admin.register(ListItem)
class ListItemAdmin(admin.ModelAdmin):
    pass