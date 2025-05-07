import numpy as np
import matplotlib.pyplot as plt

from django.core.management.base import BaseCommand
from din.models import Questionary, Test, Response
from din.utils import get_plots

class Command(BaseCommand):
    help = "Describe what this command does"

    def handle(self, *args, **options):
        entries = Questionary.objects.all()

        for entry in entries:
            responses = Response.objects.filter(questionary=entry)
            tests = responses.values_list("test_id", flat=True).distinct()
            
            for test in tests:
                test = Test.objects.get(id=test)
                if not test.active:
                    continue
                test_responses = responses.filter(test=test).order_by("index")
                if test_responses.count() != test.n_questions:
                    print(entry, "has not answered all questions for test", test)
                    continue

                levels = np.array([x.stimulus.level for x in test_responses])
                n_correct = np.array([x.n_correct for x in test_responses])
                srt_levels = np.r_[
                    levels[-20:], Response.get_next_level(test_responses.last())
                ]
                print(len(srt_levels))
                srt = np.mean(srt_levels)
                record = [
                    entry.id,
                    entry.age,
                    test.name,
                    test.audio_generator,
                    srt,
                ]
                print(record)
                fig = get_plots(levels, n_correct, srt)
                fig.suptitle(f"{entry.id} {test.name}_{test.audio_generator}")
                plt.tight_layout()
            plt.show()
