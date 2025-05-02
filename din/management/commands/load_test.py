import os

from django.core.management.base import BaseCommand
from django.conf import settings
from din.models import Test, Stimulus



class Command(BaseCommand):
    help = "Describe what this command does"
    
    def add_arguments(self, parser):
        parser.add_argument('name', type=str)
        parser.add_argument('--test_name', type=str, default='din')
        parser.add_argument('--language', type=str, default='nl')
        parser.add_argument('--n_questions', type=int, default=24)
        parser.add_argument('--starting_level', type=int, default=0)
        parser.add_argument('--increment', type=int, default=2)
        parser.add_argument('--min_level', type=int, default=-20)
        parser.add_argument('--max_level', type=int, default=10)
        parser.add_argument('--active', action='store_true')      
        

    def handle(self, *args, **options):
        base_folder = settings.MEDIA_ROOT

        data_sets = os.listdir(base_folder)
        if options['name'] not in data_sets:
            print(options['name'], "not found")
            return 
        
        data_set, *_ = [d for d in data_sets if d == options['name']]
        generator_name = options['name'].replace("din_", '')
        test, created = Test.objects.get_or_create(
            name=options['test_name'],
            language=options['language'],
            n_questions=options['n_questions'],
            starting_level=options['starting_level'],
            min_level=options['min_level'],
            max_level=options['max_level'],
            increment=options['increment'],           
            audio_generator=generator_name,
            active=options['active']
        )
        if not created:
            print("test already exists")
            return 
        
        stimuli = []
        for snr in os.listdir(base_folder / data_set):
            level = int(snr.split("snr")[1])
            for wav in os.listdir(base_folder / data_set / snr ):
                name = f"{snr}_{wav}"
                label, *_ = wav.split(".")
                stim = Stimulus(name=name, test=test, level=level, label=label)
                stimuli.append(stim)

        n_expected = int((test.max_level - test.min_level) / test.increment) * test.n_stimuli
        
        if n_expected != len(stimuli):
            print(f"the number of files {len(stimuli)} is different "
                  f"from the expected number of files {n_expected}")

            test.delete()
            return 
        
        
        res = Stimulus.objects.bulk_create(stimuli)
        print("created", len(res))