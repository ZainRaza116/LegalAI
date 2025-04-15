from channels.db import database_sync_to_async
from rest_framework.authtoken.models import Token
import re

@database_sync_to_async
def validate_token(token):
    try:

        token_instance=Token.objects.get(key=token).user
        print("Found the token : ",token_instance)
        return token_instance
    except Token.DoesNotExist:
        raise Token.DoesNotExist()


class QueryAuthMiddleware:
    """
    Custom middleware (insecure) that takes user IDs from the query string.
    """

    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):
        # Look up user from query string (you should also do things like
        # checking if it is a valid user ID, or if scope["user"] is already
        # populated).

        path = scope.get('path', '')
        print("path:",path)
        token = path.split('/')[-1]
        room_name_match = re.match(r'^/ws/[^/]+/(?P<room_name>\w+)/$', path)

        print("room name:", room_name_match)
        if room_name_match:
            token = room_name_match.group('room_name')
        try:
            # token = scope["url_route"]["kwargs"]["room_name"]

            scope["user"] = await validate_token(token)
        except Token.DoesNotExist:
            # Reject the connection if the token is not found
            await send(
                {"type": "websocket.close", "code": 4000, "error": "Invalid Token"}
            )
            return

        return await self.app(scope, receive, send)
