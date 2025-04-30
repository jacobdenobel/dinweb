from django.db import models


class AudioGenerator(models.Model):
    name = models.CharField(max_length=100, default="raw")
    
class Test(models.Model):
    name = models.CharField(max_length=100, default="din")
    language = models.CharField(max_length=2, default='nl')
    n_questions = models.PositiveSmallIntegerField(default=24)
    starting_level = models.IntegerField(default=0)
    increment = models.IntegerField(default=2)
    min_level = models.IntegerField(default=-20)
    max_level = models.IntegerField(default=10)
    n_stimuli = models.IntegerField(default=128)
    audio_generator = models.ForeignKey(AudioGenerator, on_delete=models.CASCADE)

   
class Stimulus(models.Model):
    name = models.CharField(max_length=100)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    level = models.IntegerField()
    label = models.CharField(max_length=3)
    
    @property
    def filename(self):
        return ""    
    
class Questionary(models.Model):
    age = models.PositiveSmallIntegerField()
    normal_hearing = models.BooleanField()
    approve = models.BooleanField()
    first_time = models.BooleanField()
    first_language = models.BooleanField()   
    

class Experiment(models.Model):
    questionary = models.ForeignKey(Questionary, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    
    
class Response(models.Model):
    index = models.PositiveSmallIntegerField()
    stimulus = models.ForeignKey(Stimulus, on_delete=models.CASCADE)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    answer = models.CharField(max_length=3) 
    
