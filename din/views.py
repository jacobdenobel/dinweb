import random
import io
import urllib
import base64

import numpy as np
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from din.models import Questionary, Test, Response, Stimulus
from din.utils import plot_psychometric, plot_test_results, get_plots

def context_processor(request):
    keypad_rows = [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
        ["",  "0", ""],
    ]
    return {"keypad_rows": keypad_rows}


class QuestionaryForm(forms.ModelForm):
    class Meta:
        model = Questionary
        fields = ["age", "normal_hearing", "first_time", "first_language", "approve"]
        required_checks = ["normal_hearing", "first_language", "approve"]
        labels = {
            "age": "Wat is uw leeftijd?",
            "normal_hearing": "Heeft u (voor zover u weet) een normaal gehoor?",
            "first_time": "Is dit de eerste keer dat u deze test doet?",
            "first_language": "Is Nederlands uw eerste of moedertaal?",
            "approve": "Ik geef toestemming voor het gebruik van mijn (anonieme) gegevens voor onderzoeksdoeleinden.",
        }
        help_texts = {
            "age": "Dit helpt ons uw resultaat te vergelijken met mensen van dezelfde leeftijdsgroep.",
            "normal_hearing": 'Kies "Ja" als u geen bekende gehoorproblemen of gehoorverlies heeft.',
            "first_time": "Deze informatie helpt ons begrijpen of ervaring invloed heeft op de resultaten.",
            "first_language": "De test is in het Nederlands. Als u een andere moedertaal heeft, kan dat invloed hebben op het resultaat.",
            "approve": "Uw gegevens worden vertrouwelijk behandeld en alleen gebruikt voor wetenschappelijk onderzoek.",
        }

    def clean(self):
        cleaned_data = super().clean()
        for field in self.Meta.required_checks:
            if not cleaned_data.get(field):
                self.add_error(field, "Vergeet deze checkbox niet!")
        return cleaned_data


def index(request):
    return render(request, "index.html")


def questionary(request):
    if request.method == "POST":
        form = QuestionaryForm(request.POST)
        if form.is_valid():
            new_instance = form.save()
            return redirect("setup", qid=new_instance.pk)

        return render(request, "questionary.html", {"form": form})

    form = QuestionaryForm()
    return render(request, "questionary.html", {"form": form})


def setup(request, qid):
    return render(request, "setup.html", {"qid": qid})


def test_question(request, qid):
    tests = Test.objects.filter(active=True)
    if request.method == "POST":
        random_test = random.choice(tests.values_list('pk', flat=True))
        return redirect("question", qid, random_test, 1)

    return render(request, "test_question.html", {"n_tests": tests.count()})

def get_available_tests(questionary):
    responses = Response.objects.filter(questionary=questionary)
    test_already_done = set(responses.values_list('test_id', flat=True).distinct())
    available_tests = set(Test.objects.filter(active=True).values_list('pk', flat=True))
    return list(available_tests - test_already_done)


def get_next_url(request, test, questionary):
    parts = request.path.split("/")
    next_q = int(parts[-2]) + 1
    
    if next_q > test.n_questions:
        next_tests = get_available_tests(questionary)
        if len(next_tests) == 0:
            return "/test_complete"
        parts[-3] = str(random.choice(next_tests))
        parts[-2] = str(1)
    else:
        parts[-2] = str(next_q)
    
    return "/".join(parts)
    

def question(request, qid, tid, question_number):
    test = Test.objects.get(pk=tid)
    questionary = Questionary.objects.get(pk=qid)
    
    response, _ = Response.objects.get_or_create(
        index=question_number,
        questionary=questionary,
        test=test, 
    )
    
    available_tests = get_available_tests(questionary)
    if not response.stimulus:
        stims = Stimulus.objects.filter(test=test, level=response.get_level())
        response.stimulus = random.choice(stims)
        response.save()
    
    if request.method == "POST":
        user_answer = request.POST.get("answer").strip()
        if not response.answered:
            response.answer = user_answer
            response.save()
            
        next_q = int(question_number) + 1
        if next_q > test.n_questions:
            if len(available_tests) == 0:
                return redirect('test_complete')
            next_test = random.choice(available_tests)
            return redirect('question', qid, next_test, 1)
        return redirect('question', qid, tid, next_q)
    
    n_tests = Test.objects.filter(active=True).count()
    nth_test = Response.objects.filter(
        questionary=questionary).values_list(
            'test_id', flat=True
    ).distinct().count()
    return render(request, "question.html", {
        'response': response,
        'current': question_number,
        'total': test.n_questions,
        'nth_test': nth_test,
        'total_tests': n_tests,
        'next_url': get_next_url(request, test, questionary),
    })
    
def test_complete(request):
    return render(request, "test_complete.html")


def plot_to_data(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format='png',  transparent=True)
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    return uri

def get_boxplot_snr(tests: Test) -> str:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.violinplot(
        [t.get_snrs() for t in tests],
        showmedians=True,        
    )
    ax.set_xticks([y + 1 for y in range(len(tests))],
                  labels=[f"{t.name}_{t.audio_generator}" for t in tests])
    ax.grid()
    return plot_to_data(fig)
    


@login_required
def result_overview(request):
    questionaries = Questionary.objects.all() 
    tests = Test.objects.all()
    
    return render(request, "results_overview.html", context={
        "questionaries": questionaries,
        "tests": tests,
        "boxplot": get_boxplot_snr(tests)
    })

@login_required
def results(request, qid):
    questionary = Questionary.objects.get(pk=qid)
    responses = questionary.response_set.filter()
    tests = responses.values_list("test", flat=True).distinct()
    
    test_results = []
    for test in tests:
        test = Test.objects.get(pk=test)
        test_responses = responses.filter(test=test).order_by("index")
        completed = test_responses.count() == test.n_questions
        if not completed:
            continue
        
        levels = np.array([x.stimulus.level for x in test_responses])
        n_correct = np.array([x.n_correct for x in test_responses])
        srt_levels = np.r_[
            levels[-20:], Response.get_next_level(test_responses.last())
        ]       
        srt = np.mean(srt_levels)
        
        fig = get_plots(levels, n_correct, srt)
        test_results.append(
            {
                "test": test,
                "srt": srt,
                "result_plot": plot_to_data(fig),
            }
        )
        
    return render(request, "results.html", context={
        "test_results": test_results,
        "questionary": questionary
    })
