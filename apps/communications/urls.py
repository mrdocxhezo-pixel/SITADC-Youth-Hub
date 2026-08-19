"""URL configuration for Communication and Media (Phase 30)."""

from django.urls import path

from . import views

app_name = "communications"

urlpatterns = [
    # Dashboard
    path("", views.communications_dashboard, name="communications_dashboard"),
    # CommunicationCategory URLs
    path(
        "categories/",
        views.communication_category_list,
        name="communication_category_list",
    ),
    path(
        "categories/create/",
        views.communication_category_create,
        name="communication_category_create",
    ),
    path(
        "categories/<uuid:pk>/update/",
        views.communication_category_update,
        name="communication_category_update",
    ),
    path(
        "categories/<uuid:pk>/delete/",
        views.communication_category_delete,
        name="communication_category_delete",
    ),
    # Communication URLs
    path("communications/", views.communication_list, name="communication_list"),
    path(
        "communications/create/",
        views.communication_create,
        name="communication_create",
    ),
    path(
        "communications/<uuid:pk>/update/",
        views.communication_update,
        name="communication_update",
    ),
    path(
        "communications/<uuid:pk>/delete/",
        views.communication_delete,
        name="communication_delete",
    ),
    path(
        "communications/<uuid:pk>/approve/",
        views.communication_approve,
        name="communication_approve",
    ),
    path(
        "communications/<uuid:pk>/publish/",
        views.communication_publish,
        name="communication_publish",
    ),
    path(
        "communications/<uuid:pk>/archive/",
        views.communication_archive,
        name="communication_archive",
    ),
    path(
        "communications/<uuid:pk>/restore/",
        views.communication_restore,
        name="communication_restore",
    ),
    path(
        "communications/<uuid:pk>/",
        views.communication_detail,
        name="communication_detail",
    ),
    # Announcement URLs
    path("announcements/", views.announcement_list, name="announcement_list"),
    path(
        "announcements/create/",
        views.announcement_create,
        name="announcement_create",
    ),
    path(
        "announcements/<uuid:pk>/update/",
        views.announcement_update,
        name="announcement_update",
    ),
    path(
        "announcements/<uuid:pk>/delete/",
        views.announcement_delete,
        name="announcement_delete",
    ),
    path(
        "announcements/<uuid:pk>/publish/",
        views.announcement_publish,
        name="announcement_publish",
    ),
    path(
        "announcements/<uuid:pk>/",
        views.announcement_detail,
        name="announcement_detail",
    ),
    # NewsArticle URLs
    path("news/", views.news_article_list, name="news_article_list"),
    path("news/create/", views.news_article_create, name="news_article_create"),
    path(
        "news/<uuid:pk>/update/",
        views.news_article_update,
        name="news_article_update",
    ),
    path(
        "news/<uuid:pk>/delete/",
        views.news_article_delete,
        name="news_article_delete",
    ),
    path(
        "news/<uuid:pk>/publish/",
        views.news_article_publish,
        name="news_article_publish",
    ),
    path(
        "news/<uuid:pk>/",
        views.news_article_detail,
        name="news_article_detail",
    ),
    # Newsletter URLs
    path("newsletters/", views.newsletter_list, name="newsletter_list"),
    path(
        "newsletters/create/",
        views.newsletter_create,
        name="newsletter_create",
    ),
    path(
        "newsletters/<uuid:pk>/update/",
        views.newsletter_update,
        name="newsletter_update",
    ),
    path(
        "newsletters/<uuid:pk>/delete/",
        views.newsletter_delete,
        name="newsletter_delete",
    ),
    path(
        "newsletters/<uuid:pk>/distribute/",
        views.newsletter_distribute,
        name="newsletter_distribute",
    ),
    path(
        "newsletters/<uuid:pk>/",
        views.newsletter_detail,
        name="newsletter_detail",
    ),
    # NewsletterSubscriber URLs
    path(
        "newsletter-subscribers/",
        views.newsletter_subscriber_list,
        name="newsletter_subscriber_list",
    ),
    path(
        "newsletter-subscribers/create/",
        views.newsletter_subscriber_create,
        name="newsletter_subscriber_create",
    ),
    path(
        "newsletter-subscribers/<uuid:pk>/update/",
        views.newsletter_subscriber_update,
        name="newsletter_subscriber_update",
    ),
    path(
        "newsletter-subscribers/<uuid:pk>/delete/",
        views.newsletter_subscriber_delete,
        name="newsletter_subscriber_delete",
    ),
    # PressRelease URLs
    path(
        "press-releases/",
        views.press_release_list,
        name="press_release_list",
    ),
    path(
        "press-releases/create/",
        views.press_release_create,
        name="press_release_create",
    ),
    path(
        "press-releases/<uuid:pk>/update/",
        views.press_release_update,
        name="press_release_update",
    ),
    path(
        "press-releases/<uuid:pk>/delete/",
        views.press_release_delete,
        name="press_release_delete",
    ),
    path(
        "press-releases/<uuid:pk>/publish/",
        views.press_release_publish,
        name="press_release_publish",
    ),
    path(
        "press-releases/<uuid:pk>/",
        views.press_release_detail,
        name="press_release_detail",
    ),
    # SocialMedia URLs
    path(
        "social-accounts/",
        views.social_media_account_list,
        name="social_media_account_list",
    ),
    path(
        "social-accounts/create/",
        views.social_media_account_create,
        name="social_media_account_create",
    ),
    path(
        "social-accounts/<uuid:pk>/update/",
        views.social_media_account_update,
        name="social_media_account_update",
    ),
    path(
        "social-accounts/<uuid:pk>/delete/",
        views.social_media_account_delete,
        name="social_media_account_delete",
    ),
    path(
        "social-posts/",
        views.social_media_post_list,
        name="social_media_post_list",
    ),
    path(
        "social-posts/create/",
        views.social_media_post_create,
        name="social_media_post_create",
    ),
    path(
        "social-posts/<uuid:pk>/update/",
        views.social_media_post_update,
        name="social_media_post_update",
    ),
    path(
        "social-posts/<uuid:pk>/delete/",
        views.social_media_post_delete,
        name="social_media_post_delete",
    ),
    path(
        "social-posts/<uuid:pk>/publish/",
        views.social_media_post_publish,
        name="social_media_post_publish",
    ),
    # Campaign URLs
    path("campaigns/", views.campaign_list, name="campaign_list"),
    path("campaigns/create/", views.campaign_create, name="campaign_create"),
    path(
        "campaigns/<uuid:pk>/update/",
        views.campaign_update,
        name="campaign_update",
    ),
    path(
        "campaigns/<uuid:pk>/delete/",
        views.campaign_delete,
        name="campaign_delete",
    ),
    path(
        "campaigns/<uuid:pk>/launch/",
        views.campaign_launch,
        name="campaign_launch",
    ),
    path("campaigns/<uuid:pk>/", views.campaign_detail, name="campaign_detail"),
    # CampaignActivity URLs
    path(
        "campaign-activities/",
        views.campaign_activity_list,
        name="campaign_activity_list",
    ),
    path(
        "campaign-activities/create/",
        views.campaign_activity_create,
        name="campaign_activity_create",
    ),
    path(
        "campaign-activities/<uuid:pk>/update/",
        views.campaign_activity_update,
        name="campaign_activity_update",
    ),
    path(
        "campaign-activities/<uuid:pk>/delete/",
        views.campaign_activity_delete,
        name="campaign_activity_delete",
    ),
    # MediaAlbum URLs
    path("media-albums/", views.media_album_list, name="media_album_list"),
    path(
        "media-albums/create/",
        views.media_album_create,
        name="media_album_create",
    ),
    path(
        "media-albums/<uuid:pk>/update/",
        views.media_album_update,
        name="media_album_update",
    ),
    path(
        "media-albums/<uuid:pk>/delete/",
        views.media_album_delete,
        name="media_album_delete",
    ),
    # MediaAsset URLs
    path("media/", views.media_asset_list, name="media_asset_list"),
    path("media/create/", views.media_asset_create, name="media_asset_create"),
    path(
        "media/<uuid:pk>/update/",
        views.media_asset_update,
        name="media_asset_update",
    ),
    path(
        "media/<uuid:pk>/delete/",
        views.media_asset_delete,
        name="media_asset_delete",
    ),
    path(
        "media/<uuid:pk>/publish/",
        views.media_asset_publish,
        name="media_asset_publish",
    ),
    path("media/<uuid:pk>/", views.media_asset_detail, name="media_asset_detail"),
    # Photograph URLs
    path("photographs/", views.photograph_list, name="photograph_list"),
    path(
        "photographs/create/",
        views.photograph_create,
        name="photograph_create",
    ),
    path(
        "photographs/<uuid:pk>/update/",
        views.photograph_update,
        name="photograph_update",
    ),
    path(
        "photographs/<uuid:pk>/delete/",
        views.photograph_delete,
        name="photograph_delete",
    ),
    # Video URLs
    path("videos/", views.video_list, name="video_list"),
    path("videos/create/", views.video_create, name="video_create"),
    path("videos/<uuid:pk>/update/", views.video_update, name="video_update"),
    path("videos/<uuid:pk>/delete/", views.video_delete, name="video_delete"),
    # Publication URLs
    path("publications/", views.publication_list, name="publication_list"),
    path(
        "publications/create/",
        views.publication_create,
        name="publication_create",
    ),
    path(
        "publications/<uuid:pk>/update/",
        views.publication_update,
        name="publication_update",
    ),
    path(
        "publications/<uuid:pk>/delete/",
        views.publication_delete,
        name="publication_delete",
    ),
    path(
        "publications/<uuid:pk>/publish/",
        views.publication_publish,
        name="publication_publish",
    ),
    path(
        "publications/<uuid:pk>/",
        views.publication_detail,
        name="publication_detail",
    ),
    # BrandAsset URLs
    path("brand-assets/", views.brand_asset_list, name="brand_asset_list"),
    path(
        "brand-assets/create/",
        views.brand_asset_create,
        name="brand_asset_create",
    ),
    path(
        "brand-assets/<uuid:pk>/update/",
        views.brand_asset_update,
        name="brand_asset_update",
    ),
    path(
        "brand-assets/<uuid:pk>/delete/",
        views.brand_asset_delete,
        name="brand_asset_delete",
    ),
    # BrandGuideline URLs
    path(
        "brand-guidelines/",
        views.brand_guideline_list,
        name="brand_guideline_list",
    ),
    path(
        "brand-guidelines/create/",
        views.brand_guideline_create,
        name="brand_guideline_create",
    ),
    path(
        "brand-guidelines/<uuid:pk>/update/",
        views.brand_guideline_update,
        name="brand_guideline_update",
    ),
    path(
        "brand-guidelines/<uuid:pk>/delete/",
        views.brand_guideline_delete,
        name="brand_guideline_delete",
    ),
    # WebsitePage URLs
    path("website-pages/", views.website_page_list, name="website_page_list"),
    path(
        "website-pages/create/",
        views.website_page_create,
        name="website_page_create",
    ),
    path(
        "website-pages/<uuid:pk>/update/",
        views.website_page_update,
        name="website_page_update",
    ),
    path(
        "website-pages/<uuid:pk>/delete/",
        views.website_page_delete,
        name="website_page_delete",
    ),
    path(
        "website-pages/<uuid:pk>/publish/",
        views.website_page_publish,
        name="website_page_publish",
    ),
    path(
        "website-pages/<uuid:pk>/",
        views.website_page_detail,
        name="website_page_detail",
    ),
    # WebsiteContent URLs
    path(
        "website-content/",
        views.website_content_list,
        name="website_content_list",
    ),
    path(
        "website-content/create/",
        views.website_content_create,
        name="website_content_create",
    ),
    path(
        "website-content/<uuid:pk>/update/",
        views.website_content_update,
        name="website_content_update",
    ),
    path(
        "website-content/<uuid:pk>/delete/",
        views.website_content_delete,
        name="website_content_delete",
    ),
    # EventCommunication URLs
    path(
        "event-communications/",
        views.event_communication_list,
        name="event_communication_list",
    ),
    path(
        "event-communications/create/",
        views.event_communication_create,
        name="event_communication_create",
    ),
    path(
        "event-communications/<uuid:pk>/update/",
        views.event_communication_update,
        name="event_communication_update",
    ),
    path(
        "event-communications/<uuid:pk>/delete/",
        views.event_communication_delete,
        name="event_communication_delete",
    ),
    path(
        "event-communications/<uuid:pk>/publish/",
        views.event_communication_publish,
        name="event_communication_publish",
    ),
    path(
        "event-communications/<uuid:pk>/",
        views.event_communication_detail,
        name="event_communication_detail",
    ),
    # Timeline URLs
    path("timeline/", views.timeline_list, name="timeline_list"),
]
