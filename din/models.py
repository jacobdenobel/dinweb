from django.conf import settings
from django.db import models


class Test(models.Model):
    language = models.CharField(max_length=2, default="nl")
    n_questions = models.PositiveSmallIntegerField(default=24)
    starting_level = models.IntegerField(default=0)
    increment = models.IntegerField(default=2)
    min_level = models.IntegerField(default=-20)
    max_level = models.IntegerField(default=10)
    n_stimuli = models.IntegerField(default=128)
    name = models.CharField(max_length=100, default="din")
    audio_generator = models.CharField(max_length=100, default="din")
    active = models.BooleanField()


class Stimulus(models.Model):
    name = models.CharField(max_length=100)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    level = models.IntegerField()
    label = models.CharField(max_length=3)

    @property
    def filename(self):
        return f"{self.label}.wav"
    
    @property
    def static_url(self):
        return (
            f"{settings.MEDIA_URL}"
            f"{self.test.name}_{self.test.audio_generator}"
            f"/snr{self.level:+03d}/{self.filename}")


class Questionary(models.Model):
    age = models.PositiveSmallIntegerField()
    normal_hearing = models.BooleanField()
    approve = models.BooleanField()
    first_time = models.BooleanField()
    first_language = models.BooleanField()


class Response(models.Model):
    index = models.PositiveSmallIntegerField()
    questionary = models.ForeignKey(Questionary, on_delete=models.CASCADE)
    stimulus = models.ForeignKey(Stimulus, on_delete=models.CASCADE, null=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    answer = models.CharField(max_length=3)

    @property
    def answered(self):
        return len(self.answer) != 0

    @property
    def correct(self):
        if self.answered:
            return self.answer == self.stimulus.label

    @property
    def n_correct(self):
        n = 0
        if self.answered:
            for a, c in zip(self.answer, self.stimulus.label):
                n += int(a == c)
        return n
    
    @staticmethod
    def get_next_level(previous_question: "Response"):
        if previous_question.correct:
            return max(
                previous_question.stimulus.level - previous_question.test.increment,
                previous_question.test.min_level,
            )
        return min(
            previous_question.stimulus.level + previous_question.test.increment, previous_question.test.max_level
        )
        
    def get_level(self):
        if self.index == 1:
            return self.test.starting_level

        previous_question = Response.objects.get(
            index=self.index - 1,
            questionary=self.questionary,
            test=self.test,
        )
        return Response.get_next_level(previous_question)
