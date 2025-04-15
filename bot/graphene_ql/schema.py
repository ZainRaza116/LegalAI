import graphene
from graphql_jwt.decorators import login_required
from bot.graphene_ql.graphene_mutations.auth_mutations import AuthMutation
from .graphene_types.django_type_mapping import (
    UserProfileType,Profile)

class Query(graphene.ObjectType):
    profiles = graphene.List(UserProfileType)

    @login_required
    def resolve_profiles(self, info, **kwargs):
        return Profile.objects.all()


class Mutation(AuthMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
