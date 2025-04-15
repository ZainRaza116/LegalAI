import uuid
import LegalAI.settings as settings
from django.db import models
from django.contrib.auth.models import User
from typing import List, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
from enum import Enum


# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    usrType = models.TextField(null=True)
    indexUUID = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.TextField(null=True)
    imgUrl = models.TextField(null=True)


class ChatType(Enum):
    CourtBrief = "CourtBrief"
    UserResearch = "UserResearch"


class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.TextField(null=True, default="")
    type = models.CharField(
        max_length=50,
        choices=[(chat_type.value, chat_type.name) for chat_type in ChatType],
        null=False,
        default=ChatType.CourtBrief.value,
    )
    ip_address = models.TextField(null=True)
    date_time = models.DateTimeField(auto_now_add=True)


class Query(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    query = models.TextField(null=False)
    query_datetime = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get_latest_query_by_chat(cls, chat_id):
        latest_query = cls.objects.filter(chat_id=chat_id).aggregate(
            latest_query_datetime=models.Max("query_datetime")
        )

        if latest_query["latest_query_datetime"]:
            latest_query_object = cls.objects.filter(
                chat_id=chat_id, query_datetime=latest_query["latest_query_datetime"]
            ).first()
            return latest_query_object
        else:
            return None


class ReplyType(Enum):
    TEXT = "TEXT"
    LLM_ACTION = "LLM_ACTION"
    ARGUMENT_FROM_OPINION = "ARGUMENT_FROM_OPINION"
    BRIEF = "BRIEF"


class Reply(models.Model):
    REPLY_TYPES = [(reply_type.value, reply_type.name) for reply_type in ReplyType]

    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=REPLY_TYPES, null=True)
    value = models.JSONField(null=True)
    reply_datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply of type {self.type} to '{self.query}'"

    class Meta:
        verbose_name_plural = "Replies"

    def clean(self):
        super().clean()
        self.validate_reply_type()

    def validate_reply_type(self):
        if self.type not in [choice[0] for choice in self.REPLY_TYPES]:
            raise ValidationError("Invalid reply type.")

        if self.type == ReplyType.TEXT:
            self.validate_text_reply()
        elif self.type == ReplyType.LLM_ACTION:
            self.validate_llm_action_reply()
        elif self.type == ReplyType.ARGUMENT_FROM_OPINION:
            self.validate_argument_from_opinion_reply()
        elif self.type == ReplyType.BRIEF:
            self.validate_brief_reply()

    def validate_text_reply(self):
        if "message" not in self.value:
            raise ValidationError(
                "For 'Text' type, 'message' key must be present in the value."
            )

    def validate_llm_action_reply(self):
        if "trigger_number" not in self.value or "trigger_content" not in self.value:
            raise ValidationError(
                "For 'LLM Action' type, 'trigger_number' and 'trigger_content' keys must be present in the value."
            )

    def validate_argument_from_opinion_reply(self):
        if "selected_opinion_id" not in self.value:
            raise ValidationError(
                "For 'Argument from Opinion' type, 'selected_opinion_id' key must be present in the value."
            )

    def validate_brief_reply(self):
        if "brief_id" not in self.value:
            raise ValidationError(
                "For 'Brief' type, 'brief_id' key must be present in the value."
            )
        # Perform additional validation for 'Brief' type

    @classmethod
    def save_reply(cls, query, reply_type, value):
        # Create a new Reply instance
        reply = cls(query=query, type=reply_type, value=value)
        reply.clean()
        reply.save()

        # Serialize the reply instance into JSON
        reply_json = {
            "id": reply.id,
            "type": reply.type,
            "value": reply.value,
            "reply_datetime": reply.reply_datetime.isoformat(),
        }

        return reply, reply_json

    @classmethod
    def get_reply_by_id(cls, id):
        reply = cls.objects.get(id=id)
        reply_json = {
            "id": reply.id,
            "type": reply.type,
            "value": reply.value,
            "reply_datetime": reply.reply_datetime.isoformat(),
        }
        return reply, reply_json

    @classmethod
    def convert_to_dict(cls, reply: "Reply"):
        json_object = {
            "id": reply.id,
            "type": reply.type,
            "value": reply.value,
            "reply_datetime": reply.reply_datetime.isoformat(),
        }
        return json_object


class Source(models.Model):
    user_query = models.ForeignKey(Query, on_delete=models.CASCADE)
    search_type = models.CharField(null=False, max_length=20)
    search_target = models.CharField(null=False, max_length=20, default="SystemDB")
    search_query = models.TextField(null=False)
    source_link = models.TextField(null=True)
    score = models.TextField(null=True)
    content = models.TextField(null=True)

    @classmethod
    def save_sources_list(
        cls, query_instance, sources_list, search_type="Auto", search_target="SystemDB"
    ):
        sources_as_string_list = []
        for source in sources_list:
            content = source[0].page_content
            score = source[1]
            sources_as_string_list.append(content)
            new_source = cls.objects.create(
                user_query=query_instance,
                search_type=search_type,
                search_target=search_target,
                search_query=query_instance.query,
                source_link=source[0].metadata.get("source"),
                score=score,
                content=content,
            )
            new_source.save()
        return sources_as_string_list


class Files(models.Model):
    file_name = models.TextField(null=True)
    file_identifier = models.TextField(null=True)
    _type = models.TextField(null=True)
    status = models.TextField(null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    logs = models.TextField(null=True)
    reason = models.TextField(null=True)


class UserDocuments(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, null=True)
    file_name = models.TextField(null=True)
    file_identifier = models.TextField(null=True)
    _type = models.TextField(null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    create_embeddings = models.BooleanField(null=False, default=False)
    embedding_status = models.TextField(null=True)
    embedded_at = models.DateTimeField(null=True)
    embedding_logs = models.TextField(null=True)
    embedding_failure_reason = models.TextField(null=True)


class UserBrief(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    court_name = models.TextField(null=True)
    court_term = models.TextField(null=True)
    petitioner_name = models.TextField(null=True)
    respondent_name = models.TextField(null=True)
    title_of_brief = models.TextField(null=True)
    submitting_entity = models.TextField(null=True)
    attorneys = models.JSONField(null=True)
    questions_presented = models.JSONField(null=True)
    table_of_authorities = models.JSONField(null=True)
    statement_of_case = models.JSONField(null=True)
    summary_of_arguments = models.JSONField(null=True)
    conclusion = models.TextField(null=True)

    @classmethod
    def save_user_brief(
        cls,
        user: User,
        chat: Chat,
        court_name: str,
        court_term: str,
        petitioner_name: str,
        respondent_name: str,
        title_of_brief: str,
        submitting_entity: str,
        attorneys: str,
        questions_presented: str,
        table_of_authorities: str,
        statement_of_case: str,
        summary_of_arguments: str,
        conclusion: str,
        brief_arguments: List[Tuple[str, str]],
    ) -> "UserBrief":
        with transaction.atomic():
            user_brief = cls.objects.create(
                user=user,
                chat=chat,
                court_name=court_name,
                court_term=court_term,
                petitioner_name=petitioner_name,
                respondent_name=respondent_name,
                title_of_brief=title_of_brief,
                submitting_entity=submitting_entity,
                attorneys=attorneys,
                questions_presented=questions_presented,
                table_of_authorities=table_of_authorities,
                statement_of_case=statement_of_case,
                summary_of_arguments=summary_of_arguments,
                conclusion=conclusion,
            )
            if brief_arguments:
                for title, description in brief_arguments:
                    BriefArguments.objects.create(
                        user_brief=user_brief, title=title, description=description
                    )

        return user_brief

    @classmethod
    def convert_to_dict(cls, user_brief_instance: "UserBrief"):
        # try:
        #     user_brief_instance.attorneys=json.loads(user_brief_instance.attorneys)
        # except Exception as ex:
        #     user_brief_instance.attorneys=user_brief_instance.attorneys[1:-1]
        #     print(ex)
        # try:
        #     user_brief_instance.questions_presented=json.loads(user_brief_instance.questions_presented)
        # except Exception as ex:
        #     print(ex)
        #     user_brief_instance.questions_presented[1:-1]
        # try:
        #     user_brief_instance.table_of_authorities=json.loads(user_brief_instance.table_of_authorities)
        # except Exception as ex:
        #     print(ex)
        #     user_brief_instance.table_of_authorities[1:-1]
        brief_dict = {
            "brief_id": user_brief_instance.id,
            "unique_id": str(user_brief_instance.unique_id),
            "user_id": user_brief_instance.user.id,
            "chat_id": user_brief_instance.chat.id,
            "court_name": user_brief_instance.court_name,
            "court_term": user_brief_instance.court_term,
            "petitioner_name": user_brief_instance.petitioner_name,
            "respondent_name": user_brief_instance.respondent_name,
            "title_of_brief": user_brief_instance.title_of_brief,
            "submitting_entity": user_brief_instance.submitting_entity,
            "attorneys": user_brief_instance.attorneys,
            "questions_presented": user_brief_instance.questions_presented,
            "table_of_authorities": user_brief_instance.table_of_authorities,
            "statement_of_case": user_brief_instance.statement_of_case,
            "summary_of_arguments": user_brief_instance.summary_of_arguments,
            "conclusion": user_brief_instance.conclusion,
            "brief_arguments": [
                {"title": arg.title, "description": arg.description}
                for arg in user_brief_instance.arguments.all()
            ],
        }
        return brief_dict

    @classmethod
    def get_cover_page(cls, user_brief_instance: "UserBrief"):
        brief_dict = {
            "brief_id": user_brief_instance.id,
            "unique_id": str(user_brief_instance.unique_id),
            "user_id": user_brief_instance.user.id,
            "chat_id": user_brief_instance.chat.id,
            "court_name": user_brief_instance.court_name,
            "court_term": user_brief_instance.court_term,
            "petitioner_name": user_brief_instance.petitioner_name,
            "respondent_name": user_brief_instance.respondent_name,
            "title_of_brief": user_brief_instance.title_of_brief,
            "submitting_entity": user_brief_instance.submitting_entity,
            "attorneys": user_brief_instance.attorneys,
        }
        return brief_dict

    @classmethod
    def get_questions(cls, user_brief_instance: "UserBrief"):
        brief_dict = {
            "brief_id": user_brief_instance.id,
            "questions_presented": user_brief_instance.questions_presented,
        }
        return brief_dict

    @classmethod
    def get_statement(cls, user_brief_instance: "UserBrief"):
        brief_dict = {
            "brief_id": user_brief_instance.id,
            "statement_of_case": user_brief_instance.statement_of_case,
        }
        return brief_dict

    @classmethod
    def get_arguments(cls, user_brief_instance: "UserBrief"):
        brief_dict = {
            "brief_id": user_brief_instance.id,
            "brief_arguments": [
                {"title": arg.title, "description": arg.description}
                for arg in user_brief_instance.arguments.all()
            ],
        }
        return brief_dict

    @classmethod
    def get_summary(cls, user_brief_instance: "UserBrief"):
        brief_dict = {
            "brief_id": user_brief_instance.id,
            "summary_of_arguments": user_brief_instance.summary_of_arguments,
        }
        return brief_dict

    @classmethod
    def get_conclusion(cls, user_brief_instance: "UserBrief"):
        brief_dict = {
            "brief_id": user_brief_instance.id,
            "conclusion": user_brief_instance.conclusion,
        }
        return brief_dict

    @classmethod
    def convert_to_preview_dict(cls, user_brief_instance: "UserBrief"):
        brief_dict = {
            "brief_id": user_brief_instance.id,
            "unique_id": str(user_brief_instance.unique_id),
            "user_id": user_brief_instance.user.id,
            "chat_id": user_brief_instance.chat.id,
            "court_name": user_brief_instance.court_name,
            "court_term": user_brief_instance.court_term,
            "petitioner_name": user_brief_instance.petitioner_name,
            "respondent_name": user_brief_instance.respondent_name,
            "title_of_brief": user_brief_instance.title_of_brief,
            "submitting_entity": user_brief_instance.submitting_entity,
            "attorneys": user_brief_instance.attorneys,
        }
        return brief_dict


class BriefArguments(models.Model):
    user_brief = models.ForeignKey(
        UserBrief, on_delete=models.CASCADE, related_name="arguments"
    )
    title = models.TextField(null=False)
    description = models.JSONField(null=True)


class SelectedOpinion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    opinion_id = models.TextField()
    case_name = models.TextField()
    absolute_url = models.TextField()
    court_name = models.TextField(null=True)
    date_filed = models.TextField()
    status = models.TextField()
    citations = models.TextField()
    summary = models.TextField()
    docket_reference = models.TextField(null=True)
    generated_argument = models.TextField()

    @classmethod
    def save_selected_opinion(
        cls,
        user,
        chat,
        opinion_id,
        case_name,
        absolute_url,
        court_name,
        date_filed,
        status,
        citations,
        summary,
        generated_argument,
        docket_reference,
    ):
        selected_opinion = cls(
            user=user,
            chat=chat,
            opinion_id=opinion_id,
            case_name=case_name,
            absolute_url=absolute_url,
            court_name=court_name,
            date_filed=date_filed,
            status=status,
            citations=citations,
            summary=summary,
            generated_argument=generated_argument,
            docket_reference=docket_reference,
        )
        selected_opinion.save()
        return selected_opinion

    @classmethod
    def dict_for_llm(cls, selected_opinion: "SelectedOpinion"):
        json_object = {
            "case_name": selected_opinion.case_name,
            "court_name": selected_opinion.court_name,
            "date_filed": selected_opinion.date_filed,
            "status": selected_opinion.status,
            "generated_argument": selected_opinion.generated_argument,
        }
        return json_object

    @classmethod
    def convert_to_dict(cls, opinion: "SelectedOpinion"):
        json_object = {
            "user_id": opinion.user.id,
            "chat_id": opinion.chat.id,
            "opinion_id": opinion.opinion_id,
            "case_name": opinion.case_name,
            "absolute_url": opinion.absolute_url,
            "court_name": opinion.court_name,
            "date_filed": opinion.date_filed,
            "status": opinion.status,
            "citations": opinion.citations,
            "summary": opinion.summary,
            "generated_argument": opinion.generated_argument,
        }
        return json_object


class WaitingList(models.Model):
    name = models.TextField(null=True)
    email = models.TextField(null=True)
    date = models.DateTimeField(null=True)


class ChatTokenUsage(models.Model):
    reply = models.OneToOneField(
        Reply, on_delete=models.CASCADE, related_name="token_usage"
    )
    input_tokens = models.IntegerField()
    output_tokens = models.IntegerField()
    date_time = models.DateTimeField(auto_now_add=True)
    usage_cost_in_cents = models.DecimalField(
        max_digits=15, decimal_places=2, null=True
    )

    @classmethod
    def save(self, reply, input_tokens, output_tokens):
        cost_input = input_tokens * float(
            settings.PRIMARY_MODEL_INPUT_PRICE_PER_TOKEN_IN_CENTS
        )
        cost_output = output_tokens * float(
            settings.PRIMARY_MODEL_OUTPUT_PRICE_PER_TOKEN_IN_CENTS
        )
        total_cost = cost_input + cost_output
        token_usage = self(
            reply=reply,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            usage_cost_in_cents=total_cost,
        )
        token_usage.save()
        return token_usage


class StripeCustomer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=255, null=False)
    customerID = models.CharField(max_length=255, null=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.name} ({self.email})"


class SuccessfulPayment(models.Model):
    stripe_customer = models.ForeignKey(StripeCustomer, on_delete=models.CASCADE, related_name='payments')
    payment_amount = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default='usd')
    payment_status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Successful Payment"
        verbose_name_plural = "Successful Payments"