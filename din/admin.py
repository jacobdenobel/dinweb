from django.contrib import admin

from .models import AudioGenerator, Test, Stimulus, Experiment, Response, Questionary


def make_readonly(mod, extra_fields=None):
    class ReadOnlyInline(admin.TabularInline):
        model = mod
        extra = 0
        max_num = 0
        show_change_link = True
        readonly_fields = tuple([f.name for f in mod._meta.fields] + 
            (extra_fields if extra_fields else []))

    return ReadOnlyInline

def register_with_inline(mod, inline_mods, excludes = None, extra_fields = None, search_fieldset = ()):
    @admin.register(mod)
    class AdminModel(admin.ModelAdmin):
        inlines = inline_mods
        list_display_links = list_display = [
            field.name
            for field in mod._meta.fields
        ] + (extra_fields if extra_fields else [])
        search_fields = search_fieldset 
        exclude = excludes


register_with_inline(AudioGenerator, (make_readonly(Test), ))
register_with_inline(Test, (make_readonly(Experiment), ))
register_with_inline(Stimulus, (make_readonly(Response), ))
register_with_inline(Experiment, (make_readonly(Response), ))
register_with_inline(Questionary, (make_readonly(Experiment), ))
register_with_inline(Response, ())