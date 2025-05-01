import numpy as np
from scipy.optimize import curve_fit
from scipy.special import expit

import matplotlib.pyplot as plt

from django.core.management.base import BaseCommand
from din.models import Questionary, Test, Response


def get_bins(levels, n_correct, lb=-20, ub=10):
    bins = np.arange(lb, ub, step=2)
    trials = np.zeros(len(bins))
    bin_words_correct = np.zeros(len(bins))
    bin_correct = np.zeros(len(bins))
    mask = np.digitize(levels, bins, right=True)
    for i, m in enumerate(mask):
        trials[m] += 1
        bin_correct[m] += n_correct[i] == 3
        bin_words_correct[m] += n_correct[i]
    return bins, bin_correct, bin_words_correct, trials


def logistic(x, alpha, beta, gamma, lambda_):
    return gamma + (1 - gamma - lambda_) * expit((x - alpha) / beta)


def fit_curve(bins, bin_correct, trials, random_lvl):
    psycho = np.zeros(len(bins))
    mask = np.nonzero(trials)
    psycho[mask] = bin_correct[mask] / trials[mask]

    ma = mask[0][-1]
    psycho[ma:] = psycho[ma]
    mb = mask[0][0]
    psycho[:mb] = min(random_lvl, psycho[mb])

    (alpha, beta, gamma, lambda_), *_ = curve_fit(
        lambda x, alpha, beta, gamma, lambda_: logistic(x, alpha, beta, gamma, lambda_),
        bins,
        psycho,
        p0=[-11.0, 0.65, 0.15, -0.0033],
        bounds=(
            [-30.0, 0.001, 1e-10, -0.1],
            [-0.0, 5.0, 1.0, 0.1],
        ),
    )
    x50 = alpha + beta * np.log((0.5 - gamma) / (0.5 - lambda_))
    x_fit = np.linspace(-20, 10.0, 200)
    y_fit = logistic(x_fit, alpha, beta, gamma, lambda_)
    return x50, x_fit, y_fit, bins[mask], psycho[mask]


def plot_test_results(levels, srt, ax):
    x = np.arange(1, 1 + len(levels))
    ax.plot(x, levels, linestyle="dashed", marker="*")
    ax.plot(
        x,
        np.ones(len(x)) * srt,
        linestyle="dashed",
        alpha=0.5,
        color="magenta",
        label="SRT",
    )
    ax.set_ylabel("SNR level (dB)")
    ax.set_xlabel("presentation #")
    ax.set_xticks(x)
    ax.legend()
    ax.grid()


def plot_psychometric(levels, n_correct, ax1, ax2):
    bins, bin_correct, bin_words_correct, trials = get_bins(levels, n_correct)

    def inner(ax, bin_correct_, trials_, nh_db, ci_db, rnd_lvl):
        x50, x_fit, y_fit, mbins, mpsycho = fit_curve(
            bins, bin_correct_, trials_, rnd_lvl
        )
        ax.plot(mbins, mpsycho, linestyle="dashed", marker="*")
        ax.plot(x_fit, y_fit, color="magenta", alpha=0.5)
        ax.scatter(
            x50, 0.5, color="black", marker="o", label=f"50% at {x50:.2f} dB SNR"
        )
        ax.set_xlabel("db SNR")
        ax.grid()
        ax.set_yticks(np.arange(0, 1.1, 0.1))
        ax.scatter(nh_db, 0.5, color="blue", marker="_")
        ax.vlines(
            nh_db,
            0,
            0.5,
            label=f"50% NH ({nh_db} dB)",
            color="blue",
            zorder=-10,
            # linestyle="dashed",
            alpha=0.4,
        )
        ax.scatter(ci_db, 0.5, color="red", marker="_")
        ax.vlines(
            ci_db,
            0,
            0.5,
            label=f"50% CI ({ci_db} dB)",
            color="red",
            zorder=-10,
            # linestyle="dashed",
            alpha=0.4,
        )
        ax.legend(fontsize=7, loc="lower right")
        ax.set_ylim(0, 1.05)

    inner(ax1, bin_words_correct, trials * 3, -11, -6, 1 / 10)
    inner(ax2, bin_correct, trials, -8, -3, 1 / 120)

    ax1.set_ylabel("percentage correct (digit)")
    ax2.set_ylabel("percentage correct (triplet)")


def get_plots(levels, n_correct, srt):
    fig = plt.figure(figsize=(15, 4))
    ax1 = fig.add_subplot(131)
    ax2 = fig.add_subplot(132) 
    ax3 = fig.add_subplot(133, sharey=ax2)    
    plot_test_results(levels, srt, ax1)
    plot_psychometric(levels, n_correct, ax2, ax3)
    plt.tight_layout()
    return fig    
    
    
    
    

class Command(BaseCommand):
    help = "Describe what this command does"

    def handle(self, *args, **options):
        entries = Questionary.objects.all()

        for entry in entries:
            responses = Response.objects.filter(questionary=entry)
            tests = responses.values_list("test_id", flat=True).distinct()
            for test in tests:
                test = Test.objects.get(id=test)
                test_responses = responses.filter(test=test).order_by("index")
                if test_responses.count() != test.n_questions:
                    print(entry, "has not answered all questions for test", test)
                    continue

                levels = np.array([x.stimulus.level for x in test_responses])
                n_correct = np.array([x.n_correct for x in test_responses])
                srt_levels = np.r_[
                    levels[-20:], Response.get_next_level(test_responses.last())
                ]
                srt = np.mean(srt_levels)
                record = [
                    entry.id,
                    entry.age,
                    test.name,
                    test.audio_generator.name,
                    srt,
                ]
                print(record)
                fig = get_plots(levels, n_correct, srt)
                fig.suptitle(f"{entry.id} {test.name}_{test.audio_generator.name}")
                plt.tight_layout()
                plt.show()
