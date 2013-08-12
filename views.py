# See https://bugzilla.mozilla.org/show_bug.cgi?id=698031

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from pootle_statistics.models import Submission
from pootle_translationproject.models import TranslationProject
from pootle_project.models import Project
from pootle_language.models import Language
from pootle_app.models import Suggestion
from registration.views import register as original_register
from .forms import RegistrationForm

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from pootle.apps.pootle_profile.forms import language_list
from pootle.apps.pootle_profile.views import redirect_after_login
from django.contrib import auth


# Different from pootle_profile.forms in that this adds a
# longer username form field
def lang_auth_form_factory(request, **kwargs):

    class LangAuthenticationForm(AuthenticationForm):

        username = forms.CharField(label=_("Username"), max_length=75)
        language = forms.ChoiceField(label=_('Interface Language'),
                                     choices=language_list(request),
                                     initial="", required=False)


        def clean(self):
            username = self.cleaned_data.get('username')
            password = self.cleaned_data.get('password')

            if username and password:
                self.user_cache = auth.authenticate(username=username,
                                                    password=password)

                if self.user_cache is None:
                    raise forms.ValidationError(
                        _("Please enter a correct username and password. "
                          "Note that both fields are case-sensitive.")
                    )
                elif not self.user_cache.is_active:
                    raise forms.ValidationError(_("This account is inactive."))

            return self.cleaned_data

    return LangAuthenticationForm(**kwargs)

# Override this in its entirety from pootle_profile.view
# so that we can override what form instance gets used.
def login(request):
    """Logs the user in."""
    if request.user.is_authenticated():
        return redirect_after_login(request)
    else:
        if request.POST:
            form = lang_auth_form_factory(request, data=request.POST)

            # Do login here
            if form.is_valid():
                auth.login(request, form.get_user())

                language = request.POST.get('language')
                request.session['django_language'] = language

                return redirect_after_login(request)
        else:
            form = lang_auth_form_factory(request)

        context = {
            'form': form,
            'next': request.GET.get(auth.REDIRECT_FIELD_NAME, ''),
            }

        return render_to_response("index/login.html", context,
                                  context_instance=RequestContext(request))


def register(request, success_url=None,
             form_class=RegistrationForm,
             template_name='mozilla_extras/registration_form.html',
             extra_context=None):
    """
    overriding the register view
    (this needs a better doc string /peterbe)
    """
    return original_register(request,
      form_class=form_class,
      template_name=template_name,
      extra_context=extra_context
    )
