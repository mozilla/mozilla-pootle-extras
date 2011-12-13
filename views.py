# See https://bugzilla.mozilla.org/show_bug.cgi?id=698031

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from pootle_profile.models import PootleProfile

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
    from collections import defaultdict; from pprint import pprint
    lang_counts = defaultdict(int)
    proj_counts = defaultdict(int)
    from pootle_statistics.models import Submission
    from pootle_project.models import Project
    from pootle_language.models import Language
    from pootle_app.models import Suggestion

    _languages = {}
    _language_map = {}
    for language in Language.objects.all():
        _languages[language.fullname] = defaultdict(set)
        _language_map[language.id] = language.fullname

    def lmap(id):
        return _language_map[id]

    EXCLUDED_PROJECT_NAMES = (
      u"Testing, please don't work here",
    )
    _project_map = {}

    for project in Project.objects.exclude(fullname__in=EXCLUDED_PROJECT_NAMES):
        _project_map[project.id] = project.fullname

    def pmap(id):
        try:
            return _project_map[id]
        except KeyError:
            raise Project.DoesNotExist(id)

    def user_name(user):
        name = ('%s %s' % (user.first_name, user.last_name)).strip()
        if not name:
            name = user.username
        if 'test' in name:
            print "WARNING"
            print repr(name)
            print repr(user.username)
            print
        return name


    for profile in PootleProfile.objects.all().select_related('user'):#order_by('?')[:10]:
        name = user_name(profile.user)

        for s in profile.suggester.all().select_related('translation_project'):
            tp = s.translation_project
            try:
                _languages[lmap(tp.language_id)][pmap(tp.project_id)].add(name)
            except Project.DoesNotExist:
                pass

        for s in profile.reviewer.all().select_related('translation_project'):
            tp = s.translation_project
            try:
                _languages[lmap(tp.language_id)][pmap(tp.project_id)].add(name)
            except Project.DoesNotExist:
                pass

        for s in profile.submission_set.all().select_related('translation_project'):
            tp = s.translation_project
            try:
                _languages[lmap(tp.language_id)][pmap(tp.project_id)].add(name)
            except Project.DoesNotExist:
                pass

    contributors = []
    for language, projectsmap in _languages.items():
        projects = []
        users = None
        for projectname, usersset in projectsmap.items():
            users = sorted(usersset)
            projects.append((projectname, users))
        if users:
            contributors.append((language, projects))
    contributors.sort()


    print "# NODES", sum(len(users) for language, projects in contributors for name, users in projects)
    return render_to_response(template_name,
                              {'contributors': contributors},
                              context_instance=RequestContext(request))


def verbatim_contributors(request,
              template_name='mozilla_extras/verbatim-contributors.html'):
    """render a nested list like this::

        contributors = [
          ('french', [
            ('Hackaraus', ['Auser Name', 'username2', ...]),
            ('Project 2', ['username1', 'usernameX', ...]),
            ...
            ]),
          ('spanish', [
            ('Project 1', ['User 1', 'User2', ...]),
            ('Project 2', ['User 1', 'UserX', ...]),
            ]

        }
    """
    EXCLUDED_PROJECT_NAMES = (
      u"Testing, please don't work here",
    )

    EXCLUDED_USERNAMES = (
      u'sorryjusttesting',
      u'marcoos_test',
      u'test',
      u'\'">,test \'">,test',
      u'testo\'"><',
    )

    from pootle_statistics.models import Submission
    from pootle_translationproject.models import TranslationProject
    from pootle_project.models import Project
    from pootle_language.models import Language
    from pootle_app.models import Suggestion

    _user_names = {}  # user id -> name
    for user in (User.objects.exclude(username__in=EXCLUDED_USERNAMES)
                 .values('id', 'first_name', 'last_name', 'username')):
        name = ('%s %s' % (user['first_name'], user['last_name'])).strip()
        if not name:
            name = user['username']
        #if 'test' in name:
        #    print "WARNING"
        #    print repr(name)
        #    print repr(user['username'])
        #    print
        _user_names[user['id']] = name

    _language_names = {}  # language id -> name
    for language in Language.objects.all().values('id', 'fullname'):
        _language_names[language['id']] = language['fullname']

    _project_names = {}  # project id -> name
    for project in (Project.objects
                    .exclude(fullname__in=EXCLUDED_PROJECT_NAMES)
                    .values('id', 'fullname')):
        _project_names[project['id']] = project['fullname']

    # map users to projects per language across:
    # submitters, suggesters and reviewers
    _languages = {}
    _tp_to_lang_id = {}
    _tp_to_proj_id = {}

    # prepare a map of TranslationProject IDs to
    # language and project to save queries for later
    for tp in (TranslationProject.objects.all()
               .values('id', 'language_id', 'project_id')):
        _tp_to_lang_id[tp['id']] = tp['language_id']
        _tp_to_proj_id[tp['id']] = tp['project_id']

    for model, user_key in ((Submission, 'submitter_id'),
                            (Suggestion, 'suggester_id'),
                            (Suggestion, 'reviewer_id')):
        for item in (model.objects.all()
                     .values('translation_project_id', user_key)
                     .distinct()):
            lang_id = _tp_to_lang_id[item['translation_project_id']]
            proj_id = _tp_to_proj_id[item['translation_project_id']]
            user_id = item[user_key]
            if not user_id:  # bad paste on_delete cascades
                continue
            if lang_id not in _languages:
                _languages[lang_id] = {}
            if proj_id not in _languages[lang_id]:
                _languages[lang_id][proj_id] = set()
            _languages[lang_id][proj_id].add(user_id)

    # finally, turn this massive dict into a list of lists of lists
    # to be used in the template to loop over.
    # also change from IDs to real names
    contributors = []
    for lang_id, projectsmap in _languages.items():
        language = _language_names[lang_id]
        projects = []
        users = None
        for proj_id, user_ids in projectsmap.items():
            usersset = [_user_names[x] for x in user_ids]
            users = sorted(usersset, lambda x, y: cmp(x.lower(), y.lower()))
            try:
                projectname = _project_names[proj_id]
            except KeyError:
                # some legacy broken project or excluded
                continue
            if users:
                projects.append((projectname, users))
        if projects:
            contributors.append((language, projects))
    contributors.sort()
#    print "# NODES", sum(len(users) for language, projects in contributors for name, users in projects)
    return render_to_response(template_name,
                              {'contributors': contributors},
                              context_instance=RequestContext(request))
