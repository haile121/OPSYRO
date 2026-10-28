from django.urls import path

from .views import FeedbackSubmitView, PublicResponsesView

urlpatterns = [
    path("", FeedbackSubmitView.as_view(), name="feedback-submit"),
    path("public/sessions/<uuid:session_token>/responses/", PublicResponsesView.as_view(), name="public-session-responses"),
]
