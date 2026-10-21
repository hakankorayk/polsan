from django.urls import path

from balances.views import BalanceView

urlpatterns = [path("api/balance/", BalanceView.as_view(), name="balance")]
