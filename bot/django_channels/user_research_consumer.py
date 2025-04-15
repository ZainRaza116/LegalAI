import json
import LegalAI.settings as settings
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from ..chat_bots.user_research_bot import UserResearchBot
from ..models import Chat, Query, ReplyType
from ..court_listener import (
    search as courtlistener_search,
    opinion as courtlistener_opinion,
)


class UserResearchConsumer(WebsocketConsumer):
    def connect(self):
        # self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"group_{self.scope['user'].id}"
        # Join room group
        print("User in Request Scope: ")
        print(self.scope["user"])
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

        self.send(
            text_data=json.dumps(
                {
                    "type": settings.WEBSOCKET_EVENT_TYPES.CONNECTION_SUCCESS.value,
                    "data": {"message": "You are now connected"},
                }
            )
        )

    def disconnect(self, close_code):
        print(f"Disconnected : {close_code}")
        print(self.room_group_name, self.channel_name, self.scope["user"])
        print("==============")
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data):
        try:
            payload = json.loads(text_data)
            print(payload)

            if payload["type"] == settings.WEBSOCKET_EVENT_TYPES.QUERY_AND_REPLY.value:
                payload_data = payload["data"]
                query = payload_data["query"]
                history = payload_data["history"]
                chat_id = payload_data["chat_id"]

                # ip_address = self.scope.get('client')[0] if 'client' in self.scope else None

                history_string = ""
                for element in history:
                    if element["type"] == "query":
                        history_string += f"query={element['query']['message']},"
                    elif element["type"] == "reply":
                        if element["reply"]["type"] == ReplyType.TEXT.value:
                            history_string += f" reply={json.dumps(element['reply']['value']['message'])},\n"
                        elif (
                            element["reply"]["type"]
                            == ReplyType.ARGUMENT_FROM_OPINION.value
                        ):
                            history_string += f" reply={json.dumps(element['reply']['value']['generated_argument'])},\n"

                _Chat, created = Chat.objects.get_or_create(id=chat_id)
                _Query = Query(chat=_Chat, query=query)
                _Query.save()
                self.scope["_Chat_Instance"] = _Chat
                self.scope["_Query_Instance"] = _Query
                self.scope["_Query_History"] = history_string
                self.scope["gpt_triggers_history"] = []
                # self.send(text_data=json.dumps({"message": "Hi, I am good, Thanks."}))
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name, {"type": "chat.message"}
                )
            elif (
                payload["type"]
                == settings.WEBSOCKET_EVENT_TYPES.COURTLISTENER_SEARCH.value
            ):
                print("i am hre in type.courtlistener_search")
                search_query = payload["data"]["search_query"]
                jurisdiction_id = payload["data"]["jurisdiction_id"]
                jurisdiction_court_id = payload["data"]["jurisdiction_court_id"]
                page_number = payload["data"]["page_number"]
                search_result = courtlistener_search(
                    search_query=search_query,
                    page_number=page_number,
                    jurisdiction_id=jurisdiction_id,
                    jurisdiction_court_id=jurisdiction_court_id,
                )
                print("search results", search_result)
                self.send(
                    text_data=json.dumps(
                        {
                            "type": settings.WEBSOCKET_EVENT_TYPES.COURTLISTENER_SEARCH.value,
                            "data": search_result,
                        }
                    )
                )
            elif (
                payload["type"]
                == settings.WEBSOCKET_EVENT_TYPES.COURTLISTENER_OPINION.value
            ):
                opinion = courtlistener_opinion(payload["data"]["opinion_id"])
                self.send(
                    text_data=json.dumps(
                        {
                            "type": settings.WEBSOCKET_EVENT_TYPES.COURTLISTENER_OPINION.value,
                            "data": opinion,
                        }
                    )
                )
            elif (
                payload["type"]
                == settings.WEBSOCKET_EVENT_TYPES.COURTLISTENER_CITATIONS.value
            ):
                payload_data = payload["data"]
                chat_id = payload_data["chat_id"]
                history = payload_data["history"]
                selected_opinions = payload_data["selected_opnions"]
                history_string = ""
                for element in history:
                    if element["type"] == "query":
                        history_string += f"query={element['query']['message']},"
                    elif element["type"] == "reply":
                        if element["reply"]["type"] == ReplyType.TEXT.value:
                            history_string += f" reply={json.dumps(element['reply']['value']['message'])},\n"
                        elif (
                            element["reply"]["type"]
                            == ReplyType.ARGUMENT_FROM_OPINION.value
                        ):
                            history_string += f" reply={json.dumps(element['reply']['value']['generated_argument'])},\n"
                _Chat = Chat.objects.get(id=chat_id)
                _Query = Query.get_latest_query_by_chat(chat_id)
                self.scope["_Chat_Instance"] = _Chat
                self.scope["_Query_Instance"] = _Query
                self.scope["_Query_History"] = history_string
                self.scope["_Selected_Opinions"] = selected_opinions
                conversational_handler = UserResearchConsumer(_ChatInstance=self)
                conversational_handler.handle_citations()
        except Exception as ex:
            self.send(
                text_data=json.dumps(
                    {
                        "type": settings.WEBSOCKET_EVENT_TYPES.ERROR.value,
                        "data": {"message": f"An error has occured {str(ex)}"},
                    }
                )
            )

    # Receive message from room group
    def chat_message(self, event):
        conversational_handler = UserResearchBot(_ChatInstance=self)
        conversational_handler.handle()
        # Send message to WebSocket
        # self.send(text_data=json.dumps({"message": message}))
