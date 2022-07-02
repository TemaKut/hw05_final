from django.contrib import admin

from .models import Post, Group


class PostAdmin(admin.ModelAdmin):
    """Админская часть редактирования поста."""

    list_display = (
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text', )
    list_filter = ('pub_date', 'group')
    empty_value_display = '-пусто-'


admin.site.register(Group)
admin.site.register(Post, PostAdmin)
