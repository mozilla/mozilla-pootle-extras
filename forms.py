# See https://bugzilla.mozilla.org/show_bug.cgi?id=698031

from django import forms
from registration.forms import RegistrationForm as OriginalRegistrationForm

class RegistrationForm(OriginalRegistrationForm):
    displayname = forms.CharField(
                                max_length=150,
                                )
    tos_license = forms.BooleanField(required=True)
    tos_rules = forms.BooleanField(required=True)

    def save(self):
        new_user = super(RegistrationForm, self).save()
        if self.cleaned_data['displayname']:
            displayname = self.cleaned_data['displayname'].strip()
            first_name, last_name = displayname.split(None, 1)
            new_user.first_name = first_name
            new_user.last_name = last_name
            new_user.save()
        return new_user
