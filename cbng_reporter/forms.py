from typing import ClassVar

from django import forms

from cbng_reporter.constants import ReportStatus
from cbng_reporter.models import User


class RevertLookupForm(forms.Form):
    id = forms.IntegerField(min_value=1, label="Revert ID", widget=forms.TextInput(attrs={"class": "form-control"}))


class ReportForm(forms.Form):
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))


class CommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control", "rows": 10}))


class StatusForm(forms.Form):
    status = forms.TypedChoiceField(choices=ReportStatus.choices, coerce=int)


class OptionsForm(forms.ModelForm):
    next_on_review = forms.BooleanField(required=False, label="Redirect on review")
    keyboard_shortcuts = forms.BooleanField(required=False, label="Review keyboard shortcuts")
    hide_anon = forms.BooleanField(required=False, label="Hide Anon")

    class Meta:
        model = User
        fields: ClassVar = ["next_on_review", "keyboard_shortcuts", "hide_anon"]
