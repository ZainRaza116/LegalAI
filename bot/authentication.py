from rest_framework.authentication import TokenAuthentication
class CustomTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'
    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthError('Invalid token.')
        if not token.user.is_active:
            raise AuthError('User inactive or deleted.')
        return (token.user, token)
class AuthError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)