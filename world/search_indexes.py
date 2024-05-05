from haystack import indexes
from .models import Team, Player


class PlayerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, template_name="search/player.txt")

    player_name = indexes.CharField(model_attr="name")

    i_player_name = indexes.NgramField(model_attr="name")
 
    def get_model(self):
        return Player

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

class TeamIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True, template_name="search/team.txt")

    team_name = indexes.CharField(model_attr="name")

    i_team_name = indexes.NgramField(model_attr="name")
 
    def get_model(self):
        return Team

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


