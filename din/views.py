from django import forms
from django.shortcuts import render, redirect

from din.models import Questionary


def context_processor(request):
    keypad_rows = [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
    ]
    return {"keypad_rows": keypad_rows}


class QuestionaryForm(forms.ModelForm):
    class Meta:
        model = Questionary
        fields = ["age", "normal_hearing", "first_time", "first_language", "approve"]
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
        for field in self.Meta.fields[1:]:
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
    if request.method == "POST":
        return redirect("question", qid, 0)

    return render(request, "test_question.html")


def question(request, qid, question_number):
    total_questions = 2
    if request.method == "POST":
        user_answer = request.POST.get("answer")
        next_q = int(question_number) + 1
        
        if next_q > total_questions:
            return redirect('test_complete')
        
        return redirect('question', qid=qid, question_number=next_q)
        

    return render(request, "question.html", {
        'current': question_number,
        'total': total_questions,
        'audio_url': '',
    })
    
def test_complete(request):
    return render(request, "test_complete.html")


