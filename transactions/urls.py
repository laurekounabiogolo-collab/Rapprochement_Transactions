from django.urls import path

from .views import liste_transactions, modifier_transaction, supprimer_transaction

urlpatterns = [
    path("", liste_transactions, name="liste_transactions"),
    path("<int:pk>/modifier/", modifier_transaction, name="modifier_transaction"),
    path("<int:pk>/supprimer/", supprimer_transaction, name="supprimer_transaction"),
]
