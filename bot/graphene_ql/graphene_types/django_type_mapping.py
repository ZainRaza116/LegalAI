import graphene
from graphene_django import DjangoObjectType
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from bot.models import (Profile,Chat,Query as UserQuery,Reply,Source,Files)

class RequestResponseType(graphene.ObjectType):
    status = graphene.Boolean()
    status_code = graphene.Int()
    message = graphene.String()

class AppUserType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            "id",
            "last_login",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "profile",
            "auth_token",
        )
        interfaces = (graphene.relay.Node,)

    @classmethod
    def get_node(cls, info, id):
        # Implementing the get_node method is necessary for relay support
        return cls._meta.model.objects.get(pk=id)

class UserProfileType(DjangoObjectType):
    class Meta:
        model = Profile
        fields = ("id", "name", "usrType", "indexUUID", "imgUrl")
        interfaces = (graphene.relay.Node,)

class DjangoTokenType(DjangoObjectType):
    class Meta:
        model = Token
        fields = ("key",)





