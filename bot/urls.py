from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from . import views
from bot.graphene_ql.schema import schema


urlpatterns = [
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True,schema=schema))),
    path('SignupView', views.SignupView.as_view(), name='SignupView'),
    path('LoginView', views.LoginView.as_view(), name='LoginView'),
    path('ChangePasswordView', views.ChangePasswordView.as_view(), name='ChangePasswordView'),
    path('UserProfileView', views.UserProfileView.as_view(), name='UserProfileView'),
    path('ChatView', views.ChatView.as_view(), name='ChatView'),
    path('ChatDetailView', views.ChatDetailView.as_view(), name='ChatView'),
    path('UploadSystemDocuments', views.UploadSystemDocuments.as_view(), name='UploadSystemDocuments'),
    path('UploadUserDocuments', views.UploadUserDocuments.as_view(), name='UploadUserDocuments'),
    path('UserDocumentsByChat', views.UserDocumentsByChat.as_view(), name='UserDocumentsByChat'),
    path('ServeUserDocument', views.ServeUserDocument.as_view(), name='ServeUserDocument'),
    path('UserBriefView', views.UserBriefView.as_view(), name='UserBriefView'),
    path('UserBriefPreview', views.UserBriefPreview.as_view(), name='UserBriefPreview'),
    path('JoinWaitingList', views.JoinWaitingList.as_view(), name='JoinWaitingList'),
    path('GetWaitingList', views.GetWaitingList.as_view(), name='GetWaitingList'),
    path('GetJurisdictions', views.GetJurisdictions.as_view(), name='GetJurisdictions'),
    path('GetCourtsByJurisdiction', views.GetCourtsByJurisdiction.as_view(), name='GetCourtsByJurisdiction'),
    path('GetTokenUsageByChat', views.GetTokenUsageByChat.as_view(), name='GetTokenUsageByChat'),
    path('DownloadAsDocx', views.DownloadAsDocx.as_view(), name='DownloadAsDocx'),
    path('CreateCheckoutSessionView', views.CreateCheckoutSessionView.as_view(), name='CheckoutSession'),
    path('update-chat-types/', views.update_chat_types, name='update_chat_types'),
    path('successful-payments/', views.SuccessfulPaymentListView.as_view(), name='successful-payment-list'),
    path('stripe_webhook/', views.stripe_webhook_view, name='stripe_webhook_view'),
]
