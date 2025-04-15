import datetime
import json
import os
import uuid
from threading import Thread
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import FileResponse
from django.db.models import Sum
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from langchain.document_loaders import DirectoryLoader
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
)
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from LegalAI import settings
from .models import (
    ChatTokenUsage,
    ChatType,
    Profile,
    Files,
    Chat,
    Query,
    Reply,
    UserDocuments,
    UserBrief,
    WaitingList,
    BriefArguments,
    StripeCustomer,
    SuccessfulPayment
)
from .utilities import GenerateRequestResponse, GetClientIpAddress, Handle_Files_Upload
from .authentication import CustomTokenAuthentication
from .court_listener import courts as fetch_courtlistener_courts
import stripe
from .docx_generator import generate_docx_for_brief
from .serializers import SuccessfulPaymentSerializer, StripeCustomerSerializer
os.environ["OPENAI_API_KEY"] = settings.OPENAI_KEY
os.environ["STRIPE_SECRETE_KEY"] = settings.STRIPE_SECRETE_KEY
stripe.api_key = settings.STRIPE_SECRETE_KEY
webhook_secret = settings.webhook_secret

class SignupView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            email = request.data.get("email")
            first_name = request.data.get("first_name")
            last_name = request.data.get("last_name")
            password = request.data.get("password")
            usrType = "normal"
            if not email or not password:
                return Response(
                    GenerateRequestResponse(
                        False, 400, "Username and password are required", None
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user, created = User.objects.get_or_create(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )
            if created:
                myProfile = Profile(user=user, usrType=usrType, name=first_name)
                myProfile.save()
                user.set_password(password)
                user.save()

                token, created = Token.objects.get_or_create(user=user)
                return Response(
                    GenerateRequestResponse(
                        status=True,
                        status_code=201,
                        message="Account Created Successfully",
                        response={"token": token.key},
                    ),
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="A user with this email already exists",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            email = request.data.get("email")
            password = request.data.get("password")
            try:
                user = User.objects.get(username=email)
                if not user.is_active:
                    return Response(
                        GenerateRequestResponse(
                            status=False,
                            status_code=400,
                            message="Please verify your account by following the instructions sent to you via email",
                            response=None,
                        ),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if user.check_password(password):
                    token = Token.objects.get(user=user)
                    token.delete()
                    newToken = Token(user=user)
                    newToken.save()
                    return Response(
                        GenerateRequestResponse(
                            status=True,
                            status_code=200,
                            message="Login Successfull",
                            response={"token": newToken.key},
                        ),
                        status=status.HTTP_200_OK,
                    )

                else:
                    return Response(
                        GenerateRequestResponse(
                            status=False,
                            status_code=400,
                            message="Invalid password",
                            response=None,
                        ),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except User.DoesNotExist:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="User not Found",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChangePasswordView(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=403,
                    message="Authentication credentials were not provided.",
                    response=None,
                ),
                status=status.HTTP_403_FORBIDDEN,
            )

        data = json.loads(request.body)
        try:
            oldPassword = data.get("old_password")
            newPassword = data.get("new_password")
            if not oldPassword or not newPassword:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Old password and new password are required.",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not user.check_password(oldPassword):
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Old password is incorrect",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = Token.objects.get(user=user)
            token.delete()
            user.set_password(newPassword)
            user.save()
            new_token, created = Token.objects.get_or_create(user=user)
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="Password updated successfully",
                    response={"token": new_token.key},
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserProfileView(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        try:
            user = request.user
            data = json.loads(request.POST.get("payload"))
            first_name = data.get("first_name", None)
            last_name = data.get("last_name", None)

            if not first_name:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="First Name is Required.",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not last_name:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Last Name is Required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            image_file = request.FILES.get("image_file")
            file_extension = os.path.splitext(image_file.name)[1]
            temp_file_path = os.path.join(
                "bot/static/profile_pictures", f"{user.id}__{file_extension}"
            )

            with open(temp_file_path, "wb") as output_file:
                for chunk in image_file.chunks():
                    output_file.write(chunk)
            user_profile = Profile.objects.get(user=user)
            user_profile.imgUrl = temp_file_path.replace("bot/", "/")
            user_profile.save()
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="User Profile Updated Successfully",
                    response={
                        "first_name": first_name,
                        "last_name": last_name,
                        "profile_picture": user_profile.imgUrl,
                    },
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            user_profile = Profile.objects.get(user=user)
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="User Profile Data Fetched Successfully.",
                    response={
                        "id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "profile_picture": user_profile.imgUrl,
                    },
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatView(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            data = json.loads(request.body)

            title = data.get("title")
            type = data.get("type", ChatType.CourtBrief.value)
            if not title:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Chat title is required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if type not in [chat_type.value for chat_type in ChatType]:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Chat type is Invalid!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ip_address = GetClientIpAddress(request=request)
            _chat = Chat(user=user, title=title, ip_address=ip_address, type=type)
            _chat.save()
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="Chat created sucessfully",
                    response={
                        "chat_id": _chat.id,
                        "chat_title": _chat.title,
                        "chat_type": _chat.type,
                        "chat_date": _chat.date_time,
                    },
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            page = self.request.query_params.get("page", 1)
            type = self.request.query_params.get("type", None)
            if type is not None and type not in [
                chat_type.value for chat_type in ChatType
            ]:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Chat type is Invalid!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if type == ChatType.UserResearch.value:
                user_chats = Chat.objects.filter(user=user).order_by("-date_time")
            else:
                # user_chats = Chat.objects.filter(user=user, type=type).order_by(
                #     "-date_time"
                # )
                user_chats = []
            user_chats_list = []
            paginator = Paginator(user_chats, 10)
            chats_page = paginator.get_page(page)
            for chat in chats_page:
                user_chats_list.append(
                    {
                        "chat_id": chat.id,
                        "chat_title": chat.title,
                        "chat_type": chat.type,
                        "chat_date": chat.date_time,
                    }
                )
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="User Chats Data Fetched Successfully.",
                    response={
                        "chats": user_chats_list,
                        "pagination": {
                            "page": page,
                            "total_pages": paginator.num_pages,
                            "has_next": chats_page.has_next(),
                            "has_prev": chats_page.has_previous(),
                        },
                        "success": True,
                    },
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, *args, **kwargs):
        try:
            user = request.user
            data = json.loads(request.body)
            chat_id = data.get("chat_id")

            if not chat_id:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Chat ID is required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            chat = Chat.objects.get(id=chat_id, user=user)  # Enforce ownership
            chat.delete()

            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="Chat deleted successfully",
                    response=None,  # No need to return data on delete
                ),
                status=status.HTTP_200_OK,
            )

        except Chat.DoesNotExist:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=404,
                    message="Chat not found",
                    response=None,
                ),
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatDetailView(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            chat_id = self.request.query_params.get("chat_id", None)
            if not chat_id:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Chat Id is required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            chat = Chat.objects.get(user=user, id=chat_id)
            queires = Query.objects.filter(chat=chat).order_by("query_datetime")
            replies = Reply.objects.filter(query__in=queires)
            queries_and_replies = []
            for query in queires:
                queries_and_replies.append(
                    {
                        "type": "query",
                        "query": {"id": query.id, "message": query.query},
                        "reply": None,
                    }
                )
                query_replies = replies.filter(query=query).order_by("reply_datetime")
                for reply in query_replies:
                    queries_and_replies.append(
                        {
                            "type": "reply",
                            "query": {"id": query.id, "message": query.query},
                            "reply": {
                                "id": reply.id,
                                "type": reply.type,
                                "value": reply.value,
                                "reply_datetime": reply.reply_datetime,
                            },
                        }
                    )
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="User Chats Data Fetched Successfully.",
                    response={
                        "chat_detail": queries_and_replies,
                    },
                ),
                status=status.HTTP_200_OK,
            )
        except Chat.DoesNotExist:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=400,
                    message="Chat does not exisit",
                    response=None,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UploadSystemDocuments(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    # permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        try:
            pdf_files = request.FILES.getlist("pdf_files")
            txt_files = request.FILES.getlist("txt_files")
            Directory = settings.US_CONSTITUTION_VECTOR_DB_PATH
            pdf_paths = Handle_Files_Upload(
                pdf_files, Directory, settings.PDF_FILE_STORAGE_SUBDIRECTORY
            )
            txt_paths = Handle_Files_Upload(
                txt_files, Directory, settings.TXT_FILE_STORAGE_SUBDIRECTORY
            )
            uploaded_files_info = []
            for pdf_file_path in pdf_paths:
                uploaded_files_info.append(
                    {"type": settings.PDF_FILE_TYPE_NAME, "path": pdf_file_path}
                )
            for txt_file_path in txt_paths:
                uploaded_files_info.append(
                    {"type": settings.TXT_FILE_TYPE_NAME, "path": txt_file_path}
                )

            uniqueIdentifier = str(uuid.uuid4())
            for uploaded_file in uploaded_files_info:
                file = Files(
                    file_name=str(uploaded_file["path"]).split("/")[-1],
                    file_identifier=uniqueIdentifier,
                    _type=uploaded_file["type"],
                    status="Processing",
                )
                file.save()
            Thread(
                target=GenerateEmbeddings,
                args=(Directory, uploaded_files_info, uniqueIdentifier),
            ).start()
            return JsonResponse(
                {"success": True, "message": "Embeddings are being Generated!"}
            )
        except Exception as e:
            print(f"An error=> {e}")
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UploadUserDocuments(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            data = json.loads(request.POST.get("payload"))
            chat_id = data.get("chat_id")
            if not chat_id:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Chat Id is required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            chat = Chat.objects.get(id=chat_id)
            pdf_files = request.FILES.getlist("pdf_files")
            if not len(pdf_files) > 0:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Pdf Files not Found!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Directory = os.path.join(
                settings.USER_DOCUMENTS__VECTOR_DB_PATH, str(user.profile.indexUUID)
            )
            pdf_paths = Handle_Files_Upload(
                pdf_files, Directory, settings.PDF_FILE_STORAGE_SUBDIRECTORY
            )
            uploaded_files_info = []
            uploaded_files_results = []
            for pdf_file_path in pdf_paths:
                uploaded_files_info.append(
                    {"type": settings.PDF_FILE_TYPE_NAME, "path": pdf_file_path}
                )
            uniqueIdentifier = str(uuid.uuid4())
            for uploaded_file in uploaded_files_info:
                user_file = UserDocuments(
                    user=user,
                    chat=chat,
                    file_name=str(uploaded_file["path"]).split("/")[-1],
                    file_identifier=uniqueIdentifier,
                    _type=uploaded_file["type"],
                    create_embeddings=True,
                    embedding_status="Processing",
                )
                user_file.save()
                uploaded_files_results.append(
                    {
                        "file_id": user_file.id,
                        "file_name": user_file.file_name,
                        "embedding_status": user_file.embedding_status,
                    }
                )
            Thread(
                target=GenerateEmbeddings,
                args=(
                    Directory,
                    uploaded_files_info,
                    uniqueIdentifier,
                    settings.USER_FILES_OWNER_NAME,
                ),
            ).start()
            print(uploaded_files_results)
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=201,
                    message="Files are being processed........",
                    response=uploaded_files_results,
                ),
                status=status.HTTP_200_OK,
            )
        except Chat.DoesNotExist:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=400,
                    message="Chat does not exisit",
                    response=None,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            print(f"An error=> {e}")
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            file_id = self.request.query_params.get("file_id", 1)
            if not file_id:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="File Id is required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_document = UserDocuments.objects.get(user=user, id=file_id)
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="Document Data Fetched Successfully.",
                    response={
                        "file_id": user_document.id,
                        "file_name": user_document.file_name,
                        "embedding_status": user_document.embedding_status,
                    },
                ),
                status=status.HTTP_200_OK,
            )
        except Chat.UserDocuments:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=400,
                    message="Chat does not exisit",
                    response=None,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserDocumentsByChat(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            chat_id = self.request.query_params.get("chat_id", 1)
            if not chat_id:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Chat Id is required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_documents = UserDocuments.objects.filter(chat__id=chat_id)
            user_documents_list = []
            for user_doc in user_documents:
                user_documents_list.append(
                    {
                        "file_id": user_doc.id,
                        "file_name": user_doc.file_name,
                        "embedding_status": user_doc.embedding_status,
                    }
                )
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="Document Data Fetched Successfully.",
                    response=user_documents_list,
                ),
                status=status.HTTP_200_OK,
            )
        except Chat.DoesNotExist:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=400,
                    message="Chat does not exisit",
                    response=None,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ServeUserDocument(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            document_id = self.request.query_params.get("document_id", None)
            if not document_id:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Document Id is required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user_documents = UserDocuments.objects.get(id=document_id, user=user)

            Directory = os.path.join(
                settings.USER_DOCUMENTS__VECTOR_DB_PATH, str(user.profile.indexUUID)
            )
            File_Path = os.path.join(
                Directory,
                settings.PDF_FILE_STORAGE_SUBDIRECTORY,
                user_documents.file_name,
            )
            if os.path.exists(File_Path):
                response = FileResponse(
                    open(File_Path, "rb"), content_type="application/pdf"
                )
                response["Content-Disposition"] = (
                    f'inline; filename="{user_documents.file_name}"'
                )
                return response
            else:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=404,
                        message="Document not Found!",
                        response=None,
                    ),
                    status=status.HTTP_404_NOT_FOUND,
                )
        except UserDocuments.DoesNotExist:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=400,
                    message="Chat does not exisit",
                    response=None,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def GenerateEmbeddings(
    directory,
    uploaded_files_info: list,
    unique_identifief_for_batch,
    files_owner=settings.SYSTEM_FILES_OWNER_NAME,
):
    model_name = "sentence-transformers/all-mpnet-base-v2"
    hf = HuggingFaceEmbeddings(model_name=model_name)

    uniqueIdentifier = unique_identifief_for_batch
    try:
        data = []
        PDF_FILES_PATH = os.path.join(directory, settings.PDF_FILE_STORAGE_SUBDIRECTORY)
        print("PDF FILES PATH IS : ")
        print(PDF_FILES_PATH)
        TXT_FILES_PATH = os.path.join(directory, settings.TXT_FILE_STORAGE_SUBDIRECTORY)
        pdf_files_loader = DirectoryLoader(
            PDF_FILES_PATH,
            glob="**/*.pdf",
            show_progress=True,
            loader_cls=UnstructuredPDFLoader,
        )
        text_files_loader = DirectoryLoader(
            TXT_FILES_PATH, glob="**/*.txt", show_progress=True
        )
        pdf_files_paths = [
            x for x in uploaded_files_info if x["type"] == settings.PDF_FILE_TYPE_NAME
        ]
        text_files_paths = [
            x for x in uploaded_files_info if x["type"] == settings.TXT_FILE_TYPE_NAME
        ]
        print(pdf_files_paths)
        if pdf_files_loader != []:
            if pdf_files_paths:
                print("extending pdfLoader")
                data.extend(pdf_files_loader.load())
                print("Lenght of Data : ")
                print(len(data))
        if text_files_loader != []:
            if text_files_paths:
                print("extending txtLoader")
                data.extend(text_files_loader.load())
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.split_documents(data)

        # persist_directory = "vector_store/database/"
        persist_directory = os.path.join(directory, settings.VECTOR_DB_PERSIST_STORAGE)
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
            print(f"Persist directory '{persist_directory}' created successfully.")
        embeddings = None
        embeddings = hf
        print("Documents length is ", len(docs))
        if docs:
            if os.path.exists(persist_directory):
                print("1. Going to Initialize Vector DB at ", persist_directory)
                vectordb = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=embeddings,
                )
                vectordb.add_documents(docs)
                vectordb.persist()
                vectordb = None
                print("Vector DB Created successfully!")
            else:
                print("2. Going to Initialize Vector DB at ", persist_directory)
                vectordb = Chroma.from_documents(
                    documents=docs,
                    embedding=embeddings,
                    persist_directory=persist_directory,
                )
                vectordb.persist()
                vectordb = None
                print("Vector DB Created successfully!")

        # FILES TRY
        try:
            if uploaded_files_info and files_owner == settings.SYSTEM_FILES_OWNER_NAME:
                allUrls = Files.objects.filter(file_identifier=uniqueIdentifier)
                for each in allUrls:
                    each.status = "Done"
                    each.reason = None
                    each.save()
                print("Files Status Updated to Done!")
            elif uploaded_files_info and files_owner == settings.USER_FILES_OWNER_NAME:
                allUserFiles = UserDocuments.objects.filter(
                    file_identifier=unique_identifief_for_batch
                )
                for user_file in allUserFiles:
                    user_file.embedding_status = "Done"
                    user_file.embedded_at = datetime.datetime.now()
                    user_file.save()
                print("User Document Status Updated To Done!")
        except Exception as e:
            print(f"Error fething session files {e}")

    except Exception as er:
        print(er)
        print(f"An Error Occurred while generating Embeddings, ERROR=> {er}")
        try:
            if uploaded_files_info and files_owner == settings.SYSTEM_FILES_OWNER_NAME:
                allUrls = Files.objects.filter(file_identifier=uniqueIdentifier)
                for each in allUrls:
                    each.status = "Failed"
                    each.logs = f"{er}"
                    each.save()
                print("Files Status Updated to Failed!")
            elif uploaded_files_info and files_owner == settings.USER_FILES_OWNER_NAME:
                allUserFiles = UserDocuments.objects.filter(
                    file_identifier=unique_identifief_for_batch
                )
                for user_file in allUserFiles:
                    user_file.embedding_status = "Failed"
                    user_file.embedded_at = datetime.datetime.now()
                    user_file.embedding_logs = f"{er}"
                    user_file.embedding_failure_reason = f"{er}"
                    user_file.save()
        except Exception as e:
            print(f"Error fething session files {e}")


class UserBriefView(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            brief_id = self.request.query_params.get("brief_id", 1)
            if not brief_id:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Breif Id is required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_brief = UserBrief.objects.get(id=brief_id)
            user_brief_json = UserBrief.convert_to_dict(user_brief)
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="User Breif Data Fetched Successfully.",
                    response={
                        "brief_data": user_brief_json,
                    },
                ),
                status=status.HTTP_200_OK,
            )
        except UserBrief.DoesNotExist:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=400,
                    message="Brief does not exisit",
                    response=None,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request, *args, **kwargs):
        try:
            print("i m aher ")
            data = json.loads(request.body)
            print(data)
            brief_id = data.get("brief_id")
            brief_data = data.get("brief_data")

            attorneys = brief_data.get("attorneys")
            conslusion = brief_data.get("conclusion")
            court_name = brief_data.get("court_name")
            court_term = brief_data.get("court_term")
            petitioner_name = brief_data.get("petitioner_name")
            questions_presented = brief_data.get("questions_presented")
            respondent_name = brief_data.get("respondent_name")
            statement_of_case = brief_data.get("statement_of_case")
            submitting_entity = brief_data.get("submitting_entity")
            summary_of_arguments = brief_data.get("summary_of_arguments")
            table_of_authorities = brief_data.get("table_of_authorities")
            title_of_brief = brief_data.get("title_of_brief")
            brief_arguments = brief_data.get("brief_arguments")

            user_brief = UserBrief.objects.get(id=brief_id)

            user_brief.court_name = court_name
            user_brief.court_term = court_term
            user_brief.petitioner_name = petitioner_name
            user_brief.respondent_name = respondent_name
            user_brief.title_of_brief = title_of_brief
            user_brief.submitting_entity = submitting_entity
            user_brief.attorneys = attorneys
            user_brief.questions_presented = questions_presented
            user_brief.table_of_authorities = table_of_authorities
            user_brief.statement_of_case = statement_of_case
            user_brief.summary_of_arguments = summary_of_arguments
            user_brief.conclusion = conslusion
            user_brief.save()
            print("saved")
            my_arguments = BriefArguments.objects.filter(user_brief=user_brief)
            for i, argument in enumerate(my_arguments):
                argument.title = brief_arguments[i].get("title")
                argument.description = brief_arguments[i].get("description")
                argument.save()

            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="User Breif Data Updated Successfully.",
                    response={},
                )
            )
        except UserBrief.DoesNotExist:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=400,
                    message="Brief does not exist",
                    response=None,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserBriefPreview(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            brief_id = self.request.query_params.get("brief_id", 1)
            if not brief_id:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Breif Id is required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_brief = UserBrief.objects.get(id=brief_id)
            user_brief_json = UserBrief.convert_to_preview_dict(user_brief)
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="User Breif Data Fetched Successfully.",
                    response={"brief_preview_data": user_brief_json},
                ),
                status=status.HTTP_200_OK,
            )
        except UserBrief.DoesNotExist:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=400,
                    message="Brief does not exisit",
                    response=None,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"An Error Occurred ERROR=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class JoinWaitingList(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            email = data.get("email")
            name = data.get("name")
            newInstance = WaitingList(
                name=name, email=email, date=datetime.datetime.now()
            )
            newInstance.save()
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="Added to waiting list",
                    response=None,
                ),
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"something went wrong=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetWaitingList(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            page_num = data.get("page_num", 1)
            items_per_page = 10

            waiting_list_qs = WaitingList.objects.all().order_by("-date")
            paginator = Paginator(waiting_list_qs, items_per_page)
            page_obj = paginator.get_page(page_num)

            rtnList = [
                {"name": li.name, "email": li.email, "date_joined": li.date}
                for li in page_obj
            ]

            responseObj = {
                "list": rtnList,
                "paginator": {
                    "total_items": paginator.count,
                    "total_pages": paginator.num_pages,
                    "current_page": page_num,
                    "items_per_page": items_per_page,
                },
            }
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="waitingList",
                    response=responseObj,
                ),
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(f"An error {e}")
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"something went wrong=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetJurisdictions(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="Jurisdictions Fetched Successfully!",
                    response=settings.COURT_LISTENER_JURISDICTIONS,
                ),
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(f"An error {e}")
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"something went wrong=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetCourtsByJurisdiction(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            jurisdiction_id = self.request.query_params.get("jurisdiction_id", None)
            if jurisdiction_id is None:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Jurisdiction Id is required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            courts_list = fetch_courtlistener_courts(jurisdiction_id)
            return Response(
                GenerateRequestResponse(
                    status=True,
                    status_code=200,
                    message="Courts Fetched Successfully!",
                    response=courts_list,
                ),
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(f"An error {e}")
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"something went wrong=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DownloadAsDocx(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    # permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            brief_id = self.request.query_params.get("brief_id", 1)
            if not brief_id:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Breif Id is required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_brief = UserBrief.objects.get(id=brief_id)
            user_brief_json = UserBrief.convert_to_dict(user_brief)
            docx_file = generate_docx_for_brief(user_brief_json)

            response = FileResponse(
                docx_file, as_attachment=True, filename="user_brief.docx"
            )
            return response
        except Exception as e:
            print(f"An error {e}")
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"something went wrong=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetTokenUsageByChat(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            chat_id = self.request.query_params.get("chat_id", None)
            if chat_id is None:
                return Response(
                    GenerateRequestResponse(
                        status=False,
                        status_code=400,
                        message="Chat Id is required!",
                        response=None,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Find all replies associated with the chat
            replies = Reply.objects.filter(query__chat_id=chat_id)
            # Aggregate token usage for these replies
            aggregated_data = ChatTokenUsage.objects.filter(
                reply__in=replies
            ).aggregate(
                total_input_tokens=Sum("input_tokens"),
                total_output_tokens=Sum("output_tokens"),
                total_usage_cost_in_cents=Sum("usage_cost_in_cents"),
            )
            # Ensure values are not None
            aggregated_data = {
                key: val if val is not None else 0
                for key, val in aggregated_data.items()
            }

            return JsonResponse(
                {
                    "status": True,
                    "status_code": 200,
                    "message": "Token Usage Fetched Successfully!",
                    "data": aggregated_data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(f"An error {e}")
            return Response(
                GenerateRequestResponse(
                    status=False,
                    status_code=500,
                    message=f"something went wrong=> {e}",
                    response=None,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class TokenUsageByUser(generics.GenericAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return JsonResponse(
                {
                    "status": False,
                    "status_code": 400,
                    "message": "User ID is required!",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Find all chats associated with the user
            chats = Chat.objects.filter(user_id=user_id)
            # Find all replies associated with these chats
            replies = Reply.objects.filter(query__chat__in=chats)
            # Aggregate token usage for these replies
            aggregated_data = ChatTokenUsage.objects.filter(
                reply__in=replies
            ).aggregate(
                total_input_tokens=Sum("input_tokens"),
                total_output_tokens=Sum("output_tokens"),
                total_usage_cost_in_cents=Sum("usage_cost_in_cents"),
            )
            # Ensure values are not None
            aggregated_data = {
                key: val if val is not None else 0
                for key, val in aggregated_data.items()
            }

            return JsonResponse(
                {
                    "status": True,
                    "status_code": 200,
                    "message": "Token Usage Fetched Successfully!",
                    "data": aggregated_data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return JsonResponse(
                {
                    "status": False,
                    "status_code": 500,
                    "message": f"Something went wrong: {e}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def check_user_payment_methods(customer_id):
    payment_methods = stripe.PaymentMethod.list(
        customer=customer_id,
        type='card'
    )
    if payment_methods['data']:
        return True
    else:
        return False


class CreateCheckoutSessionView(generics.GenericAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            customer_name = request.user.first_name
            stripe_customer_in_database = StripeCustomer.objects.filter(user=request.user).first()
            if not stripe_customer_in_database:
                stripe_customer = stripe.Customer.create(
                    email=request.user.username,
                    name=customer_name
                )
                stripe_customer_in_database = StripeCustomer.objects.create(user=request.user,
                                                            email=request.user.username,customerID=stripe_customer.id)

            has_valid_payment_method = check_user_payment_methods(stripe_customer_in_database.customerID)
            if not has_valid_payment_method:
                return Response(
                    {'error': 'No valid payment method available. Please update your payment method.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': 'Onboarding Fee',
                            },
                            'unit_amount': 100,
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                customer=stripe_customer_in_database.customerID,
                success_url='https://your-success-url.com',
                cancel_url='https://your-cancel-url.com',
            )
            print(checkout_session)
            # Return the session ID in the response
            return Response({'session_id': checkout_session['id']
                             }, status=status.HTTP_200_OK)

        except Exception as e:
            # Return error response
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def update_chat_types(request):
    if request.method == 'GET':
        chats_updated_count = Chat.objects.update(type=ChatType.CourtBrief.value)
        return JsonResponse({"status": "success", "updated_chats_count": chats_updated_count})
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


@csrf_exempt
def stripe_webhook_view(request):
    print("WE ARE HERE")
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None
    endpoint_secret = webhook_secret

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_id = session.get('customer')

        try:
            stripe_customer = StripeCustomer.objects.get(customerID=customer_id)
        except StripeCustomer.DoesNotExist:
            return JsonResponse({"error": "Customer not found"}, status=404)

        payment_amount = session['amount_total'] / 100.0
        currency = session['currency']
        payment_status = "PAID"

        successful_payment = SuccessfulPayment(
            stripe_customer=stripe_customer,
            payment_amount=payment_amount,
            currency=currency,
            payment_status=payment_status,
        )

        successful_payment.save()
        return JsonResponse({"message": "Payment recorded successfully"}, status=200)

    return JsonResponse({"message": "Event received"}, status=200)


class SuccessfulPaymentListView(generics.ListAPIView):
    queryset = SuccessfulPayment.objects.all()
    serializer_class = SuccessfulPaymentSerializer
