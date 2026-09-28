from django.urls import path

from .views import liste_transactions, modifier_transaction

urlpatterns = [
    path("", liste_transactions, name="liste_transactions"),
    path("<int:pk>/modifier/", modifier_transaction, name="modifier_transaction"),
]
