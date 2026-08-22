"""Constants for the Accessibility Review module (Phase 33)."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class AccessibilityStandard(models.TextChoices):
    """Supported accessibility standards."""

    WCAG_2_2_A = "WCAG_2_2_A", _("WCAG 2.2 Level A")
    WCAG_2_2_AA = "WCAG_2_2_AA", _("WCAG 2.2 Level AA")
    WCAG_2_2_AAA = "WCAG_2_2_AAA", _("WCAG 2.2 Level AAA")
    SECTION_508 = "SECTION_508", _("Section 508")
    EN_301_549 = "EN_301_549", _("EN 301 549")


class AccessibilityCategory(models.TextChoices):
    """Categories of accessibility requirements."""

    PERCEIVABLE = "PERCEIVABLE", _("Perceivable")
    OPERABLE = "OPERABLE", _("Operable")
    UNDERSTANDABLE = "UNDERSTANDABLE", _("Understandable")
    ROBUST = "ROBUST", _("Robust")


class WCAGPrinciple(models.TextChoices):
    """WCAG POUR principles."""

    PERCEIVABLE = "PERCEIVABLE", _("1. Perceivable")
    OPERABLE = "OPERABLE", _("2. Operable")
    UNDERSTANDABLE = "UNDERSTANDABLE", _("3. Understandable")
    ROBUST = "ROBUST", _("4. Robust")


class WCAGLevel(models.TextChoices):
    """WCAG conformance levels."""

    A = "A", _("Level A")
    AA = "AA", _("Level AA")
    AAA = "AAA", _("Level AAA")


class SeverityLevel(models.TextChoices):
    """Accessibility issue severity levels."""

    CRITICAL = "CRITICAL", _("Critical")
    HIGH = "HIGH", _("High")
    MEDIUM = "MEDIUM", _("Medium")
    LOW = "LOW", _("Low")
    INFO = "INFO", _("Informational")


class ComplianceStatus(models.TextChoices):
    """Compliance status of an accessibility check."""

    COMPLIANT = "COMPLIANT", _("Compliant")
    NON_COMPLIANT = "NON_COMPLIANT", _("Non-Compliant")
    PARTIAL = "PARTIAL", _("Partially Compliant")
    NOT_APPLICABLE = "NOT_APPLICABLE", _("Not Applicable")
    NOT_TESTED = "NOT_TESTED", _("Not Tested")


class AuditType(models.TextChoices):
    """Types of accessibility audits."""

    AUTOMATED = "AUTOMATED", _("Automated Scan")
    MANUAL = "MANUAL", _("Manual Review")
    KEYBOARD = "KEYBOARD", _("Keyboard Testing")
    SCREEN_READER = "SCREEN_READER", _("Screen Reader Testing")
    USER_TESTING = "USER_TESTING", _("User Testing")
    COLOUR_CONTRAST = "COLOUR_CONTRAST", _("Colour Contrast Analysis")
    REGRESSION = "REGRESSION", _("Regression Testing")


class AccessibilityIssueStatus(models.TextChoices):
    """Status of an accessibility issue."""

    OPEN = "OPEN", _("Open")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    NEEDS_REVIEW = "NEEDS_REVIEW", _("Needs Review")
    VERIFIED = "VERIFIED", _("Verified Fixed")
    WONT_FIX = "WONT_FIX", _("Won't Fix")
    FALSE_POSITIVE = "FALSE_POSITIVE", _("False Positive")
    DEFERRED = "DEFERRED", _("Deferred")


class AccessibilityPreferenceType(models.TextChoices):
    """User accessibility preference types."""

    FONT_SIZE = "FONT_SIZE", _("Font Size")
    COLOUR_THEME = "COLOUR_THEME", _("Colour Theme")
    HIGH_CONTRAST = "HIGH_CONTRAST", _("High Contrast Mode")
    REDUCED_MOTION = "REDUCED_MOTION", _("Reduced Motion")
    KEYBOARD_NAV = "KEYBOARD_NAV", _("Keyboard Navigation Enhancements")
    FOCUS_VISIBILITY = "FOCUS_VISIBILITY", _("Focus Visibility")
    SCREEN_READER = "SCREEN_READER", _("Screen Reader Optimizations")
    NOTIFICATION_TIMING = "NOTIFICATION_TIMING", _("Notification Timing")
    LANGUAGE = "LANGUAGE", _("Language")
    READING_ENHANCEMENTS = "READING_ENHANCEMENTS", _("Reading Enhancements")


class FontSizeOption(models.TextChoices):
    """Font size options for accessibility."""

    SMALL = "SMALL", _("Small (14px)")
    MEDIUM = "MEDIUM", _("Medium (16px)")
    LARGE = "LARGE", _("Large (18px)")
    EXTRA_LARGE = "EXTRA_LARGE", _("Extra Large (20px)")
    CUSTOM = "CUSTOM", _("Custom")


class ColourThemeOption(models.TextChoices):
    """Colour theme options for accessibility."""

    LIGHT = "LIGHT", _("Light")
    DARK = "DARK", _("Dark")
    HIGH_CONTRAST_LIGHT = "HIGH_CONTRAST_LIGHT", _("High Contrast Light")
    HIGH_CONTRAST_DARK = "HIGH_CONTRAST_DARK", _("High Contrast Dark")
    SEPIA = "SEPIA", _("Sepia")
    CUSTOM = "CUSTOM", _("Custom")


class NotificationTimingOption(models.TextChoices):
    """Notification timing preferences."""

    IMMEDIATE = "IMMEDIATE", _("Immediate")
    DELAYED_3S = "DELAYED_3S", _("3 Seconds")
    DELAYED_5S = "DELAYED_5S", _("5 Seconds")
    DELAYED_10S = "DELAYED_10S", _("10 Seconds")
    PERSISTENT = "PERSISTENT", _("Persistent Until Dismissed")


class AccessibilityRole(models.TextChoices):
    """ARIA roles for accessible components."""

    BUTTON = "button", _("Button")
    LINK = "link", _("Link")
    MENU = "menu", _("Menu")
    MENU_ITEM = "menuitem", _("Menu Item")
    TAB = "tab", _("Tab")
    TAB_PANEL = "tabpanel", _("Tab Panel")
    DIALOG = "dialog", _("Dialog")
    ALERT_DIALOG = "alertdialog", _("Alert Dialog")
    REGION = "region", _("Region")
    NAVIGATION = "navigation", _("Navigation")
    MAIN = "main", _("Main")
    COMPLEMENTARY = "complementary", _("Complementary")
    SEARCH = "search", _("Search")
    FORM = "form", _("Form")
    BANNER = "banner", _("Banner")
    CONTENTINFO = "contentinfo", _("Content Info")


DEFAULT_WCAG_VERSION = "2.2"
DEFAULT_TARGET_LEVEL = WCAGLevel.AA

CONTRAST_RATIOS = {
    "normal_text": 4.5,
    "large_text": 3.0,
    "ui_components": 3.0,
    "graphics": 3.0,
    "enhanced_normal": 7.0,
    "enhanced_large": 4.5,
}

FOCUS_INDICATOR_MIN_WIDTH = 2
FOCUS_INDICATOR_MIN_CONTRAST = 3.0

SKIP_LINK_TEXT = "Skip to main content"

ACCESSIBILITY_ACTION_PERMISSIONS: dict[str, str] = {
    "view": "accessibility.view",
    "create": "accessibility.create",
    "update": "accessibility.update",
    "delete": "accessibility.delete",
    "configure": "accessibility.configure",
    "audit": "accessibility.audit",
    "test": "accessibility.test",
    "report": "accessibility.report",
    "manage": "accessibility.manage",
    "approve": "accessibility.approve",
}

# Standalone permission constants for use in views
ACCESSIBILITY_VIEW = "accessibility.view"
ACCESSIBILITY_CREATE = "accessibility.create"
ACCESSIBILITY_UPDATE = "accessibility.update"
ACCESSIBILITY_DELETE = "accessibility.delete"
ACCESSIBILITY_CONFIGURE = "accessibility.configure"
ACCESSIBILITY_AUDIT = "accessibility.audit"
ACCESSIBILITY_TEST = "accessibility.test"
ACCESSIBILITY_REPORT = "accessibility.report"
ACCESSIBILITY_MANAGE = "accessibility.manage"
ACCESSIBILITY_APPROVE = "accessibility.approve"
