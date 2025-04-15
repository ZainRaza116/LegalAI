import os
import re
import json
from typing import List
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
    UserBrief,
    BriefArguments,
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


class CortBriefBot:
    def __init__(self, _ChatInstance) -> None:
        from bot.django_channels.court_brief_consumer import CourtBriefConsumer

        os.environ["OPENAI_API_KEY"] = settings.OPENAI_KEY
        self.ChatInstance: CourtBriefConsumer = _ChatInstance
        self.model_name = settings.PRIMARY_MODEL

    def generate_stream(
        self,
        Query_Instance: Query,
        prompt: str,
    ):
        print("Going to Generate Response Stream")
        trigger_found_flag = False
        trigger_number = None
        first_and_and_flag = False
        trigger_number_flag_after_first_and_and = False
        trigger_number_removal_flag = False

        Reply_Instance_Against_Trigger_11 = None
        Reply_Instance_Against_Trigger_10 = None
        Reply_Instance_Against_Trigger_9 = None
        Reply_Instance_Against_Trigger_8 = None
        Reply_Instance_Against_Trigger_7 = None
        Reply_Instance_Against_Trigger_6 = None
        Reply_Instance_Against_Trigger_5 = None
        Reply_Instance_Against_Trigger_4 = None
        Reply_Instance_Against_Trigger_3 = None
        Reply_Instance_Against_Trigger_2 = None
        Reply_Instance_Against_Trigger_1 = None

        for next_token, content, job_done in self.stream(prompt):
            print(next_token)
            # print(content)
            # print(content)
            if not trigger_found_flag:
                # Check if the response contains a trigger (&&1&&, &&2&&, &&3&&)
                trigger_1_index = content.find("&&1&&")
                trigger_2_index = content.find("&&2&&")
                trigger_3_index = content.find("&&3&&")
                trigger_4_index = content.find("&&4&&")
                trigger_5_index = content.find("&&5&&")
                trigger_6_index = content.find("&&6&&")
                trigger_7_index = content.find("&&7&&")
                trigger_8_index = content.find("&&8&&")
                trigger_9_index = content.find("&&9&&")
                trigger_10_index = content.find("&&10&&")
                trigger_11_index = content.find("&&11&&")

                if (
                    trigger_1_index != -1
                    or trigger_2_index != -1
                    or trigger_3_index != -1
                    or trigger_4_index != -1
                    or trigger_5_index != -1
                    or trigger_6_index != -1
                    or trigger_7_index != -1
                    or trigger_8_index != -1
                    or trigger_9_index != -1
                    or trigger_10_index != -1
                    or trigger_11_index != -1
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

            if trigger_number == "11":
                if Reply_Instance_Against_Trigger_11 is None:
                    Reply_Instance_Against_Trigger_11, _ = Reply.save_reply(
                        Query_Instance,
                        ReplyType.LLM_ACTION.value,
                        {
                            "trigger_number": trigger_number,
                            "trigger_content": "",
                            "message": "",
                        },
                    )
                if job_done:
                    Reply_Instance_Against_Trigger_11.value = {
                        "trigger_number": trigger_number,
                        "trigger_content": "",
                        "message": content,
                    }
                    Reply_Instance_Against_Trigger_11.save()
                    Thread(
                        target=save_chat_tokens,
                        args=(prompt, content, Reply_Instance_Against_Trigger_11),
                    ).start()
                    _, reply_json = Reply.get_reply_by_id(
                        id=Reply_Instance_Against_Trigger_11.id
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

            if trigger_number == "10":
                if Reply_Instance_Against_Trigger_10 is None:
                    reply_json = None
                    Reply_Instance_Against_Trigger_10, reply_json = Reply.save_reply(
                        Query_Instance,
                        ReplyType.LLM_ACTION.value,
                        {
                            "trigger_number": trigger_number,
                            "trigger_content": "",
                            "message": "",
                        },
                    )
                if job_done:
                    Reply_Instance_Against_Trigger_10.value = {
                        "trigger_number": trigger_number,
                        "trigger_content": "",
                        "message": content,
                    }
                    Reply_Instance_Against_Trigger_10.save()
                    Thread(
                        target=save_chat_tokens,
                        args=(prompt, content, Reply_Instance_Against_Trigger_10),
                    ).start()
                    _, reply_json = Reply.get_reply_by_id(
                        id=Reply_Instance_Against_Trigger_10.id
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
                    reply_json["value"]["message"] = next_token
                    yield self.arrange_response_to_yield(
                        query_id=Query_Instance.id, reply_json=reply_json
                    )
                    continue

            if trigger_number == "9":
                if Reply_Instance_Against_Trigger_9 is None:
                    reply_json = None
                    Reply_Instance_Against_Trigger_9, reply_json = Reply.save_reply(
                        Query_Instance,
                        ReplyType.LLM_ACTION.value,
                        {
                            "trigger_number": trigger_number,
                            "trigger_content": "",
                            "message": "",
                        },
                    )
                if job_done:
                    Reply_Instance_Against_Trigger_9.value = {
                        "trigger_number": trigger_number,
                        "trigger_content": "",
                        "message": content,
                    }
                    Reply_Instance_Against_Trigger_9.save()
                    Thread(
                        target=save_chat_tokens,
                        args=(prompt, content, Reply_Instance_Against_Trigger_9),
                    ).start()
                    _, reply_json = Reply.get_reply_by_id(
                        id=Reply_Instance_Against_Trigger_9.id
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
                    reply_json["value"]["message"] = next_token
                    yield self.arrange_response_to_yield(
                        query_id=Query_Instance.id, reply_json=reply_json
                    )
                    continue

            if trigger_number == "8":
                if Reply_Instance_Against_Trigger_8 is None:
                    reply_json = None
                    Reply_Instance_Against_Trigger_8, reply_json = Reply.save_reply(
                        Query_Instance,
                        ReplyType.LLM_ACTION.value,
                        {
                            "trigger_number": trigger_number,
                            "trigger_content": "",
                            "message": "",
                        },
                    )
                if job_done:
                    Reply_Instance_Against_Trigger_8.value = {
                        "trigger_number": trigger_number,
                        "trigger_content": "",
                        "message": content,
                    }
                    Reply_Instance_Against_Trigger_8.save()
                    Thread(
                        target=save_chat_tokens,
                        args=(prompt, content, Reply_Instance_Against_Trigger_8),
                    ).start()
                    _, reply_json = Reply.get_reply_by_id(
                        id=Reply_Instance_Against_Trigger_8.id
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
                    reply_json["value"]["message"] = next_token
                    yield self.arrange_response_to_yield(
                        query_id=Query_Instance.id, reply_json=reply_json
                    )
                    continue

            if trigger_number == "7":
                if Reply_Instance_Against_Trigger_7 is None:
                    reply_json = None
                    Reply_Instance_Against_Trigger_7, reply_json = Reply.save_reply(
                        Query_Instance,
                        ReplyType.LLM_ACTION.value,
                        {
                            "trigger_number": trigger_number,
                            "trigger_content": "",
                            "message": "",
                        },
                    )
                if job_done:
                    Reply_Instance_Against_Trigger_7.value = {
                        "trigger_number": trigger_number,
                        "trigger_content": "",
                        "message": content,
                    }
                    Reply_Instance_Against_Trigger_7.save()
                    Thread(
                        target=save_chat_tokens,
                        args=(prompt, content, Reply_Instance_Against_Trigger_7),
                    ).start()
                    _, reply_json = Reply.get_reply_by_id(
                        id=Reply_Instance_Against_Trigger_7.id
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
                    reply_json["value"]["message"] = next_token
                    yield self.arrange_response_to_yield(
                        query_id=Query_Instance.id, reply_json=reply_json
                    )
                    continue

            if trigger_number == "6":
                if Reply_Instance_Against_Trigger_6 is None:
                    reply_json = None
                    Reply_Instance_Against_Trigger_6, reply_json = Reply.save_reply(
                        Query_Instance,
                        ReplyType.LLM_ACTION.value,
                        {
                            "trigger_number": trigger_number,
                            "trigger_content": "",
                            "message": "",
                        },
                    )
                if job_done:
                    Reply_Instance_Against_Trigger_6.value = {
                        "trigger_number": trigger_number,
                        "trigger_content": "",
                        "message": content,
                    }
                    Reply_Instance_Against_Trigger_6.save()
                    Thread(
                        target=save_chat_tokens,
                        args=(prompt, content, Reply_Instance_Against_Trigger_6),
                    ).start()
                    _, reply_json = Reply.get_reply_by_id(
                        id=Reply_Instance_Against_Trigger_6.id
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
                    reply_json["value"]["message"] = next_token
                    yield self.arrange_response_to_yield(
                        query_id=Query_Instance.id, reply_json=reply_json
                    )
                    continue

            if trigger_number == "5":
                if Reply_Instance_Against_Trigger_5 is None:
                    reply_json = None
                    Reply_Instance_Against_Trigger_5, reply_json = Reply.save_reply(
                        Query_Instance,
                        ReplyType.LLM_ACTION.value,
                        {
                            "trigger_number": trigger_number,
                            "trigger_content": "",
                            "message": "",
                        },
                    )
                if job_done:
                    Reply_Instance_Against_Trigger_5.value = {
                        "trigger_number": trigger_number,
                        "trigger_content": "",
                        "message": content,
                    }
                    Reply_Instance_Against_Trigger_5.save()
                    Thread(
                        target=save_chat_tokens,
                        args=(prompt, content, Reply_Instance_Against_Trigger_5),
                    ).start()
                    _, reply_json = Reply.get_reply_by_id(
                        id=Reply_Instance_Against_Trigger_5.id
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
                    reply_json["value"]["message"] = next_token
                    yield self.arrange_response_to_yield(
                        query_id=Query_Instance.id, reply_json=reply_json
                    )
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
                    Thread(
                        target=save_chat_tokens,
                        args=(prompt, content, Reply_Instance_Against_Trigger_4),
                    ).start()
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
                    Thread(
                        target=save_chat_tokens,
                        args=(prompt, content, Reply_Instance_Against_Trigger_3),
                    ).start()

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
                    Thread(
                        target=save_chat_tokens,
                        args=(prompt, content, Reply_Instance_Against_Trigger_2),
                    ).start()
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
                    Thread(
                        target=save_chat_tokens,
                        args=(prompt, content, Reply_Instance_Against_Trigger_1),
                    ).start()
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

        if trigger == "5":
            print("Trigger # 5")
            self.handle_cover_page_generation(Gpt_Trigger=_GptTrigger)
        elif trigger == "6":
            print("Trigger # 6")
            self.handle_questions_generation(Gpt_Trigger=_GptTrigger)
        elif trigger == "7":
            print("Trigger # 7")
            self.handle_statement_generation(Gpt_Trigger=_GptTrigger)
        elif trigger == "8":
            print("Trigger # 8")
            self.handle_arguments_generation(Gpt_Trigger=_GptTrigger)
        elif trigger == "9":
            print("Trigger # 9")
            self.handle_summary_generation(Gpt_Trigger=_GptTrigger)
        elif trigger == "10":
            print("Trigger # 10")
            self.handle_conclusion_generation(Gpt_Trigger=_GptTrigger)
        elif trigger == "11":
            print("Trigger # 11")
            self.handle_document_generation(Gpt_Trigger=_GptTrigger)

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
        list_of_generated_sections=[],
    ):
        try:
            prompt = f"""
                You are LegalAI Bot, You help lawyers to draft their legal documents and briefs. 
                Drafting/Creating Legal Documents e.g Briefs is you primary purpose.
                User Query = {user_query},
                This is your current conversation history = {chat_history}. 
                Info from internal Vector DB regarding Query= {query_data_from_vdb}
                Info from documents uploaded by User regarding Query= {query_data_from_user_docs}
                Info from internal Vector DB requested by You = {requested_data_from_vdb}
                Info from documents requested by You = {requested_data_from_user_docs}
                Info from us constitution requested by You = {requested_data_from_us_constitution}
                History of Triggers by you ={history_of_triggers}
                Here are the pages/sections of brief document that system has already generated : {list_of_generated_sections}

                Instrucion regarding the Reply:
                Your primary purpose is to generate brief document which has multiple sections/pages. 
                User can ask you to generate whole document at once or generate/revise single section in one go.
                Following are different sections/pages of brief document:
                1. Cover Page (it has court name, court term, petitioner name, respondent name, brief title, and submitting entities)
                2. Questions Presented (this page is part of brief where we write questions that we later address in brief, it is list of questions)
                3. Table of Authorities (this page has list of references to past cases similar to our case for which user is generating document)
                4. Statement of Case (this page/section has multiple paragraphs that describe in detail what the case is about)
                5. Arguments of Case (this section that is spread across multiple pages holds all the arguments of case)
                6. Summary of Arguments (this page/section has summary of arguments )
                7. Conclusion (this page/section has overall conclusion )

                You need to find information from multiple sources to support the case of user, for this, system has following:
                System has large vector database that holds info regarding legal documents , references ,
                court briefs and more. 
                System also has a vector database for US Constitution Document.
                System also ask users to upload/provide more information regarding the Brief Document to be generated.

                Now when the convesation starts, you greet and try to converse user into giving you basic information about his case.
                User must provide statment of the case, then User can choose or tell you to rewrite
                Questions presented- you will ask user to provide questions and also user can tell you to generate questions  
                Based on the information you have and also on the request of user, you start generating document.

                If you require additional information from our internal Vector DB of Court Breifes and Histories and Opinions, or user is asking for citations or references or past cases
                Reply with &&1&& and max 2 search keywords for db.
                If you require additional information from documents uploaded by user or when user asks info from them and that infor is not provided to you then
                Reply with &&2&& and search query for Similarity Search, if this query is for searching info for court brief, then return many search query for each section.
                If you want to send response after you are confident that your reply is what user is looking for then
                Reply with &&3&& and your reply for user.
                If user asks some query related to US Constitution and you need solid information from constitution then
                Reply with &&4&& and search query for US Constitution Document


                Now lets understand the rules/procedure of Document Generation.
                
                When you have basic information or information about the Cover Page of Brief
                Then Reply with &&5&& and a short message for user that system is generating Cover Page based on information provided/found.
                
                When you think that user has discussed enough questions/problems and system should generate Questions Presented Section
                Then Reply with &&6&& and a short message for user that system is going to generate Questions Presented part of Brief
                
                When you think that you have enough information and system should generate Statement of The Case in detail 
                Then Reply with &&7&& and a short message for user that system is generating statement of the case.
                
                When you think that you have or user has browsed enough references from past cases and system can now generate as many arguments as possible
                Then Reply with &&8&& and a short message for user that system is generating Arguments of case.
                
                When system has generated arguments of case or user asks you to generate summary of arguments 
                Then Reply with &&9&& and a short message for user that system is generating Summary of arguments
                
                When all the above sections are generated and now system should generate Conclusion of Brief 
                Then Reply with &&10&& and a short message for user that system is generating conclusion of Brief.

                If user is asking to revise/generate full document at once , all the sections of document, 
                Then Reply with &&11&& and a short message for user that system is generating/revising Full Document.

                Use your personality and additional info to generate response.Give reply in the query language, in native script.
                Remember to reply with correct trigger (from system vector db (max 2 keywords), from docs uploaded by user or from US Constituion Vector DB),
                Remember to reply with trigger if you do not have information to reply for User Query.
                Remember to trigger generation of different sections of document once you are confident that you have necessary information because this trigger initiates the docuemnt generation pipeline.
                Remeber that for the sections that are already generated, trigger their generation/updation only when user specifically asks in query. 
                Also remember that user can ask full document generatin, so trigger full document generation.
                Remember that replies for user must be short and engaging. Because it is a conversation. And also for the replies about document generation, keep them short too. Real short.
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

    def handle_cover_page_generation(self, Gpt_Trigger: GptTrigger = None):
        print("Going to handle generation of cover page")
        print(Gpt_Trigger.TriggerContent)
        prompt = f"""
        You are a Legal AI Assistant. Who is experenced in drafting Court Brief.You convert text data into structured JSON. 
        You analyze the text and put the respective value into JSON Field after Reasoning.
        This is the Chat History of User with another AI : {self.ChatInstance.scope["_Query_History"]}
        This is the Current Query of User : {self.ChatInstance.scope["_Query_Instance"].query}

        Understand the data and convert it into JSON of following structure:
        {{
            "court_name": "",
            "court_term": "e.g Spring Term 2021",
            "petitioner_name": "",
            "respondent_name": "",
            "title_of_brief": "",
            "submitting_entity":"",
            "attorneys":[]
        }}

        Remember tho analyze hard, and find out value for each field. 
        Remeber to find hard the values of submitting entities, these are the names of attorneys/entites of petitioner, if it is petitiner/user itself then use his name.
        Remember that the attorneys string array must have names of attorneys of respondent for this brief .You must not leave this array empty.
        Remeber that the attorneys is a string array of names of attorneys of the respondent . Find them from the chat history.
        If you do not find any value for certain fields then do not keep it empty, put some value in it.
        Remember, you only reply JSON, you do not talk other than JSON. Again, only reply in JSON string of above structure.
        """
        llm = OpenAI(model_name=self.model_name)
        res = llm(prompt)
        parsed_response = json.loads(res)
        user_biref_instance, _ = UserBrief.objects.get_or_create(
            user=self.ChatInstance.scope["user"],
            chat=self.ChatInstance.scope["_Chat_Instance"],
        )

        user_biref_instance.court_name = parsed_response.get("court_name", "")
        user_biref_instance.court_term = parsed_response.get("court_term", None)
        user_biref_instance.petitioner_name = parsed_response.get(
            "petitioner_name", None
        )
        user_biref_instance.respondent_name = parsed_response.get(
            "respondent_name", None
        )
        user_biref_instance.title_of_brief = parsed_response.get("title_of_brief", None)
        user_biref_instance.submitting_entity = parsed_response.get(
            "submitting_entity", None
        )
        user_biref_instance.attorneys = parsed_response.get("attorneys", None)
        user_biref_instance.save()

        reply_instance, reply_json = Reply.save_reply(
            self.ChatInstance.scope["_Query_Instance"],
            ReplyType.BRIEF.value,
            {
                "message": "Cover Page of Brief has been Generated/Updated",
                "brief_data": UserBrief.convert_to_dict(
                    user_brief_instance=user_biref_instance
                ),
            },
        )
        Thread(target=save_chat_tokens, args=(prompt, res, reply_instance)).start()
        json_response = self.arrange_response_to_yield(
            query_id=self.ChatInstance.scope["_Query_Instance"].id,
            reply_json=reply_json,
            completed=True,
        )
        self.send_response_to_user(json_response)
        print("Cover Page of Brief Document is updated")

    def handle_questions_generation(self, Gpt_Trigger: GptTrigger = None):
        print("Going to handle generation of questions page")
        print(Gpt_Trigger.TriggerContent)
        prompt = f"""
        You are a Legal AI Assistant. Who is experenced in drafting Court Brief.You convert text data into structured JSON. 
        You analyze the text and put the respective value into JSON Field after Reasoning.
        This is the Chat History of User with another AI : {self.ChatInstance.scope["_Query_History"]}
        This is the Current Query of User : {self.ChatInstance.scope["_Query_Instance"].query}
        
        You need to generate as many questions as reasonable by understanding the Chat History . 
        These questions will be presented to a court via Court Brief. 
        The Quetions must be reasonalbe and they must have a legal perspective. 
        These Questions must be appealing to a court and logical, legal and reasonable at same time.
        

        Understand the data and generate questions and put them into JSON of following structure:
        {{
            "questions_presented":[],
        }}

        Remember tho analyze hard, and generate array of questions (array of strings) from understading chat history.
        Remember to find hard the questions that can be presented to a court in court brief. You must also generate questions yourself 
        after analyzing the case from chat history. And you do not need to proivide the numbering of questions.. just put question strings in array without number.
        Front-End will apply numbering by itself, so you are to only generate question strings.
        Remember, you only reply JSON string, you do not talk other than JSON. The array of questions_presented will be parsed, it should not throw error.
        The JSON string that you will generate will be parsed directly by the system , it should not throw error. Return Json string of above structure.
        """
        llm = OpenAI(model_name=self.model_name)
        res = llm(prompt)
        parsed_response = json.loads(res)
        user_biref_instance, _ = UserBrief.objects.get_or_create(
            user=self.ChatInstance.scope["user"],
            chat=self.ChatInstance.scope["_Chat_Instance"],
        )

        user_biref_instance.questions_presented = parsed_response.get(
            "questions_presented", ""
        )
        user_biref_instance.save()
        reply_instance, reply_json = Reply.save_reply(
            self.ChatInstance.scope["_Query_Instance"],
            ReplyType.BRIEF.value,
            {
                "message": "Questions Presented Page of Brief has been Generated/Updated",
                "brief_data": UserBrief.convert_to_dict(
                    user_brief_instance=user_biref_instance
                ),
            },
        )
        Thread(target=save_chat_tokens, args=(prompt, res, reply_instance)).start()
        json_response = self.arrange_response_to_yield(
            query_id=self.ChatInstance.scope["_Query_Instance"].id,
            reply_json=reply_json,
            completed=True,
        )
        self.send_response_to_user(json_response)
        print("Questions Presented  Page of Brief Document is updated")

    def handle_statement_generation(self, Gpt_Trigger: GptTrigger = None):
        print("Going to handle generation of statement page")
        print(Gpt_Trigger.TriggerContent)
        prompt = f"""
        You are a Legal AI Assistant. Who is experenced in drafting Court Brief.You convert text data into structured JSON. 
        You analyze the text and put the respective value into JSON Field after Reasoning.
        This is the Chat History of User with another AI : {self.ChatInstance.scope["_Query_History"]}
        This is the Current Query of User : {self.ChatInstance.scope["_Query_Instance"].query}
        
        You need to generate Statement of the Case after analyzing the Chat History and analyzing it hard.
        You must put each paragraph as seperate element in array of strings.Length of statement_of_case must be atleast 3. One element for each paragraph.
        You must generate reasonable paragrapsh for Satement for the Court Brief Document. 
        You must activate your legal mode and make the paragrapshs of statement appealing to a court so that court can rule as user wants. 

        Understand the data and generate paragrapshs for statement of the case and put it into array of strings in JSON of following structure:
        {{
            "statement_of_case":[],
        }}

        Remember to analyze hard, and generate atleaset 3 paragraphs for statement of the case. You can generate as many paragrphs you want but be reasonable. 
        Now Remember, you only reply JSON, you do not talk other than JSON. Again, only reply in JSON string of above structure.
        """
        llm = OpenAI(model_name=self.model_name)
        res = llm(prompt)
        print(res)
        parsed_response = json.loads(res)
        print(parsed_response)
        user_biref_instance, _ = UserBrief.objects.get_or_create(
            user=self.ChatInstance.scope["user"],
            chat=self.ChatInstance.scope["_Chat_Instance"],
        )

        user_biref_instance.statement_of_case = parsed_response.get(
            "statement_of_case", ""
        )
        user_biref_instance.save()
        reply_instance, reply_json = Reply.save_reply(
            self.ChatInstance.scope["_Query_Instance"],
            ReplyType.BRIEF.value,
            {
                "message": "Statement of Brief has been Generated/Updated",
                "brief_data": UserBrief.convert_to_dict(
                    user_brief_instance=user_biref_instance
                ),
            },
        )
        Thread(target=save_chat_tokens, args=(prompt, res, reply_instance)).start()
        json_response = self.arrange_response_to_yield(
            query_id=self.ChatInstance.scope["_Query_Instance"].id,
            reply_json=reply_json,
            completed=True,
        )
        self.send_response_to_user(json_response)
        print("Statement Page of Brief Document is updated")

    def handle_arguments_generation(self, Gpt_Trigger: GptTrigger = None):
        print("Going to handle generation of arguments page")
        print(Gpt_Trigger.TriggerContent)
        prompt = f"""
        You are a Legal AI Assistant. Who is experenced in drafting Court Brief.You convert text data into structured JSON. 
        You are expert/Geek of making/drafting arguments related to legal matter and arguments of Court Brief. You are the 
        best lawyer and you know your game. You know how to generate and put arguments in front of a judge and in the brief.

        Now You have to analyze the text and put the respective value into JSON Field after Reasoning.
        This is the Chat History of User with another AI : {self.ChatInstance.scope["_Query_History"]}
        This is the Current Query of User : {self.ChatInstance.scope["_Query_Instance"].query}
        
        You need to generate As many arguments as possible after analyzing the Chat History.
        In chat history there might be arguments made by another AI using references of past case.
        You need to also utlize those arguemnts as well, and create new one. User must win this case.

        Understand the data and generate arguments and put them into JSON of following structure:
        {{
            "arguments_of_case": [
                {{
                "title": "value of argument title/heading",
                "description": "value of argument description"
                }}
            ],
        }}

        Remember to analyze hard.
        Now Remember, you only reply JSON, you do not talk other than JSON. Again, only reply in JSON string of above structure.
        """
        llm = OpenAI(model_name=self.model_name)
        res = llm(prompt)
        parsed_response = json.loads(res)

        user_biref_instance, _ = UserBrief.objects.get_or_create(
            user=self.ChatInstance.scope["user"],
            chat=self.ChatInstance.scope["_Chat_Instance"],
        )
        arguments_of_brief = parsed_response.get("arguments_of_case", None)
        (
            reply_instance_for_successfull_generation_of_arguments,
            reply_json_for_successfull_generation_of_arguments,
        ) = Reply.save_reply(
            self.ChatInstance.scope["_Query_Instance"],
            ReplyType.LLM_ACTION.value,
            {
                "trigger_number": 8,
                "trigger_content": "",
                "message": f"System has successfully generated {len(arguments_of_brief)} arguments, but now system is enhancing arguments.",
            },
        )
        Thread(
            target=save_chat_tokens,
            args=(prompt, res, reply_instance_for_successfull_generation_of_arguments),
        ).start()
        self.send_response_to_user(
            self.arrange_response_to_yield(
                query_id=self.ChatInstance.scope["_Query_Instance"].id,
                reply_json=reply_json_for_successfull_generation_of_arguments,
            )
        )

        # Fetch Past Cases selected for this Brief Chat, then pass these cases to argument enhancer
        selected_past_cases_or_opinions = SelectedOpinion.objects.filter(
            chat=self.ChatInstance.scope["_Chat_Instance"]
        )
        selected_past_cases_list = []
        if selected_past_cases_or_opinions:
            for selected_past_case in selected_past_cases_or_opinions:
                selected_past_cases_list.append(
                    SelectedOpinion.dict_for_llm(selected_past_case)
                )

        for argument in arguments_of_brief:

            (
                reply_instance_for_argument_enhancement_message,
                reply_json_for_argument_enhancement_message,
            ) = Reply.save_reply(
                self.ChatInstance.scope["_Query_Instance"],
                ReplyType.LLM_ACTION.value,
                {
                    "trigger_number": 8,
                    "trigger_content": "",
                    "message": f"System is going to enhance the Argument : {argument.get('title')}",
                },
            )
            self.send_response_to_user(
                self.arrange_response_to_yield(
                    query_id=self.ChatInstance.scope["_Query_Instance"].id,
                    reply_json=reply_json_for_argument_enhancement_message,
                )
            )

            enhancedArgument = self.enhance_argument(
                argument, reply_instance_for_argument_enhancement_message,
                selected_past_cases_list
            )
            BriefArguments.objects.create(
                user_brief=user_biref_instance,
                title=enhancedArgument["title"],
                description=enhancedArgument["description_paragraphs"],
            )
        user_biref_instance, _ = UserBrief.objects.get_or_create(
            user=self.ChatInstance.scope["user"],
            chat=self.ChatInstance.scope["_Chat_Instance"],
        )
        reply_instance, reply_json = Reply.save_reply(
            self.ChatInstance.scope["_Query_Instance"],
            ReplyType.BRIEF.value,
            {
                "message": "Arguments of Brief has been Generated/Updated",
                "brief_data": UserBrief.convert_to_dict(
                    user_brief_instance=user_biref_instance
                ),
            },
        )
        json_response = self.arrange_response_to_yield(
            query_id=self.ChatInstance.scope["_Query_Instance"].id,
            reply_json=reply_json,
            completed=True,
        )
        self.send_response_to_user(json_response)
        print("Questions Presented  Page of Brief Document is updated")

    def enhance_argument(self, argument, reply_instance: Reply,past_cases_list:List):
        print("Going to enhance argument ", argument.get("title"))
        prompt = f"""
            You are a Legal AI Assistant. Who is experenced in drafting Court Brief.You convert text data into structured JSON. 
            You are expert/Geek of making/drafting arguments related to legal matter and arguments of Court Brief. You are the 
            best lawyer and you know your game. You know how to generate and put arguments in front of a judge and in the brief.

            Now You have to analyze the argument title, description and the history.
            You must write multiple paragrpahs for description. The length of description_paragraphs string array must be atleast 5.
            But you can enhance and write as many paragrapsh you want but be reasonable. 
            You must put each paragraph as a seperate element in description_paragraphs string array.

            This is the Chat History of User with another AI : {self.ChatInstance.scope["_Query_History"]}
            This is the Current Query of User : {self.ChatInstance.scope["_Query_Instance"].query}

            This is the argument's title that you need to enhance : {argument.get('title')}
            This is the argument's description for which you have to write multiple paragrphs : {argument.get('description')} 
            
            Past cases that can be related to this argument : {past_cases_list}

            In chat history there might be information that can support in enhancement of above argument.
            You need to also utlize history, and write as many paragrphs as possible for above arguement that you need to enhance. 
            You must also reffer to one or many past cases if list is present for this argument, You must mention past case name, court name and explain how the past case is related to this one and this argument. 
            User must win this case.

            Understand the data and generate paragrphs for above argument and put them into description_paragraphs string array in JSON of following structure:
            {{
                "argument":
                    {{
                    "title": "value of argument title/heading",
                    "description_paragraphs": []
                    }}
            }}

            Remember to analyze hard.
            Now Remember, you only reply JSON, you do not talk other than JSON. Again, only reply in JSON string of above structure.
        """
        llm = OpenAI(model_name=self.model_name)
        res = llm(prompt)
        print(res)
        Thread(target=save_chat_tokens, args=(prompt, res, reply_instance)).start()
        parsed_response = self.extract_json(res)
        print(parsed_response)
        return parsed_response.get("argument")

    def extract_json(self, input_string):
        print("&&&&&&&&&&&&&&&&&")
        # Find the start and end positions of the JSON content
        start_pos = input_string.find("{")
        end_pos = input_string.rfind("}") + 1

        # Extract the JSON content from the string
        json_str = input_string[start_pos:end_pos]
        text = json_str.replace("\n\n", "")
        print(text)

        # Load the JSON content into a Python object
        try:
            json_object = json.loads(text)
            return json_object
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None

    def handle_summary_generation(self, Gpt_Trigger: GptTrigger = None):
        print("Going to handle generation of arguments page")
        print(Gpt_Trigger.TriggerContent)
        prompt = f"""
        You are a Legal AI Assistant. Who is experenced in drafting Court Brief.You convert text data into structured JSON. 
        You are expert/Geek of making/drafting summary of arguments related to legal matter and summary of arguments of Court Brief. 
        You are the best lawyer and you know your game. You know how to generate and put summary in front of a judge and in the brief.

        Now You have to analyze the text and put the respective value into JSON Field after Reasoning.
        This is the Chat History of User with another AI : {self.ChatInstance.scope["_Query_History"]}
        This is the Current Query of User : {self.ChatInstance.scope["_Query_Instance"].query}
        
        You need to generate the best summary possible after analyzing the Chat History.
        You must put each paragraph as a seperate element in summary_of_arguments in string array. 
        Ideal length of  summary_of_arguments string array is 2 but you can generate a maximum of 3 pargarpsh if required.
        User must win this case.

        Understand the data and generate paragrphs for summary of arguments and put them into summary_of_arguments string array in JSON of following structure:
        {{
            "summary_of_arguments": [],
        }}

        Remember to analyze hard.
        Now Remember, you only reply JSON, you do not talk other than JSON. Again, only reply in JSON string of above structure.
        """
        llm = OpenAI(model_name=self.model_name)
        res = llm(prompt)
        parsed_response = json.loads(res)
        user_biref_instance, _ = UserBrief.objects.get_or_create(
            user=self.ChatInstance.scope["user"],
            chat=self.ChatInstance.scope["_Chat_Instance"],
        )

        user_biref_instance.summary_of_arguments = parsed_response.get(
            "summary_of_arguments", []
        )
        user_biref_instance.save()
        reply_instance, reply_json = Reply.save_reply(
            self.ChatInstance.scope["_Query_Instance"],
            ReplyType.BRIEF.value,
            {
                "message": "Summary of Arguments has been Generated/Updated",
                "brief_data": UserBrief.convert_to_dict(
                    user_brief_instance=user_biref_instance
                ),
            },
        )
        Thread(target=save_chat_tokens, args=(prompt, res, reply_instance)).start()
        json_response = self.arrange_response_to_yield(
            query_id=self.ChatInstance.scope["_Query_Instance"].id,
            reply_json=reply_json,
            completed=True,
        )
        self.send_response_to_user(json_response)
        print("Summary of Arguments  is updated")

    def handle_conclusion_generation(self, Gpt_Trigger: GptTrigger = None):
        print("Going to handle generation of conclusion page")
        print(Gpt_Trigger.TriggerContent)
        prompt = f"""
        You are a Legal AI Assistant. Who is experenced in drafting Court Brief.You convert text data into structured JSON. 
        You are expert/Geek of making/drafting conclusion of legal matters and conclusion of Court Brief. 
        You are the best lawyer and you know your game. You know how to generate and put conclusion in front of a judge and in the brief.

        Now You have to analyze the text and put the respective value into JSON Field after Reasoning.
        This is the Chat History of User with another AI : {self.ChatInstance.scope["_Query_History"]}
        This is the Current Query of User : {self.ChatInstance.scope["_Query_Instance"].query}
        
        You need to generate the best conclusion possible after analyzing the Chat History.
        In chat history there might be arguments made by another AI using references of past case.
        User must win this case.

        Understand the data and generate arguments and put them into JSON of following structure:
        {{
            "conclusion": ""
        }}

        Remember to analyze hard.
        Now Remember, you only reply JSON, you do not talk other than JSON. Again, only reply in JSON string of above structure.
        """
        llm = OpenAI(model_name=self.model_name)
        res = llm(prompt)
        parsed_response = json.loads(res)
        user_biref_instance, _ = UserBrief.objects.get_or_create(
            user=self.ChatInstance.scope["user"],
            chat=self.ChatInstance.scope["_Chat_Instance"],
        )

        user_biref_instance.conclusion = parsed_response.get("conclusion", "")
        user_biref_instance.save()
        reply_instance, reply_json = Reply.save_reply(
            self.ChatInstance.scope["_Query_Instance"],
            ReplyType.BRIEF.value,
            {
                "message": "Conclusion of Brief has been Generated/Updated",
                "brief_data": UserBrief.convert_to_dict(
                    user_brief_instance=user_biref_instance
                ),
            },
        )
        Thread(target=save_chat_tokens, args=(prompt, res, reply_instance)).start()
        json_response = self.arrange_response_to_yield(
            query_id=self.ChatInstance.scope["_Query_Instance"].id,
            reply_json=reply_json,
            completed=True,
        )
        self.send_response_to_user(json_response)
        print("conclusion Page of Brief Document is updated")

    def handle_document_generation(self, Gpt_Trigger: GptTrigger = None):
        print("Going to Handle Document Generation")
        print(Gpt_Trigger.TriggerContent)
        prompt = f"""
        You are a Legal AI Assistant. Who is experenced in drafting Court Brief.You convert text data into structured JSON. You analyze the text and put the respective value into JSON Field after Reasoning.
        This is the Chat History of User with another AI : {self.ChatInstance.scope["_Query_History"]}
        Understand the data and convert it into JSON of following structure:
        {{
            "court_name": "",
            "court_term": "e.g Spring Term 2021",
            "petitioner_name": "",
            "respondent_name": "",
            "title_of_brief": "",
            "submitting_entity":"",
            "attorneys":[],
            "questions_presented":[],
            "table_of_authorities":[],
            "statement_of_case": "",
            "arguments_of_case": [
                {{
                "title": "value of argument title/heading",
                "description": "value of argument description"
                }}
            ],
            "summary_of_arguments": "",
            "conclusion": ""
        }}
        Remember tho analyze hard, and find out value for each field. You must provide the value of arguments_of_case as array of proper data structure. 
        You can also modify the text for a better summary of arguments, and conclusion based on you understanding of case.
        Remeber to find hard the values of statement of case an values of summary of arugument and conclusion.
        Remeber to use your own reasoning to generate some content for the fields, if you cannot find any contennt, remember to generate yourself.
        Remember, you only reply JSON, you do not talk other than JSON. Again, only reply in JSON of above structure.
        And Remember to reply with big heart, meaning , with big paragraphs regarding legal perspective.
        """
        llm = OpenAI(model_name=self.model_name)
        res = llm(prompt)
        parsed_response = json.loads(res)
        arguments_of_brief = parsed_response.get("arguments_of_case", None)
        brief_arguments = []
        for argument in arguments_of_brief:
            brief_arguments.append((argument["title"], argument["description"]))
        user_biref_instance = UserBrief.save_user_brief(
            user=self.ChatInstance.scope["user"],
            chat=self.ChatInstance.scope["_Chat_Instance"],
            court_name=parsed_response.get("court_name", ""),
            court_term=parsed_response.get("court_term", None),
            petitioner_name=parsed_response.get("petitioner_name", None),
            respondent_name=parsed_response.get("respondent_name", None),
            title_of_brief=parsed_response.get("title_of_brief", None),
            submitting_entity=parsed_response.get("submitting_entity", None),
            attorneys=parsed_response.get("attorneys", None),
            questions_presented=parsed_response.get("questions_presented", None),
            table_of_authorities=parsed_response.get("table_of_authorities", None),
            statement_of_case=parsed_response.get("statement_of_case", None),
            summary_of_arguments=parsed_response.get("summary_of_arguments", None),
            conclusion=parsed_response.get("conclusion", None),
            brief_arguments=brief_arguments,
        )
        reply_instance, reply_json = Reply.save_reply(
            self.ChatInstance.scope["_Query_Instance"],
            ReplyType.BRIEF.value,
            UserBrief.convert_to_preview_dict(user_biref_instance),
        )
        Thread(target=save_chat_tokens, args=(prompt, res, reply_instance)).start()
        json_response = self.arrange_response_to_yield(
            query_id=self.ChatInstance.scope["_Query_Instance"].id,
            reply_json=reply_json,
            completed=True,
        )
        self.send_response_to_user(json_response)
        print("PDF FILE PATH SENT TO FRONTEND")

    def get_list_of_generated_section(self, chat_id):
        list_of_generated_sections = []
        try:
            user_brief = UserBrief.objects.get(chat__id=chat_id)
            if not user_brief:
                return list_of_generated_sections

            if (
                user_brief.court_name is not None
                or user_brief.court_term is not None
                or user_brief.petitioner_name is not None
                or user_brief.respondent_name is not None
                or user_brief.title_of_brief is not None
            ):
                list_of_generated_sections.append("Cover Page")
            if user_brief.questions_presented is not None:
                list_of_generated_sections.append("Questions Presented")
            if user_brief.table_of_authorities is not None:
                list_of_generated_sections.append("Table of Authorities")
            if user_brief.statement_of_case is not None:
                list_of_generated_sections.append("Statement of Case")
            try:
                arguments = BriefArguments.objects.filter(user_brief=user_brief)
                if len(arguments) > 0:
                    list_of_generated_sections.append("Arguments of Case")
            except Exception as ex:
                print(ex)
            if user_brief.summary_of_arguments is not None:
                list_of_generated_sections.append("Summary of Arguments")
            if user_brief.conclusion is not None:
                list_of_generated_sections.append("Conclusion")
        except Exception as ex:
            print(ex)
        return list_of_generated_sections

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

        # query_sources = GetDocsFromVectorDB(hf, query, False)
        # if query_sources:
        #     query_data_from_vdb = Source.save_sources_list(
        #         query_instance=ChatInstance.scope["_Query_Instance"],
        #         sources_list=query_sources,
        #     )
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
                # query_sources = GetDocsFromVectorDB(hf, Gpt_Trigger.TriggerContent, False)
                # if query_sources:
                #     requested_data_from_vdb = Source.save_sources_list(
                #         query_instance=ChatInstance.scope["_Query_Instance"],
                #         sources_list=query_sources,
                #     )
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
            list_of_generated_sections=self.get_list_of_generated_section(
                self.ChatInstance.scope["_Chat_Instance"].id
            ),
        )
        for json_response in self.generate_stream(
            Query_Instance=self.ChatInstance.scope["_Query_Instance"],
            prompt=prompt,
        ):
            # print(response)
            self.send_response_to_user(json_response)

    def handle_citations(self):
        print("Going to Handle Opinion Citations")
        length_of_selected_opinions = len(self.ChatInstance.scope["_Selected_Opinions"])
        table_of_authorities = []
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

        selected_opinions_by_chat = SelectedOpinion.objects.filter(
            chat=self.ChatInstance.scope["_Chat_Instance"]
        )
        for selected_opinion in selected_opinions_by_chat:
            if selected_opinion.docket_reference:
                table_of_authorities.append(
                    f"{selected_opinion.case_name} ({selected_opinion.date_filed}), {selected_opinion.court_name}, {selected_opinion.docket_reference}"
                )
            else:
                table_of_authorities.append(
                    f"{selected_opinion.case_name} ({selected_opinion.date_filed}), {selected_opinion.court_name},"
                )

        user_biref_instance, _ = UserBrief.objects.get_or_create(
            user=self.ChatInstance.scope["user"],
            chat=self.ChatInstance.scope["_Chat_Instance"],
        )

        user_biref_instance.table_of_authorities = table_of_authorities
        user_biref_instance.save()
        reply_instance, reply_json = Reply.save_reply(
            self.ChatInstance.scope["_Query_Instance"],
            ReplyType.BRIEF.value,
            {
                "message": "Table of Authorities Section in Brief has been updated..",
                "brief_data": UserBrief.convert_to_dict(
                    user_brief_instance=user_biref_instance
                ),
            },
        )
        json_response = self.arrange_response_to_yield(
            query_id=self.ChatInstance.scope["_Query_Instance"].id,
            reply_json=reply_json,
            completed=True,
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
