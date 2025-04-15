import os
import re
import json
from threading import Thread
from queue import Queue, Empty
from collections.abc import Generator

from langchain.callbacks.base import BaseCallbackHandler
from langchain.embeddings import HuggingFaceEmbeddings

from langchain.llms import OpenAI

# from langchain.prompts import PromptTemplate
# from langchain_core.output_parsers import JsonOutputParser

from LegalAI import settings
from bot.chat_bots.util import save_chat_tokens
from bot.models import (
    Query,
    ReplyType,
    Reply,
    Source,
    SelectedOpinion,
)
from ..utilities import (
    GetDocsFromVectorDB,
    GptTrigger,
)
from ..court_listener import (
    search as courtlistener_search,
    opinion as court_listener_opinion,
)

hf = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")


class UserResearchBot:
    def __init__(self, _ChatInstance) -> None:
        from bot.django_channels.user_research_consumer import UserResearchConsumer

        os.environ["OPENAI_API_KEY"] = settings.OPENAI_KEY
        self.ChatInstance: UserResearchConsumer = _ChatInstance
        self.model_name = settings.PRIMARY_MODEL

    def generate_stream(
        self,
        Query_Instance: Query,
        prompt: str,
    ):
        trigger_found_flag = False
        trigger_number = None
        first_and_and_flag = False
        trigger_number_flag_after_first_and_and = False
        trigger_number_removal_flag = False

        Reply_Instance_Against_Trigger_4 = None
        Reply_Instance_Against_Trigger_3 = None
        Reply_Instance_Against_Trigger_2 = None
        Reply_Instance_Against_Trigger_1 = None

        for next_token, content, job_done in self.stream(prompt):
            print(next_token)
            if not trigger_found_flag:
                # Check if the response contains a trigger (&&1&&, &&2&&, &&3&&)
                trigger_1_index = content.find("&&1&&")
                trigger_2_index = content.find("&&2&&")
                trigger_3_index = content.find("&&3&&")
                trigger_4_index = content.find("&&4&&")

                if (
                    trigger_1_index != -1
                    or trigger_2_index != -1
                    or trigger_3_index != -1
                    or trigger_4_index != -1
                ):
                    trigger_number = self.extract_trigger_number(content)
                    trigger_found_flag = True
                    print("Trigger Found, Trigger is ", trigger_number)

            # print("Content is  ", content)
            if trigger_found_flag:
                content = self.remove_trigger_number(content)
            if not trigger_number_removal_flag:
                if next_token == "&&":
                    first_and_and_flag = True
                    next_token = ""
                if first_and_and_flag and (
                    next_token == "1" or next_token == "2" or next_token == "3"
                ):
                    trigger_number_flag_after_first_and_and = True
                    next_token = ""
                if (
                    first_and_and_flag
                    and trigger_number_flag_after_first_and_and
                    and next_token == "&&"
                ):
                    next_token = ""
                    trigger_number_removal_flag = True
            # print(next_token)
            if trigger_number is None:
                continue

            if trigger_number == "4":
                if Reply_Instance_Against_Trigger_4 is None:
                    Reply_Instance_Against_Trigger_4, _ = Reply.save_reply(
                        Query_Instance,
                        ReplyType.LLM_ACTION.value,
                        {
                            "trigger_number": trigger_number,
                            "trigger_content": "",
                            "message": "",
                        },
                    )
                if job_done:
                    Reply_Instance_Against_Trigger_4.value = {
                        "trigger_number": trigger_number,
                        "trigger_content": content,
                        "message": "Please wait, System is initiating US Constitution DB....",
                    }
                    Reply_Instance_Against_Trigger_4.save()
                    Thread(target=save_chat_tokens, args=(prompt, content, Reply_Instance_Against_Trigger_4)).start()
                    _, reply_json = Reply.get_reply_by_id(
                        id=Reply_Instance_Against_Trigger_4.id
                    )
                    yield self.arrange_response_to_yield(
                        query_id=Query_Instance.id, reply_json=reply_json
                    )
                    print("=====================")
                    print("Done")
                    print("=====================")
                    Thread(
                        target=self.handle_trigger,
                        args=(
                            trigger_number,
                            Query_Instance.query,
                            content,
                        ),
                    ).start()
                else:
                    continue

            if trigger_number == "3":
                if Reply_Instance_Against_Trigger_3 is None:
                    Reply_Instance_Against_Trigger_3, _ = Reply.save_reply(
                        Query_Instance, ReplyType.TEXT.value, {"message": ""}
                    )
                if job_done:
                    print(content)
                    Reply_Instance_Against_Trigger_3.value = {"message": content}
                    Reply_Instance_Against_Trigger_3.save()
                    Thread(target=save_chat_tokens, args=(prompt, content, Reply_Instance_Against_Trigger_3)).start()

                    yield self.arrange_response_to_yield(
                        query_id=Query_Instance.id,
                        reply_json={
                            "id": Reply_Instance_Against_Trigger_3.id,
                            "type": Reply_Instance_Against_Trigger_3.type,
                            "value": {"message": next_token},
                            "reply_datetime": Reply_Instance_Against_Trigger_3.reply_datetime.isoformat(),
                        },
                        completed=True,
                    )
                    print("=====================")
                    print("Done")
                    print("=====================")
                else:
                    yield self.arrange_response_to_yield(
                        query_id=Query_Instance.id,
                        reply_json={
                            "id": Reply_Instance_Against_Trigger_3.id,
                            "type": Reply_Instance_Against_Trigger_3.type,
                            "value": {"message": next_token},
                            "reply_datetime": Reply_Instance_Against_Trigger_3.reply_datetime.isoformat(),
                        },
                        completed=False,
                    )
                    # yield next_token

            if trigger_number == "2":
                if Reply_Instance_Against_Trigger_2 is None:
                    Reply_Instance_Against_Trigger_2, _ = Reply.save_reply(
                        Query_Instance,
                        ReplyType.LLM_ACTION.value,
                        {
                            "trigger_number": trigger_number,
                            "trigger_content": "",
                            "message": "",
                        },
                    )

                if job_done:
                    Reply_Instance_Against_Trigger_2.value = {
                        "trigger_number": trigger_number,
                        "trigger_content": content,
                        "message": "Please wait, system is triggering search from your documents.....",
                    }
                    Reply_Instance_Against_Trigger_2.save()
                    Thread(target=save_chat_tokens, args=(prompt, content, Reply_Instance_Against_Trigger_2)).start()
                    _, reply_json = Reply.get_reply_by_id(
                        id=Reply_Instance_Against_Trigger_2.id
                    )
                    yield self.arrange_response_to_yield(
                        query_id=Query_Instance.id,
                        reply_json=reply_json,
                        completed=True,
                    )
                    print("=====================")
                    print("Done")
                    print("=====================")
                    Thread(
                        target=self.handle_trigger,
                        args=(
                            trigger_number,
                            Query_Instance.query,
                            content,
                        ),
                    ).start()

                else:
                    continue
                    # yield self.arrange_response_to_yield(
                    #     query_id=Query_Instance.id,
                    #     reply_id=None,
                    #     reply="",
                    # )

            if trigger_number == "1":
                if Reply_Instance_Against_Trigger_1 is None:
                    Reply_Instance_Against_Trigger_1, _ = Reply.save_reply(
                        Query_Instance,
                        ReplyType.LLM_ACTION.value,
                        {
                            "trigger_number": trigger_number,
                            "trigger_content": "",
                            "message": "",
                        },
                    )
                if job_done:
                    Reply_Instance_Against_Trigger_1.value = {
                        "trigger_number": trigger_number,
                        "trigger_content": content,
                        "message": "Please wait system is triggering relative pipelines",
                    }
                    Reply_Instance_Against_Trigger_1.save()
                    Thread(target=save_chat_tokens, args=(prompt, content, Reply_Instance_Against_Trigger_1)).start()
                    _, reply_json = Reply.get_reply_by_id(
                        id=Reply_Instance_Against_Trigger_1.id
                    )
                    yield self.arrange_response_to_yield(
                        query_id=Query_Instance.id,
                        reply_json=reply_json,
                    )
                    print("=====================")
                    print("Done")
                    print("=====================")
                    Thread(
                        target=self.handle_trigger,
                        args=(
                            trigger_number,
                            Query_Instance.query,
                            content,
                        ),
                    ).start()
                else:
                    continue

    def append_reply_in_history(self, reply):
        self.ChatInstance.scope["_Query_History"] = (
            f"query={self.ChatInstance.scope['_Query_Instance'].query}\n"
        )
        self.ChatInstance.scope["_Query_History"] = f"reply={reply}"

    def arrange_response_to_yield(
        self, query_id: int, reply_json, completed: bool = False
    ):
        return {
            "type": settings.WEBSOCKET_EVENT_TYPES.QUERY_AND_REPLY.value,
            "data": {
                "query_id": query_id,
                "reply": reply_json,
                "is_completed": completed,
            },
        }

    def send_response_to_user(self, json_response):
        print(f"Sending response to user: {json_response}")

        self.ChatInstance.send(text_data=json.dumps(json_response))

        if (
            json_response.get("type")
            == settings.WEBSOCKET_EVENT_TYPES.QUERY_AND_REPLY.value
        ):
            data = json_response.get("data")
            is_completed = data.get("is_completed")
            reply_json = data.get("reply")
            if (
                reply_json.get("type") == ReplyType.TEXT.value
                or reply_json.get("type") == ReplyType.BRIEF.value
            ) and is_completed:
                self.send_system_easy_trigger()
        elif (
            json_response.get("type")
            == settings.WEBSOCKET_EVENT_TYPES.COURTLISTENER_SEARCH.value
        ):
            self.send_system_easy_trigger()

    def send_system_easy_trigger(self):
        self.ChatInstance.send(
            text_data=json.dumps(
                {
                    "type": settings.WEBSOCKET_EVENT_TYPES.SYSTEM_EASY.value,
                    "data": None,
                }
            )
        )

    def send_system_busy_trigger(self):
        self.ChatInstance.send(
            text_data=json.dumps(
                {
                    "type": settings.WEBSOCKET_EVENT_TYPES.SYSTEM_BUSY.value,
                    "data": None,
                }
            )
        )

    def extract_trigger_number(self, content):
        match = re.search(r"&&(\d+)&&", content)
        if match:
            extracted_trigger_number = match.group(1)
            return extracted_trigger_number
        else:
            return None

    def remove_trigger_number(self, content):
        return re.sub(r"&&\d+&&", "", content)

    def handle_trigger(self, trigger, query, content):
        _GptTrigger = GptTrigger(trigger, content)
        print("Going to execute further logic")
        if trigger == "1":
            print("Trigger # 1 ")
        elif trigger == "2":
            print("Trigger # 2")
        elif trigger == "4":
            print("Trigger # 4")
        else:
            self.handle(Gpt_Trigger=_GptTrigger)

    def stream(self, prompt) -> Generator:
        q = Queue()
        job_done = object()
        language_model = OpenAI(
            streaming=True,
            callbacks=[QueueCallback(q)],
            temperature=0,
            model_name=self.model_name,
        )

        def task():
            language_model(prompt)
            q.put(job_done)

        t = Thread(target=task)
        t.start()
        content = ""
        while True:
            try:
                next_token = q.get(True, timeout=1)
                if next_token is job_done:
                    yield "", content, True
                    break
                content += next_token
                yield next_token, content, False
            except Empty:
                continue

    def generate_prompt(
        self,
        user_query,
        chat_history,
        query_data_from_vdb,
        query_data_from_user_docs,
        requested_data_from_vdb,
        requested_data_from_user_docs,
        requested_data_from_us_constitution,
        history_of_triggers=[],
    ):
        try:
            prompt = f"""
                You are LegalAI Bot, You help lawyers in research related to their legal documents and briefs. 
                Helping in research for Drafting/Creating Legal Documents e.g Briefs is you primary purpose.
                User Query = {user_query},
                This is your current conversation history = {chat_history}. 
                Info from internal Vector DB regarding Query= {query_data_from_vdb}
                Info from documents uploaded by User regarding Query= {query_data_from_user_docs}
                Info from internal Vector DB requested by You = {requested_data_from_vdb}
                Info from documents requested by You = {requested_data_from_user_docs}
                Info from us constitution requested by You = {requested_data_from_us_constitution}
                History of Triggers by you ={history_of_triggers}

                Instrucion regarding the Reply are that you need to find information from multiple sources to support the case of user, for this, system has following:
                System has large vector database that holds info regarding legal documents , references , court briefs and more. 
                System also has a vector database for US Constitution Document.
                System also ask users to upload/provide more information regarding the Brief Document to be generated.

                Now when the convesation starts, you greet and try to converse user into giving you basic information about his case.
                Then you will start looking into System Vector DB, US Constitution DB and User Documents if provided and answer to questions/queires of user.

                If you require additional information from our internal Vector DB of Court Breifes and Histories and Opinions, or user is asking for citations or references or past cases
                Reply with &&1&& and max 2 search keywords for db.
                If you require additional information from documents uploaded by user or when user asks info from them and that infor is not provided to you then
                Reply with &&2&& and search query for Similarity Search, if this query is for searching info for court brief, then return many search query for each section.
                If you want to send response after you are confident that your reply is what user is looking for then
                Reply with &&3&& and your reply for user.
                If user asks some query related to US Constitution and you need solid information from constitution then
                Reply with &&4&& and search query for US Constitution Document

                Use your personality and additional info to generate response.Give reply in the query language, in native script.
                Remember to reply with correct trigger (from system vector db (max 2 keywords), from docs uploaded by user or from US Constituion Vector DB),
                Remember to reply with trigger if you do not have information to reply for User Query.
                Remember that replies for user must be short and engaging. Because it is a conversation
                Remember to reply after thinking hard and make sure that reply is correct and short like back and forth conversation is happening. 
                And remember to not trigger many times if you do not find what you need.
                """
            return prompt
        except Exception as e:
            print(e)
            return None

    def get_title_of_chat(self, query: str):
        prompt = f"""
        Messages from user are [{query}]
        I need you to analyze messages and return a Title of Conversation. 
        The title should not be longer than 6 Words. 
        Remember , to generate accurate titles within 6 words length limit
        """
        llm = OpenAI(model_name=self.model_name)
        res = llm(prompt)
        return res

    def handle(self, Gpt_Trigger: GptTrigger = None):
        print("Going to Handle Conversation")
        query = self.ChatInstance.scope["_Query_Instance"].query
        history = self.ChatInstance.scope["_Query_History"]
        if (
            self.ChatInstance.scope["_Chat_Instance"].title == ""
            or self.ChatInstance.scope["_Chat_Instance"].title == "New Chat"
        ):
            self.ChatInstance.scope["_Chat_Instance"].title = self.get_title_of_chat(
                query=query
            )
            self.ChatInstance.scope["_Chat_Instance"].save()
        query_data_from_vdb = None
        query_data_from_user_docs = None
        requested_data_from_vdb = None
        requested_data_from_user_docs = None
        requested_data_from_us_constitution = None

        if Gpt_Trigger is not None:
            print("==========================================")
            print("INSIDE PIPELINE OF TRIGGER NUMBER : ", Gpt_Trigger.TriggerNumber)
            print("==========================================")
            if Gpt_Trigger.TriggerNumber == "1":
                self.ChatInstance.scope["gpt_triggers_history"].append(
                    f"&&1&& {Gpt_Trigger.TriggerContent}"
                )
                search_result = courtlistener_search(Gpt_Trigger.TriggerContent)
                response_json = {
                    "type": settings.WEBSOCKET_EVENT_TYPES.COURTLISTENER_SEARCH.value,
                    "data": search_result,
                }
                self.send_response_to_user(response_json)
                return
            elif Gpt_Trigger.TriggerNumber == "2":
                self.ChatInstance.scope["gpt_triggers_history"].append(
                    f"&&2&& {Gpt_Trigger.TriggerContent}"
                )
                query_sources = GetDocsFromVectorDB(
                    hf,
                    Gpt_Trigger.TriggerContent,
                    False,
                    db_path=os.path.join(
                        settings.USER_DOCUMENTS__VECTOR_DB_PATH,
                        str(self.ChatInstance.scope["user"].profile.indexUUID),
                        settings.VECTOR_DB_PERSIST_STORAGE,
                    ),
                )
                if len(query_sources) > 0:
                    query_data_from_user_docs = Source.save_sources_list(
                        query_instance=self.ChatInstance.scope["_Query_Instance"],
                        sources_list=query_sources,
                    )
                else:
                    query_data_from_user_docs = "Data not found in Documents Uploaded by User, please try a different search query"

            elif Gpt_Trigger.TriggerNumber == "4":
                self.ChatInstance.scope["gpt_triggers_history"].append(
                    f"&&4&& {Gpt_Trigger.TriggerContent}"
                )
                history += f"query={query}, reply={Gpt_Trigger.TriggerContent},\n"
                query_sources = GetDocsFromVectorDB(
                    hf,
                    query,
                    False,
                    db_path=os.path.join(
                        settings.US_CONSTITUTION_VECTOR_DB_PATH,
                        settings.VECTOR_DB_PERSIST_STORAGE,
                    ),
                )
                if query_sources:
                    requested_data_from_us_constitution = Source.save_sources_list(
                        query_instance=self.ChatInstance.scope["_Query_Instance"],
                        sources_list=query_sources,
                    )
                    print("Data from US Constitution Vector DB :")
                    print(requested_data_from_us_constitution)

        prompt = self.generate_prompt(
            user_query=query,
            chat_history=history,
            query_data_from_vdb=query_data_from_vdb,
            query_data_from_user_docs=query_data_from_user_docs,
            requested_data_from_vdb=requested_data_from_vdb,
            requested_data_from_user_docs=requested_data_from_user_docs,
            requested_data_from_us_constitution=requested_data_from_us_constitution,
            history_of_triggers=self.ChatInstance.scope["gpt_triggers_history"],
        )
        for json_response in self.generate_stream(
            Query_Instance=self.ChatInstance.scope["_Query_Instance"],
            prompt=prompt,
        ):
            self.send_response_to_user(json_response)

    def handle_citations(self):
        print("Going to Handle Opinion Citations")
        length_of_selected_opinions = len(self.ChatInstance.scope["_Selected_Opinions"])
        for idx in range(length_of_selected_opinions):
            opinion_id = self.ChatInstance.scope["_Selected_Opinions"][idx]
            opinion = court_listener_opinion(opinion_id)
            prompt = f"""
            You are a Legal AI Assistant. Who is experenced in drafting Court Brief. User selects some old opinions to build his argument for his court brief.
            You analyze data of past opinions of the Courts and see how we can use/cite that opinion in our case (court brief). 
            You analyze the opinion deep and hard, and find the points that can be used in favour of arguments of our case. 
            I will give you history of chat of user discussing his case , building arguments and more. 
            You will analyze the chat, analyze the past opinion and build a argument to support the cause/brief of user.
            History of User Chat ={self.ChatInstance.scope["_Query_History"]}
            Name of the Case to Cite From = {opinion["case_name"]}
            Filing Date of the Case to Cite From = {opinion["date_filed"]}
            Summary of Old Opinion/Case to Cite From ={opinion["content_summary"]}

            Remeber, that you have to act like a lawyer, You have to build arguments in favor of your case, court brief. So, you work hard and smart to come up 
            with solutions by analyzing post opinion. Remeber to generate a single paragraph that will hold one argument and its legal basis and citation of the
            above opinion to cite from.
            """
            llm = OpenAI(model_name="gpt-3.5-turbo-16k")
            res = llm(prompt)
            print(opinion)
            selected_opinion = SelectedOpinion.save_selected_opinion(
                user=self.ChatInstance.scope["user"],
                chat=self.ChatInstance.scope["_Chat_Instance"],
                opinion_id=opinion_id,
                case_name=opinion["case_name"],
                absolute_url=opinion["absolute_url"],
                court_name=opinion["court"].get("full_name"),
                date_filed=opinion["date_filed"],
                status=opinion["status"],
                citations=opinion["citations"],
                summary=opinion["content_summary"],
                docket_reference=opinion["docket"].get("number"),
                generated_argument=res,
            )
            selected_opinion_json = SelectedOpinion.convert_to_dict(selected_opinion)

            _Reply, _Reply_JSON = Reply.save_reply(
                self.ChatInstance.scope["_Query_Instance"],
                ReplyType.ARGUMENT_FROM_OPINION.value,
                selected_opinion_json,
            )
            Thread(target=save_chat_tokens, args=(prompt, res, _Reply)).start()
            json_response = self.arrange_response_to_yield(
                query_id=self.ChatInstance.scope["_Query_Instance"].id,
                reply_json=_Reply_JSON,
                completed=True if idx == length_of_selected_opinions - 1 else False,
            )
            self.send_response_to_user(json_response)


class QueueCallback(BaseCallbackHandler):
    """Callback handler for streaming LLM responses to a queue."""

    def __init__(self, q):
        self.q = q

    def on_llm_new_token(self, token: str, **kwargs: any) -> None:
        self.q.put(token)

    def on_llm_end(self, *args, **kwargs: any) -> None:
        return self.q.empty()
        # self.q.put(None)
