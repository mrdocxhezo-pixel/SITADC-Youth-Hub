"""Template tags for the Accessibility Review module."""

from __future__ import annotations

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def accessibility_preferences(context):
    """Render accessibility preference classes for the html element."""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return mark_safe('')

    try:
        prefs = request.user.accessibility_preferences
    except Exception:
        return mark_safe('')

    classes = []

    # Font size
    font_size_map = {
        'SMALL': 'font-size-small',
        'MEDIUM': 'font-size-medium',
        'LARGE': 'font-size-large',
        'EXTRA_LARGE': 'font-size-xlarge',
    }
    if prefs.font_size in font_size_map:
        classes.append(font_size_map[prefs.font_size])
    elif prefs.font_size == 'CUSTOM' and prefs.custom_font_size_px:
        return mark_safe(f'style="font-size: {prefs.custom_font_size_px}px;"')

    # Colour theme
    theme_map = {
        'LIGHT': 'theme-light',
        'DARK': 'theme-dark',
        'HIGH_CONTRAST_LIGHT': 'theme-high-contrast-light',
        'HIGH_CONTRAST_DARK': 'theme-high-contrast-dark',
        'SEPIA': 'theme-sepia',
        'CUSTOM': 'theme-custom',
    }
    if prefs.colour_theme in theme_map:
        classes.append(theme_map[prefs.colour_theme])
    elif prefs.colour_theme == 'SYSTEM':
        # Will be handled by JS
        pass

    # Boolean preferences
    if prefs.high_contrast:
        classes.append('high-contrast')
    if prefs.reduced_motion:
        classes.append('reduced-motion')
    if prefs.enhanced_focus:
        classes.append('enhanced-focus')
    if prefs.keyboard_navigation_enhanced:
        classes.append('kbd-enhanced')
    if prefs.screen_reader_optimized:
        classes.append('sr-optimized')

    return mark_safe(' '.join(classes))


@register.simple_tag
def accessibility_contrast_ratio(fg: str, bg: str) -> float:
    """Calculate contrast ratio between two colors."""
    def luminance(hex_color: str) -> float:
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))
        def adjust(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = map(adjust, rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    l1 = luminance(fg)
    l2 = luminance(bg)
    ratio = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
    return round(ratio, 2)


@register.simple_tag
def accessibility_passes_aa(fg: str, bg: str, large_text: bool = False) -> bool:
    """Check if color combination passes WCAG AA."""
    ratio = accessibility_contrast_ratio(fg, bg)
    return ratio >= (3.0 if large_text else 4.5)


@register.simple_tag
def accessibility_passes_aaa(fg: str, bg: str, large_text: bool = False) -> bool:
    """Check if color combination passes WCAG AAA."""
    ratio = accessibility_contrast_ratio(fg, bg)
    return ratio >= (4.5 if large_text else 7.0)


@register.inclusion_tag('accessibility/includes/skip_link.html')
def skip_link(target_id: str = 'main-content', text: str | None = None):
    """Render a skip navigation link."""
    return {
        'target_id': target_id,
        'text': text or 'Skip to main content',
    }


@register.inclusion_tag('accessibility/includes/focus_trap.html')
def focus_trap(enabled: bool = True):
    """Add focus trap attributes to a container."""
    return {'enabled': enabled}


@register.filter
def accessibility_severity_badge(severity: str) -> str:
    """Return Bootstrap badge class for severity."""
    mapping = {
        'CRITICAL': 'bg-danger',
        'HIGH': 'bg-warning text-dark',
        'MEDIUM': 'bg-info',
        'LOW': 'bg-secondary',
        'INFO': 'bg-light text-dark',
    }
    return mapping.get(severity, 'bg-secondary')


@register.filter
def accessibility_status_badge(status: str) -> str:
    """Return Bootstrap badge class for status."""
    mapping = {
        'COMPLIANT': 'bg-success',
        'NON_COMPLIANT': 'bg-danger',
        'PARTIAL': 'bg-warning text-dark',
        'NOT_APPLICABLE': 'bg-secondary',
        'NOT_TESTED': 'bg-light text-dark',
        'OPEN': 'bg-danger',
        'IN_PROGRESS': 'bg-warning text-dark',
        'NEEDS_REVIEW': 'bg-info',
        'VERIFIED': 'bg-success',
        'WONT_FIX': 'bg-secondary',
        'FALSE_POSITIVE': 'bg-light text-dark',
        'DEFERRED': 'bg-dark',
    }
    return mapping.get(status, 'bg-secondary')


@register.filter
def wcag_level_badge(level: str) -> str:
    """Return Bootstrap badge class for WCAG level."""
    mapping = {
        'A': 'bg-secondary',
        'AA': 'bg-info',
        'AAA': 'bg-dark',
    }
    return mapping.get(level, 'bg-secondary')
