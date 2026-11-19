from pathlib import Path

from django import forms
from django.conf import settings
from django.template.defaultfilters import filesizeformat

from .models import EDSRecord

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


class EDSRecordForm(forms.ModelForm):
    remove_vhx_image = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
    remove_eds_image = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = EDSRecord
        fields = ["component", "vhx_image", "vhx_remark", "eds_image", "eds_remark", "remark"]
        widgets = {
            "component": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Connector housing A12", "autofocus": True}
            ),
            # Plain FileInput: images are served through an authenticated view,
            # not a public media URL, so ClearableFileInput's link is not used.
            "vhx_image": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "eds_image": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "vhx_remark": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Notes on the VHX image"}),
            "eds_remark": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Notes on the EDS spectrum"}),
            "remark": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "General remarks"}),
        }

    def clean_component(self):
        value = self.cleaned_data["component"].strip()
        if not value:
            raise forms.ValidationError("Component name is required.")
        return value

    def _clean_image(self, field):
        image = self.cleaned_data.get(field)
        upload = self.files.get(self.add_prefix(field))
        if upload is not None:
            limit = settings.MAX_IMAGE_UPLOAD_SIZE
            if upload.size > limit:
                raise forms.ValidationError(f"Image must be smaller than {filesizeformat(limit)}.")
            if Path(upload.name).suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
                raise forms.ValidationError("Unsupported image type.")
        return image

    def clean_vhx_image(self):
        return self._clean_image("vhx_image")

    def clean_eds_image(self):
        return self._clean_image("eds_image")

    def save(self, commit=True):
        record = super().save(commit=False)
        for field in EDSRecord.IMAGE_FIELDS:
            new_upload = self.files.get(self.add_prefix(field))
            if self.cleaned_data.get(f"remove_{field}") and new_upload is None:
                setattr(record, field, "")
        if commit:
            record.save()
        return record
