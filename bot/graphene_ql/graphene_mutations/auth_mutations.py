import graphene
import graphql_jwt
from graphql_jwt.decorators import login_required
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from bot.graphene_ql.graphene_types.django_type_mapping import AppUserType,RequestResponseType
from bot.models import Profile
from .base_mutations import BaseMutation


class ObtainJSONWebToken(graphql_jwt.JSONWebTokenMutation):
    user = graphene.Field(AppUserType)

    @classmethod
    def set_django_token(cls, user):
        token = Token.objects.get(user=user)
        token.delete()
        new_token = Token(user=user)
        new_token.save()

    @classmethod
    def resolve(cls, root, info, **kwargs):
        cls.set_django_token(info.context.user)
        return cls(
            user=User.objects.get(id=info.context.user.id),
        )

class SignUpMutation(BaseMutation):
    class Arguments:
        email = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(AppUserType)
    
    @classmethod
    def mutate(cls, root, info, email, first_name, last_name, password):
        try:
            # Validate required fields
            if not email or not first_name or not last_name or not password:
                raise Exception(
                    "All fields (email, first_name, last_name, password) are required."
                )

            user, created = User.objects.get_or_create(username=email, email=email)

            if not created:
                return cls(
                    user=user,
                    response=RequestResponseType(
                        status=False,
                        status_code=400,
                        message="A user with this email already exists.",
                    ),
                )

            user.first_name = first_name
            user.last_name = last_name
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            user.save()
            profile = Profile(user=user, usrType="normal", name=first_name)
            profile.save()

            user.set_password(password)
            user.save()

            # Get or create a new token for the user
            token, created = Token.objects.get_or_create(user=user)

            return cls(
                user=user,
                response=RequestResponseType(
                    status=True,
                    status_code=201,
                    message="User Account Created Successfully.",
                ),
            )

        except Exception as e:
            # Handle unknown exceptions
            print("An Error Occured: ", str(e))
            return cls(
                user=None,
                response=RequestResponseType(
                    status=False,
                    status_code=500,
                    message=f"An Error Occured: {str(e)}",
                ),
            )

class ChangePasswordMutation(BaseMutation):
    class Arguments:
        old_password = graphene.String(required=True)
        new_password = graphene.String(required=True)

    user = graphene.Field(AppUserType)

    @classmethod
    @login_required
    def mutate(cls, root,info, old_password, new_password):
        _user = info.context.user
        try:
            # Validate old and new password
            if not _user.check_password(old_password):
                return cls(
                    user=None,
                    response=RequestResponseType(
                        status=False,
                        status_code=400,
                        message="Old password is incorrect",
                    ),
                )

            # Update user password
            _user.set_password(new_password)
            _user.save()

            # Revoke old token
            token = Token.objects.get(user=_user)
            token.delete()
            new_token, created = Token.objects.get_or_create(user=_user)

            # Create a new refresh token
            # refresh_token = create_refresh_token(user)

            return cls(
                user=User.objects.get(id=info.context.user.id),
                response=RequestResponseType(
                    status=True,
                    status_code=200,
                    message="Password updated successfully",
                ),
            )
        except Exception as ex:
            return cls(
                user=None,
                response=RequestResponseType(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {ex}",
                ),
            )


class AuthMutation(graphene.ObjectType):
    sign_up = SignUpMutation.Field()
    log_in = ObtainJSONWebToken.Field()
    change_password = ChangePasswordMutation.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
