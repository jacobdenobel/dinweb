from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("questionary", views.questionary, name="questionary"),
    path("setup/<int:qid>/", views.setup, name='setup'),
    path("test_question/<int:qid>/", views.test_question, name="test_question"),
    path("question/<int:qid>/<int:tid>/<int:question_number>/", views.question, name="question"),
    path("results/", views.result_overview, name="result_overview"),
    path("results/<int:qid>/", views.results, name="results"),
    path("test_complete", views.test_complete, name="test_complete"),
]
  