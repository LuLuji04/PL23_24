from django.contrib import admin

from .models import User, Team, Player, Match

admin.site.register(User)
admin.site.register(Team)
admin.site.register(Player)
admin.site.register(Match)
