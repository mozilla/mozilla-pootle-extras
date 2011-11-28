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

    _project_map = {}
    for project in Project.objects.exclude(fullname=u"Testing, please don't work here"):
        if 'test' in project.fullname.lower():
            print "PARNING"
            print repr(project.fullname)
            print
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

        #print "\t", profile.suggester.all()

        #if profile.suggester.all().count():
        #    print dir(profile.suggester.all()[0])

        #print
    #print _projects
    #print _languages
#    pprint(_languages)
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
#    pprint(contributors)


#    for i, p in enumerate(_projects):
#        try:
#            pn=Project.objects.get(id=p).fullname
#        except Project.DoesNotExist:
#            pn='*deleted*'
#        print str(i+1).ljust(2), pn.ljust(40), len(_projects[p])

#    for i, l in enumerate(_languages):
#        #try:
#        ln=Language.objects.get(id=l).fullname
#        #except Language.DoesNotExist:
#        #    ln='*deleted*'

#        print str(i+1).ljust(2), ln.ljust(40), len(_languages[l])



    if 0:#for profile in PootleProfile.objects.all().order_by('?')[:1]:
#        print repr(profile.user)
        langs = [x.fullname for x in profile.languages.all()]
#        print "\tLs:", langs
        #lang_counts[profile.languages.all().count()] += 1
        projs = [x.fullname for x in profile.projects.all()]
#        print "\tPs:", projs
        #proj_counts[profile.projects.all().count()] += 1

        langs2 =set()
        projs2=set()
        for s in Submission.objects.filter(submitter=profile).select_related('translation_project'):
            tp = s.translation_project
            #print dir(tp)
            #print type(tp.language), type(tp.language_id)
            #break
            langs2.add(tp.language_id)
            try:
                projs2.add(tp.project_id)
            except Project.DoesNotExist:
                pass
        for s in Suggestion.objects.filter(suggester=profile).select_related('translation_project'):
            tp = s.translation_project
            langs2.add(tp.language_id)
            try:
                projs2.add(tp.project_id)
            except Project.DoesNotExist:
                pass
        #for r in Review.objects.filter(suggester=profile).select_related('translation_project'):
        #    tp = s.translation_project
        #    langs2.add(tp.language_id)
        #    try:
        #        projs2.add(tp.project_id)
        #    except Project.DoesNotExist:
        #        pass

        lang_counts[len(langs2)] += 1
        proj_counts[len(projs2)] += 1

#        print "\tL2s:", langs2
#        print "\tP2s:", projs2
#        print

    if 0:

        print "LANGS"
        lang_counts =dict(lang_counts)
        pprint(lang_counts)

        people = sum(lang_counts.values()) * 1.0
        for c in sorted(lang_counts.keys()):
            print c, "%.1f%%"%(lang_counts[c]*100 / people)


        print "PROJS"
        proj_counts=dict(proj_counts)
        pprint(proj_counts)

        peoplex = sum(lang_counts.values()) * 1.0
        assert peoplex==people
        for c in sorted(proj_counts.keys()):
            print c, "%.1f%%"%(proj_counts[c]*100 / people)


    return render_to_response(template_name,
                              {'contributors': contributors},
                              context_instance=RequestContext(request))
