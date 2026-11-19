from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    SetPasswordForm,
    UserCreationForm,
)

from . import throttle

User = get_user_model()


def _style(form):
    for name, field in form.fields.items():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault("class", "form-check-input")
        else:
            widget.attrs.setdefault("class", "form-control")


class StyledAuthenticationForm(AuthenticationForm):
    """Login form with brute-force lockout (see accounts.throttle)."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "locked": "Too many failed login attempts. Please try again later or contact your administrator.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)
        self.fields["username"].widget.attrs["placeholder"] = "Username"
        self.fields["password"].widget.attrs["placeholder"] = "Password"

    def clean(self):
        username = self.cleaned_data.get("username", "")
        ip = throttle.client_ip(self.request)
        if throttle.is_locked(username, ip):
            # Refuse before checking the password, so guesses during lockout are useless.
            raise forms.ValidationError(self.error_messages["locked"], code="locked")
        try:
            cleaned = super().clean()
        except forms.ValidationError:
            throttle.register_failure(username, ip)
            raise
        throttle.reset(username)
        return cleaned


class UserCreateForm(UserCreationForm):
    is_staff = forms.BooleanField(
        label="Administrator",
        required=False,
        help_text="Administrators can manage user accounts and view the full activity log.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_staff")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class UserUpdateForm(forms.ModelForm):
    is_staff = forms.BooleanField(label="Administrator", required=False)
    is_active = forms.BooleanField(
        label="Active",
        required=False,
        help_text="Inactive users cannot log in. Prefer this over deleting accounts.",
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_staff", "is_active")

    def __init__(self, *args, acting_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.acting_user = acting_user
        _style(self)

    def clean(self):
        cleaned = super().clean()
        if self.acting_user and self.instance.pk == self.acting_user.pk:
            if not cleaned.get("is_staff"):
                raise forms.ValidationError("You cannot remove your own administrator rights.")
            if not cleaned.get("is_active"):
                raise forms.ValidationError("You cannot deactivate your own account.")
        return cleaned


class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)
