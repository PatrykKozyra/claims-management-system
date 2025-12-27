from django import template
from django.utils.html import format_html
from django.urls import reverse

register = template.Library()


@register.simple_tag
def user_link(user):
    """Render a clickable link to user's profile"""
    if not user:
        return format_html('<span class="text-muted">-</span>')

    url = reverse('user_profile', args=[user.id])
    display_name = user.get_full_name() or user.username

    return format_html(
        '<a href="{}" class="user-link">{}</a>',
        url,
        display_name
    )


@register.simple_tag
def user_badge(user):
    """Render a user badge with profile photo and name"""
    if not user:
        return format_html('<span class="text-muted">-</span>')

    url = reverse('user_profile', args=[user.id])
    display_name = user.get_full_name() or user.username

    if user.profile_photo:
        return format_html(
            '<a href="{}" class="user-link text-decoration-none">'
            '<img src="{}" class="profile-photo-small me-1" alt="{}">{}'
            '</a>',
            url,
            user.profile_photo.url,
            display_name,
            display_name
        )
    else:
        return format_html(
            '<a href="{}" class="user-link">'
            '<i class="bi bi-person-circle me-1"></i>{}'
            '</a>',
            url,
            display_name
        )
