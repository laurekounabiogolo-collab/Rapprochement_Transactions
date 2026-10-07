from django.urls import path

from chatbot import views

urlpatterns = [
    path("", views.discuter, name="chatbot"),
    path("intentions/", views.liste_intentions, name="chatbot_intentions"),
    path("intentions/nouvelle/", views.creer_intention, name="chatbot_creer_intention"),
    path("intentions/<int:pk>/modifier/", views.modifier_intention, name="chatbot_modifier_intention"),
]
