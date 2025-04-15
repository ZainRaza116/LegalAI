from django.urls import re_path

from . import court_brief_consumer
from bot.django_channels.user_research_consumer import UserResearchConsumer

websocket_urlpatterns = [
    # re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.CourtBriefConsumer.as_asgi()),
    re_path(r"ws/socket-server/(?P<room_name>\w+)/$", court_brief_consumer.CourtBriefConsumer.as_asgi()),
    re_path(r"ws/user-research/(?P<room_name>\w+)/$", UserResearchConsumer.as_asgi())
]