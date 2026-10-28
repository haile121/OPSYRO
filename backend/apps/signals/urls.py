from django.urls import path

from .views import SignalSubmitView

urlpatterns = [path("", SignalSubmitView.as_view(), name="signal-submit")]
