"""Views for Communication and Media (Phase 30).

All views enforce server-side authorization via the ``communications.*``
permission catalogue and remain fail-closed: list/detail data flows through
the selectors in :mod:`apps.communications.selectors`, and mutating operations
set audit metadata and allocate reference numbers through the services.
"""

from __future__ import annotations

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.rbac.decorators import any_permission_required

from . import selectors, services
from .forms import (
    AnnouncementForm,
    BrandAssetForm,
    BrandGuidelineForm,
    CampaignActivityForm,
    CampaignForm,
    CommunicationCategoryForm,
    CommunicationForm,
    EventCommunicationForm,
    MediaAlbumForm,
    MediaAssetForm,
    NewsArticleForm,
    NewsletterForm,
    NewsletterSubscriberForm,
    PhotographForm,
    PressReleaseForm,
    PublicationForm,
    SocialMediaAccountForm,
    SocialMediaPostForm,
    VideoForm,
    WebsiteContentForm,
    WebsitePageForm,
)
from .models import (
    Announcement,
    BrandAsset,
    BrandGuideline,
    Campaign,
    CampaignActivity,
    Communication,
    CommunicationCategory,
    EventCommunication,
    MediaAlbum,
    MediaAsset,
    NewsArticle,
    Newsletter,
    NewsletterSubscriber,
    Photograph,
    PressRelease,
    Publication,
    SocialMediaAccount,
    SocialMediaPost,
    Video,
    WebsiteContent,
    WebsitePage,
)
from .permissions import (
    COMMUNICATIONS_APPROVE,
    COMMUNICATIONS_ARCHIVE,
    COMMUNICATIONS_CREATE,
    COMMUNICATIONS_DELETE,
    COMMUNICATIONS_MANAGE,
    COMMUNICATIONS_PUBLISH,
    COMMUNICATIONS_RESTORE,
    COMMUNICATIONS_UPDATE,
    COMMUNICATIONS_VIEW,
)

# Authorization decorators (AND of codes is not used; ANY is applied).
_any_view = any_permission_required(COMMUNICATIONS_VIEW, COMMUNICATIONS_MANAGE)
_any_manage = any_permission_required(
    COMMUNICATIONS_CREATE, COMMUNICATIONS_UPDATE, COMMUNICATIONS_MANAGE
)
_any_delete = any_permission_required(COMMUNICATIONS_DELETE, COMMUNICATIONS_MANAGE)
_any_approve = any_permission_required(COMMUNICATIONS_APPROVE, COMMUNICATIONS_MANAGE)
_any_publish = any_permission_required(COMMUNICATIONS_PUBLISH, COMMUNICATIONS_MANAGE)
_any_archive = any_permission_required(COMMUNICATIONS_ARCHIVE, COMMUNICATIONS_MANAGE)
_any_restore = any_permission_required(COMMUNICATIONS_RESTORE, COMMUNICATIONS_MANAGE)

# Models that carry a generated reference number must allocate one on create.
_RECORD_TYPES: dict[type, str] = {
    Communication: "communication",
    Announcement: "announcement",
    NewsArticle: "news",
    Newsletter: "newsletter",
    PressRelease: "press_release",
    Campaign: "campaign",
    WebsitePage: "website_page",
    EventCommunication: "event_communication",
    Publication: "publication",
}


def _allocate_reference_if_needed(request, obj) -> None:
    """Reserve a reference number for records that require one."""
    if not hasattr(obj, "reference_number") or obj.reference_number:
        return
    record_type = _RECORD_TYPES.get(type(obj), "communication")
    services.allocate_reference(request.user, obj, record_type)


# ---------------------------------------------------------------------------
# Generic CRUD helpers (fail-closed querysets from the selectors layer).
# ---------------------------------------------------------------------------


def object_list(
    request,
    template_name,
    context_name,
    queryset,
    search_fields=(),
    paginate_by=25,
    extra_context=None,
):
    """Generic list view fed by an already-authorized queryset."""
    search_query = request.GET.get("search", "")
    if search_query:
        q_objects = Q()
        for field in search_fields:
            q_objects |= Q(**{f"{field}__icontains": search_query})
        if q_objects:
            queryset = queryset.filter(q_objects)
    paginator = Paginator(queryset, paginate_by)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {
        context_name: page_obj,
        "search_query": search_query,
        "is_paginated": page_obj.has_other_pages(),
    }
    if extra_context:
        context.update(extra_context)
    return render(request, template_name, context)


def object_create(
    request,
    form_class,
    success_url,
    success_message,
    template_name="communications/object_form.html",
):
    """Generic create view for a communication record."""
    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            if hasattr(obj, "created_by"):
                obj.created_by = request.user
            if hasattr(obj, "updated_by"):
                obj.updated_by = request.user
            _allocate_reference_if_needed(request, obj)
            obj.save()
            form.save_m2m()
            messages.success(request, success_message)
            return redirect(success_url)
    else:
        form = form_class()
    context = {
        "form": form,
        "list_url": success_url,
        "model_name": form_class.Meta.model._meta.verbose_name,
    }
    return render(request, template_name, context)


def object_update(
    request,
    model,
    form_class,
    pk,
    success_url,
    success_message,
    template_name="communications/object_form.html",
):
    """Generic update view for a communication record."""
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            if hasattr(obj, "updated_by"):
                obj.updated_by = request.user
            obj.save()
            form.save_m2m()
            messages.success(request, success_message)
            return redirect(success_url)
    else:
        form = form_class(instance=obj)
    context = {
        "form": form,
        "object": obj,
        "list_url": success_url,
        "model_name": model._meta.verbose_name,
    }
    return render(request, template_name, context)


def object_delete(
    request,
    model,
    pk,
    success_url,
    success_message,
    template_name="communications/object_confirm_delete.html",
):
    """Generic delete view for a communication record."""
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, success_message)
        return redirect(success_url)
    context = {
        "object": obj,
        "list_url": success_url,
        "model_name": model._meta.verbose_name,
    }
    return render(request, template_name, context)


def object_detail(request, queryset, pk, template_name, context_name):
    """Generic detail view for a communication record."""
    obj = get_object_or_404(queryset, pk=pk)
    context = {context_name: obj}
    return render(request, template_name, context)


def record_action(request, model, pk, success_url, action, action_past):
    """Apply a service-level status transition to a communication record."""
    obj = get_object_or_404(model, pk=pk)
    service = services.CommunicationService(user=request.user)
    if request.method == "POST":
        try:
            getattr(service, action)(request.user, obj)
            messages.success(request, f"{model._meta.verbose_name} {action_past}.")
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect(success_url)
    context = {
        "object": obj,
        "action": action,
        "action_label": action.replace("_", " ").title(),
        "list_url": success_url,
        "model_name": model._meta.verbose_name,
    }
    return render(request, "communications/object_confirm_action.html", context)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@_any_view
def communications_dashboard(request):
    """Comprehensive communications overview."""
    analytics = services.get_dashboard_analytics(request.user)
    recent = selectors.get_recent_communications(request.user)
    upcoming_events = selectors.get_upcoming_event_communications(request.user)
    context = {
        "analytics": analytics,
        "recent_communications": recent,
        "upcoming_events": upcoming_events,
        "page_title": "Communications Dashboard",
    }
    return render(request, "communications/dashboard.html", context)


# ---------------------------------------------------------------------------
# CommunicationCategory
# ---------------------------------------------------------------------------


@_any_view
def communication_category_list(request):
    return object_list(
        request,
        "communications/category_list.html",
        "categories",
        selectors.get_accessible_communication_categories(request.user),
        search_fields=("name", "code"),
    )


@_any_view
def communication_category_create(request):
    return object_create(
        request,
        CommunicationCategoryForm,
        reverse("communications:communication_category_list"),
        "Communication category created.",
    )


@_any_manage
def communication_category_update(request, pk):
    return object_update(
        request,
        CommunicationCategory,
        CommunicationCategoryForm,
        pk,
        reverse("communications:communication_category_list"),
        "Communication category updated.",
    )


@_any_delete
def communication_category_delete(request, pk):
    return object_delete(
        request,
        CommunicationCategory,
        pk,
        reverse("communications:communication_category_list"),
        "Communication category deleted.",
    )


# ---------------------------------------------------------------------------
# Communication
# ---------------------------------------------------------------------------


@_any_view
def communication_list(request):
    return object_list(
        request,
        "communications/communication_list.html",
        "communications",
        selectors.get_accessible_communications(request.user),
        search_fields=("title", "summary", "reference_number"),
        extra_context={
            "status_choices": Communication._meta.get_field("status").choices,
        },
    )


@_any_view
def communication_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_communications(request.user),
        pk,
        "communications/communication_detail.html",
        "communication",
    )


@_any_manage
def communication_create(request):
    return object_create(
        request,
        CommunicationForm,
        reverse("communications:communication_list"),
        "Communication created.",
    )


@_any_manage
def communication_update(request, pk):
    return object_update(
        request,
        Communication,
        CommunicationForm,
        pk,
        reverse("communications:communication_list"),
        "Communication updated.",
    )


@_any_delete
def communication_delete(request, pk):
    return object_delete(
        request,
        Communication,
        pk,
        reverse("communications:communication_list"),
        "Communication deleted.",
    )


@_any_approve
def communication_approve(request, pk):
    return record_action(
        request,
        Communication,
        pk,
        reverse("communications:communication_list"),
        "approve",
        "approved",
    )


@_any_publish
def communication_publish(request, pk):
    return record_action(
        request,
        Communication,
        pk,
        reverse("communications:communication_list"),
        "publish",
        "published",
    )


@_any_archive
def communication_archive(request, pk):
    return record_action(
        request,
        Communication,
        pk,
        reverse("communications:communication_list"),
        "archive",
        "archived",
    )


@_any_restore
def communication_restore(request, pk):
    return record_action(
        request,
        Communication,
        pk,
        reverse("communications:communication_list"),
        "restore",
        "restored",
    )


# ---------------------------------------------------------------------------
# Announcement
# ---------------------------------------------------------------------------


@_any_view
def announcement_list(request):
    return object_list(
        request,
        "communications/announcement_list.html",
        "announcements",
        selectors.get_accessible_announcements(request.user),
        search_fields=("title", "summary", "reference_number"),
    )


@_any_view
def announcement_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_announcements(request.user),
        pk,
        "communications/announcement_detail.html",
        "announcement",
    )


@_any_manage
def announcement_create(request):
    return object_create(
        request,
        AnnouncementForm,
        reverse("communications:announcement_list"),
        "Announcement created.",
    )


@_any_manage
def announcement_update(request, pk):
    return object_update(
        request,
        Announcement,
        AnnouncementForm,
        pk,
        reverse("communications:announcement_list"),
        "Announcement updated.",
    )


@_any_delete
def announcement_delete(request, pk):
    return object_delete(
        request,
        Announcement,
        pk,
        reverse("communications:announcement_list"),
        "Announcement deleted.",
    )


@_any_publish
def announcement_publish(request, pk):
    return record_action(
        request,
        Announcement,
        pk,
        reverse("communications:announcement_list"),
        "publish",
        "published",
    )


# ---------------------------------------------------------------------------
# NewsArticle
# ---------------------------------------------------------------------------


@_any_view
def news_article_list(request):
    return object_list(
        request,
        "communications/news_article_list.html",
        "news_articles",
        selectors.get_accessible_news_articles(request.user),
        search_fields=("title", "summary", "reference_number"),
    )


@_any_view
def news_article_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_news_articles(request.user),
        pk,
        "communications/news_article_detail.html",
        "news_article",
    )


@_any_manage
def news_article_create(request):
    return object_create(
        request,
        NewsArticleForm,
        reverse("communications:news_article_list"),
        "News article created.",
    )


@_any_manage
def news_article_update(request, pk):
    return object_update(
        request,
        NewsArticle,
        NewsArticleForm,
        pk,
        reverse("communications:news_article_list"),
        "News article updated.",
    )


@_any_delete
def news_article_delete(request, pk):
    return object_delete(
        request,
        NewsArticle,
        pk,
        reverse("communications:news_article_list"),
        "News article deleted.",
    )


@_any_publish
def news_article_publish(request, pk):
    return record_action(
        request,
        NewsArticle,
        pk,
        reverse("communications:news_article_list"),
        "publish",
        "published",
    )


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------


@_any_view
def newsletter_list(request):
    return object_list(
        request,
        "communications/newsletter_list.html",
        "newsletters",
        selectors.get_accessible_newsletters(request.user),
        search_fields=("title", "subject", "reference_number"),
    )


@_any_view
def newsletter_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_newsletters(request.user),
        pk,
        "communications/newsletter_detail.html",
        "newsletter",
    )


@_any_manage
def newsletter_create(request):
    return object_create(
        request,
        NewsletterForm,
        reverse("communications:newsletter_list"),
        "Newsletter created.",
    )


@_any_manage
def newsletter_update(request, pk):
    return object_update(
        request,
        Newsletter,
        NewsletterForm,
        pk,
        reverse("communications:newsletter_list"),
        "Newsletter updated.",
    )


@_any_delete
def newsletter_delete(request, pk):
    return object_delete(
        request,
        Newsletter,
        pk,
        reverse("communications:newsletter_list"),
        "Newsletter deleted.",
    )


@_any_publish
def newsletter_distribute(request, pk):
    obj = get_object_or_404(Newsletter, pk=pk)
    if request.method == "POST":
        service = services.NewsletterService(user=request.user)
        try:
            service.distribute(request.user, obj)
            messages.success(request, "Newsletter distributed.")
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect(reverse("communications:newsletter_list"))
    context = {
        "object": obj,
        "action": "distribute",
        "action_label": "Distribute",
        "list_url": reverse("communications:newsletter_list"),
        "model_name": "Newsletter",
    }
    return render(request, "communications/object_confirm_action.html", context)


# ---------------------------------------------------------------------------
# NewsletterSubscriber
# ---------------------------------------------------------------------------


@_any_view
def newsletter_subscriber_list(request):
    return object_list(
        request,
        "communications/newsletter_subscriber_list.html",
        "subscribers",
        selectors.get_accessible_newsletter_subscribers(request.user),
        search_fields=("email", "first_name", "last_name"),
    )


@_any_manage
def newsletter_subscriber_create(request):
    return object_create(
        request,
        NewsletterSubscriberForm,
        reverse("communications:newsletter_subscriber_list"),
        "Newsletter subscriber created.",
    )


@_any_manage
def newsletter_subscriber_update(request, pk):
    return object_update(
        request,
        NewsletterSubscriber,
        NewsletterSubscriberForm,
        pk,
        reverse("communications:newsletter_subscriber_list"),
        "Newsletter subscriber updated.",
    )


@_any_delete
def newsletter_subscriber_delete(request, pk):
    return object_delete(
        request,
        NewsletterSubscriber,
        pk,
        reverse("communications:newsletter_subscriber_list"),
        "Newsletter subscriber deleted.",
    )


# ---------------------------------------------------------------------------
# PressRelease
# ---------------------------------------------------------------------------


@_any_view
def press_release_list(request):
    return object_list(
        request,
        "communications/press_release_list.html",
        "press_releases",
        selectors.get_accessible_press_releases(request.user),
        search_fields=("title", "summary", "reference_number"),
    )


@_any_view
def press_release_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_press_releases(request.user),
        pk,
        "communications/press_release_detail.html",
        "press_release",
    )


@_any_manage
def press_release_create(request):
    return object_create(
        request,
        PressReleaseForm,
        reverse("communications:press_release_list"),
        "Press release created.",
    )


@_any_manage
def press_release_update(request, pk):
    return object_update(
        request,
        PressRelease,
        PressReleaseForm,
        pk,
        reverse("communications:press_release_list"),
        "Press release updated.",
    )


@_any_delete
def press_release_delete(request, pk):
    return object_delete(
        request,
        PressRelease,
        pk,
        reverse("communications:press_release_list"),
        "Press release deleted.",
    )


@_any_publish
def press_release_publish(request, pk):
    return record_action(
        request,
        PressRelease,
        pk,
        reverse("communications:press_release_list"),
        "publish",
        "published",
    )


# ---------------------------------------------------------------------------
# SocialMedia
# ---------------------------------------------------------------------------


@_any_view
def social_media_account_list(request):
    return object_list(
        request,
        "communications/social_media_account_list.html",
        "accounts",
        selectors.get_accessible_social_media_accounts(request.user),
        search_fields=("account_name", "handle", "platform"),
    )


@_any_manage
def social_media_account_create(request):
    return object_create(
        request,
        SocialMediaAccountForm,
        reverse("communications:social_media_account_list"),
        "Social media account created.",
    )


@_any_manage
def social_media_account_update(request, pk):
    return object_update(
        request,
        SocialMediaAccount,
        SocialMediaAccountForm,
        pk,
        reverse("communications:social_media_account_list"),
        "Social media account updated.",
    )


@_any_delete
def social_media_account_delete(request, pk):
    return object_delete(
        request,
        SocialMediaAccount,
        pk,
        reverse("communications:social_media_account_list"),
        "Social media account deleted.",
    )


@_any_view
def social_media_post_list(request):
    return object_list(
        request,
        "communications/social_media_post_list.html",
        "posts",
        selectors.get_accessible_social_media_posts(request.user),
        search_fields=("content",),
        extra_context={
            "status_choices": SocialMediaPost._meta.get_field("status").choices,
        },
    )


@_any_manage
def social_media_post_create(request):
    return object_create(
        request,
        SocialMediaPostForm,
        reverse("communications:social_media_post_list"),
        "Social media post created.",
    )


@_any_manage
def social_media_post_update(request, pk):
    return object_update(
        request,
        SocialMediaPost,
        SocialMediaPostForm,
        pk,
        reverse("communications:social_media_post_list"),
        "Social media post updated.",
    )


@_any_delete
def social_media_post_delete(request, pk):
    return object_delete(
        request,
        SocialMediaPost,
        pk,
        reverse("communications:social_media_post_list"),
        "Social media post deleted.",
    )


@_any_publish
def social_media_post_publish(request, pk):
    return record_action(
        request,
        SocialMediaPost,
        pk,
        reverse("communications:social_media_post_list"),
        "publish",
        "published",
    )


# ---------------------------------------------------------------------------
# Campaign
# ---------------------------------------------------------------------------


@_any_view
def campaign_list(request):
    return object_list(
        request,
        "communications/campaign_list.html",
        "campaigns",
        selectors.get_accessible_campaigns(request.user),
        search_fields=("title", "summary", "reference_number"),
    )


@_any_view
def campaign_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_campaigns(request.user),
        pk,
        "communications/campaign_detail.html",
        "campaign",
    )


@_any_manage
def campaign_create(request):
    return object_create(
        request,
        CampaignForm,
        reverse("communications:campaign_list"),
        "Campaign created.",
    )


@_any_manage
def campaign_update(request, pk):
    return object_update(
        request,
        Campaign,
        CampaignForm,
        pk,
        reverse("communications:campaign_list"),
        "Campaign updated.",
    )


@_any_delete
def campaign_delete(request, pk):
    return object_delete(
        request,
        Campaign,
        pk,
        reverse("communications:campaign_list"),
        "Campaign deleted.",
    )


@_any_publish
def campaign_launch(request, pk):
    obj = get_object_or_404(Campaign, pk=pk)
    if request.method == "POST":
        service = services.CampaignService(user=request.user)
        try:
            service.launch(request.user, obj)
            messages.success(request, "Campaign launched.")
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect(reverse("communications:campaign_list"))
    context = {
        "object": obj,
        "action": "launch",
        "action_label": "Launch Campaign",
        "list_url": reverse("communications:campaign_list"),
        "model_name": "Campaign",
    }
    return render(request, "communications/object_confirm_action.html", context)


# ---------------------------------------------------------------------------
# CampaignActivity
# ---------------------------------------------------------------------------


@_any_view
def campaign_activity_list(request):
    return object_list(
        request,
        "communications/campaign_activity_list.html",
        "activities",
        selectors.get_accessible_campaign_activities(request.user),
        search_fields=("title", "activity_type"),
    )


@_any_manage
def campaign_activity_create(request):
    return object_create(
        request,
        CampaignActivityForm,
        reverse("communications:campaign_activity_list"),
        "Campaign activity created.",
    )


@_any_manage
def campaign_activity_update(request, pk):
    return object_update(
        request,
        CampaignActivity,
        CampaignActivityForm,
        pk,
        reverse("communications:campaign_activity_list"),
        "Campaign activity updated.",
    )


@_any_delete
def campaign_activity_delete(request, pk):
    return object_delete(
        request,
        CampaignActivity,
        pk,
        reverse("communications:campaign_activity_list"),
        "Campaign activity deleted.",
    )


# ---------------------------------------------------------------------------
# MediaAlbum / MediaAsset
# ---------------------------------------------------------------------------


@_any_view
def media_album_list(request):
    return object_list(
        request,
        "communications/media_album_list.html",
        "albums",
        selectors.get_accessible_media_albums(request.user),
        search_fields=("title",),
    )


@_any_manage
def media_album_create(request):
    return object_create(
        request,
        MediaAlbumForm,
        reverse("communications:media_album_list"),
        "Media album created.",
    )


@_any_manage
def media_album_update(request, pk):
    return object_update(
        request,
        MediaAlbum,
        MediaAlbumForm,
        pk,
        reverse("communications:media_album_list"),
        "Media album updated.",
    )


@_any_delete
def media_album_delete(request, pk):
    return object_delete(
        request,
        MediaAlbum,
        pk,
        reverse("communications:media_album_list"),
        "Media album deleted.",
    )


@_any_view
def media_asset_list(request):
    return object_list(
        request,
        "communications/media_asset_list.html",
        "media_assets",
        selectors.get_accessible_media_assets(request.user),
        search_fields=("title", "description", "tags"),
        extra_context={
            "status_choices": MediaAsset._meta.get_field("status").choices,
        },
    )


@_any_view
def media_asset_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_media_assets(request.user),
        pk,
        "communications/media_asset_detail.html",
        "media_asset",
    )


@_any_manage
def media_asset_create(request):
    return object_create(
        request,
        MediaAssetForm,
        reverse("communications:media_asset_list"),
        "Media asset uploaded.",
    )


@_any_manage
def media_asset_update(request, pk):
    return object_update(
        request,
        MediaAsset,
        MediaAssetForm,
        pk,
        reverse("communications:media_asset_list"),
        "Media asset updated.",
    )


@_any_delete
def media_asset_delete(request, pk):
    return object_delete(
        request,
        MediaAsset,
        pk,
        reverse("communications:media_asset_list"),
        "Media asset deleted.",
    )


@_any_publish
def media_asset_publish(request, pk):
    obj = get_object_or_404(MediaAsset, pk=pk)
    if request.method == "POST":
        service = services.MediaAssetService(user=request.user)
        try:
            service.publish(request.user, obj)
            messages.success(request, "Media asset published.")
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect(reverse("communications:media_asset_list"))
    context = {
        "object": obj,
        "action": "publish",
        "action_label": "Publish",
        "list_url": reverse("communications:media_asset_list"),
        "model_name": "Media Asset",
    }
    return render(request, "communications/object_confirm_action.html", context)


# ---------------------------------------------------------------------------
# Photograph / Video
# ---------------------------------------------------------------------------


@_any_view
def photograph_list(request):
    return object_list(
        request,
        "communications/photograph_list.html",
        "photographs",
        selectors.get_accessible_photographs(request.user),
        search_fields=("title", "caption"),
    )


@_any_manage
def photograph_create(request):
    return object_create(
        request,
        PhotographForm,
        reverse("communications:photograph_list"),
        "Photograph added.",
    )


@_any_manage
def photograph_update(request, pk):
    return object_update(
        request,
        Photograph,
        PhotographForm,
        pk,
        reverse("communications:photograph_list"),
        "Photograph updated.",
    )


@_any_delete
def photograph_delete(request, pk):
    return object_delete(
        request,
        Photograph,
        pk,
        reverse("communications:photograph_list"),
        "Photograph deleted.",
    )


@_any_view
def video_list(request):
    return object_list(
        request,
        "communications/video_list.html",
        "videos",
        selectors.get_accessible_videos(request.user),
        search_fields=("title", "description"),
    )


@_any_manage
def video_create(request):
    return object_create(
        request,
        VideoForm,
        reverse("communications:video_list"),
        "Video added.",
    )


@_any_manage
def video_update(request, pk):
    return object_update(
        request,
        Video,
        VideoForm,
        pk,
        reverse("communications:video_list"),
        "Video updated.",
    )


@_any_delete
def video_delete(request, pk):
    return object_delete(
        request,
        Video,
        pk,
        reverse("communications:video_list"),
        "Video deleted.",
    )


# ---------------------------------------------------------------------------
# Publication
# ---------------------------------------------------------------------------


@_any_view
def publication_list(request):
    return object_list(
        request,
        "communications/publication_list.html",
        "publications",
        selectors.get_accessible_publications(request.user),
        search_fields=("title", "summary", "reference_number"),
    )


@_any_view
def publication_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_publications(request.user),
        pk,
        "communications/publication_detail.html",
        "publication",
    )


@_any_manage
def publication_create(request):
    return object_create(
        request,
        PublicationForm,
        reverse("communications:publication_list"),
        "Publication created.",
    )


@_any_manage
def publication_update(request, pk):
    return object_update(
        request,
        Publication,
        PublicationForm,
        pk,
        reverse("communications:publication_list"),
        "Publication updated.",
    )


@_any_delete
def publication_delete(request, pk):
    return object_delete(
        request,
        Publication,
        pk,
        reverse("communications:publication_list"),
        "Publication deleted.",
    )


@_any_publish
def publication_publish(request, pk):
    return record_action(
        request,
        Publication,
        pk,
        reverse("communications:publication_list"),
        "publish",
        "published",
    )


# ---------------------------------------------------------------------------
# BrandAsset / BrandGuideline
# ---------------------------------------------------------------------------


@_any_view
def brand_asset_list(request):
    return object_list(
        request,
        "communications/brand_asset_list.html",
        "brand_assets",
        selectors.get_accessible_brand_assets(request.user),
        search_fields=("title", "description"),
    )


@_any_manage
def brand_asset_create(request):
    return object_create(
        request,
        BrandAssetForm,
        reverse("communications:brand_asset_list"),
        "Brand asset created.",
    )


@_any_manage
def brand_asset_update(request, pk):
    return object_update(
        request,
        BrandAsset,
        BrandAssetForm,
        pk,
        reverse("communications:brand_asset_list"),
        "Brand asset updated.",
    )


@_any_delete
def brand_asset_delete(request, pk):
    return object_delete(
        request,
        BrandAsset,
        pk,
        reverse("communications:brand_asset_list"),
        "Brand asset deleted.",
    )


@_any_view
def brand_guideline_list(request):
    from .models import BrandGuideline

    return object_list(
        request,
        "communications/brand_guideline_list.html",
        "guidelines",
        BrandGuideline.objects.all(),
        search_fields=("title",),
    )


@_any_manage
def brand_guideline_create(request):
    return object_create(
        request,
        BrandGuidelineForm,
        reverse("communications:brand_guideline_list"),
        "Brand guideline created.",
    )


@_any_manage
def brand_guideline_update(request, pk):
    return object_update(
        request,
        BrandGuideline,
        BrandGuidelineForm,
        pk,
        reverse("communications:brand_guideline_list"),
        "Brand guideline updated.",
    )


@_any_delete
def brand_guideline_delete(request, pk):
    return object_delete(
        request,
        BrandGuideline,
        pk,
        reverse("communications:brand_guideline_list"),
        "Brand guideline deleted.",
    )


# ---------------------------------------------------------------------------
# WebsitePage / WebsiteContent
# ---------------------------------------------------------------------------


@_any_view
def website_page_list(request):
    return object_list(
        request,
        "communications/website_page_list.html",
        "pages",
        selectors.get_accessible_website_pages(request.user),
        search_fields=("title", "slug", "reference_number"),
    )


@_any_view
def website_page_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_website_pages(request.user),
        pk,
        "communications/website_page_detail.html",
        "page",
    )


@_any_manage
def website_page_create(request):
    return object_create(
        request,
        WebsitePageForm,
        reverse("communications:website_page_list"),
        "Website page created.",
    )


@_any_manage
def website_page_update(request, pk):
    return object_update(
        request,
        WebsitePage,
        WebsitePageForm,
        pk,
        reverse("communications:website_page_list"),
        "Website page updated.",
    )


@_any_delete
def website_page_delete(request, pk):
    return object_delete(
        request,
        WebsitePage,
        pk,
        reverse("communications:website_page_list"),
        "Website page deleted.",
    )


@_any_publish
def website_page_publish(request, pk):
    return record_action(
        request,
        WebsitePage,
        pk,
        reverse("communications:website_page_list"),
        "publish",
        "published",
    )


@_any_view
def website_content_list(request):
    return object_list(
        request,
        "communications/website_content_list.html",
        "contents",
        selectors.get_accessible_website_content(request.user),
        search_fields=("section_key", "section_title"),
    )


@_any_manage
def website_content_create(request):
    return object_create(
        request,
        WebsiteContentForm,
        reverse("communications:website_content_list"),
        "Website content created.",
    )


@_any_manage
def website_content_update(request, pk):
    return object_update(
        request,
        WebsiteContent,
        WebsiteContentForm,
        pk,
        reverse("communications:website_content_list"),
        "Website content updated.",
    )


@_any_delete
def website_content_delete(request, pk):
    return object_delete(
        request,
        WebsiteContent,
        pk,
        reverse("communications:website_content_list"),
        "Website content deleted.",
    )


# ---------------------------------------------------------------------------
# EventCommunication
# ---------------------------------------------------------------------------


@_any_view
def event_communication_list(request):
    return object_list(
        request,
        "communications/event_communication_list.html",
        "event_communications",
        selectors.get_accessible_event_communications(request.user),
        search_fields=("title", "event_name", "reference_number"),
    )


@_any_view
def event_communication_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_event_communications(request.user),
        pk,
        "communications/event_communication_detail.html",
        "event_communication",
    )


@_any_manage
def event_communication_create(request):
    return object_create(
        request,
        EventCommunicationForm,
        reverse("communications:event_communication_list"),
        "Event communication created.",
    )


@_any_manage
def event_communication_update(request, pk):
    return object_update(
        request,
        EventCommunication,
        EventCommunicationForm,
        pk,
        reverse("communications:event_communication_list"),
        "Event communication updated.",
    )


@_any_delete
def event_communication_delete(request, pk):
    return object_delete(
        request,
        EventCommunication,
        pk,
        reverse("communications:event_communication_list"),
        "Event communication deleted.",
    )


@_any_publish
def event_communication_publish(request, pk):
    return record_action(
        request,
        EventCommunication,
        pk,
        reverse("communications:event_communication_list"),
        "publish",
        "published",
    )


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


@_any_view
def timeline_list(request):
    return object_list(
        request,
        "communications/timeline_list.html",
        "timeline_events",
        selectors.get_accessible_timeline(request.user),
        search_fields=("description", "reference_number"),
    )
