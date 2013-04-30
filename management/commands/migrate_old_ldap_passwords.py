"""
In a previous incarnation of pootle, when a user logged in with LDAP a
random password was generated like this:
`LDAP_eZ8Heh4zSKfEfXsfkH4HbvQCgJHfyq5r` for example. It was supposed to say
that the password is not usable and that instead it should check credentials
by binding to LDAP.

But Django uses the convention that if the password is `!` it's unusable.
"""

from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User


class Command(NoArgsCommand):

    def handle(self, **options):
        ldap_users = User.objects.filter(password__startswith='LDAP_')
        count = 0
        for user in ldap_users:
            user.set_unusable_password()
            user.save()
            count += 1

        print "Fixed", count, "LDAP users's passwords"
