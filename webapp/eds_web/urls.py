from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView

from accounts.forms import StyledAuthenticationForm, StyledPasswordChangeForm

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="records:list", permanent=False)),
    path(
        "login/",
        auth_views.LoginView.as_view(
            authentication_form=StyledAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            form_class=StyledPasswordChangeForm,
            success_url=reverse_lazy("records:list"),
        ),
        name="password_change",
    ),
    path("records/", include("records.urls")),
    path("users/", include("accounts.urls")),
    path("django-admin/", admin.site.urls),
]
