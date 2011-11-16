# See https://bugzilla.mozilla.org/show_bug.cgi?id=698031

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User

from registration.views import register as original_register
from .forms import RegistrationForm

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

def verbatim_contributors(request,
              template_name='mozilla_extras/verbatim-contributors.html'):
    contributors = User.objects.all().order_by('first_name', 'last_name', 'username')
    return render_to_response(template_name,
                              {'contributors': contributors},
                              context_instance=RequestContext(request))
