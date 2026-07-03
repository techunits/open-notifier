from django.urls import path

from . import views

app_name = "en_console"

urlpatterns = [
    # ---- HTML pages ----
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("tenants/", views.tenants_page, name="tenants"),
    path("users/", views.users_page, name="users"),
    path("templates/", views.templates_page, name="templates"),
    path("templates/new/", views.template_editor_page, name="template-new"),
    path("templates/<uuid:pk>/edit/", views.template_editor_page, name="template-edit"),
    path("configurations/", views.configurations_page, name="configurations"),
    path("integrations/", views.integrations_page, name="integrations"),
    path("apikeys/", views.apikeys_page, name="apikeys"),
    path("logs/", views.logs_page, name="logs"),
    path("profile/", views.profile_page, name="profile"),

    # ---- JSON API ----
    path("api/meta/", views.MetaView.as_view(), name="api-meta"),
    path("api/me/", views.MeView.as_view(), name="api-me"),
    path("api/profile/", views.ProfileView.as_view(), name="api-profile"),
    path("api/profile/password/", views.ChangePasswordView.as_view(), name="api-profile-password"),
    path("api/stats/", views.StatsView.as_view(), name="api-stats"),

    path("api/tenants/", views.TenantListCreate.as_view(), name="api-tenants"),
    path("api/tenants/<uuid:pk>/", views.TenantDetail.as_view(), name="api-tenant"),

    path("api/users/", views.UserListCreate.as_view(), name="api-users"),
    path("api/users/<int:pk>/", views.UserDetail.as_view(), name="api-user"),

    path("api/templates/", views.TemplateListCreate.as_view(), name="api-templates"),
    path("api/templates/preview/", views.TemplatePreviewView.as_view(), name="api-template-preview"),
    path("api/templates/<uuid:pk>/", views.TemplateDetail.as_view(), name="api-template"),

    path("api/configurations/", views.ConfigurationListCreate.as_view(), name="api-configurations"),
    path("api/configurations/<uuid:pk>/", views.ConfigurationDetail.as_view(), name="api-configuration"),

    path("api/integrations/", views.IntegrationList.as_view(), name="api-integrations"),
    path("api/integrations/<str:key>/", views.IntegrationDetail.as_view(), name="api-integration"),

    path("api/apikeys/", views.TenantApiKeyListCreate.as_view(), name="api-apikeys"),
    path("api/apikeys/<uuid:pk>/", views.TenantApiKeyDetail.as_view(), name="api-apikey"),

    path("api/logs/", views.NotificationLogList.as_view(), name="api-logs"),
]
