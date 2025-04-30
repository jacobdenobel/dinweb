import base64
import os

import streamlit as st
import numpy as np
from scipy.optimize import curve_fit
from scipy.special import expit

import matplotlib.pyplot as plt

from one_up_one_down import DINOneUpOneDown, DATA, SOUNDS, AVAILABLE_TESTS


st.title("🎛️ DIN test")


def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio style="width: 100%;" controls autoplay="true" preload>
                <source src="data:audio/mp3;base64,{b64}" type="audio/wav">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )


def logistic(x, alpha, beta, gamma, lambda_):
    return gamma + (1 - gamma - lambda_) * expit((x - alpha) / beta)


def init_state():
    for key in (
        "start_test",
        "show_digits",
        "can_play",
        "has_loaded",
    ):
        if key not in st.session_state:
            setattr(st.session_state, key, False)

    if "test" not in st.session_state:
        st.session_state.test = DINOneUpOneDown(0)


init_state()


if not st.session_state.start_test:
    st.markdown(
        """ 
        Blabla dit is een din test klik op start test om te beginnen
        
        of klik op een sessie op de resultaten te zien
        """
    )
    st.divider()
    option_version = st.selectbox(
        "Welke versie van de test will je uitvoeren?",
        AVAILABLE_TESTS,
    )
    st.session_state.test.test_folder = os.path.join(SOUNDS, option_version)

    if st.button("Start test", use_container_width=True):
        st.session_state.start_test = True
        st.session_state.can_play = True
        st.session_state.test.reset()
        st.rerun()

    st.divider()
    option_load = st.selectbox(
        "Welke resultaten wil je bekijken?",
        sorted(os.listdir(DATA)),
    )
    if st.button("Load results", use_container_width=True):
        st.session_state.test = DINOneUpOneDown.load(os.path.join(DATA, option_load))
        st.session_state.start_test = True
        st.session_state.can_play = False
        st.session_state.has_loaded = True
        st.rerun()


if (
    st.session_state.start_test
    and st.session_state.can_play
    and not st.session_state.test.done
):
    st.markdown(
        f""" 
        Voortgang:
        {st.session_state.test.n_presentations} / {st.session_state.test.n_total_presentations}
        """
    )
    if st.button("Speel het volgende geluid"):
        st.session_state.test.ask()
        st.session_state.can_play = False
        st.session_state.show_digits = True
        st.rerun()

if (
    st.session_state.start_test
    and st.session_state.show_digits
    and not st.session_state.test.done
):
    autoplay_audio(st.session_state.test.current_file)

    st.write(f"Klik op de toetsen hieronder")
    digits = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["", "0", "X"]]

    # Loop through rows
    for row in digits:
        cols = st.columns(3)
        for i, digit in enumerate(row):
            if digit == "X" and cols[i].button(digit, use_container_width=True):
                st.session_state.test.current_response = ""
                st.rerun()

            elif digit.isdigit():
                if cols[i].button(digit, use_container_width=True):
                    if st.session_state.test.tell(digit):
                        st.session_state.can_play = True
                        st.session_state.show_digits = False
                        st.rerun()
            else:
                cols[i].empty()


def check(s1, s2):
    score = 0
    for c1, c2 in zip(s1, s2):
        score += c1 == c2
    return score


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


def fit_curve(bins, bin_correct, trials, random_lvl):
    psycho = np.zeros(len(bins))
    mask = np.nonzero(trials)
    psycho[mask] = bin_correct[mask] / trials[mask]

    ma = mask[0][-1]
    psycho[ma:] = psycho[ma]
    mb = mask[0][0]
    psycho[:mb] = min(random_lvl, psycho[mb])
    # print(psycho)

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
    print(alpha, beta, gamma, lambda_)
    x50 = alpha + beta * np.log((0.5 - gamma) / (0.5 - lambda_))

    x_fit = np.linspace(-20, 10.0, 200)
    y_fit = logistic(x_fit, alpha, beta, gamma, lambda_)
    return x50, x_fit, y_fit, bins[mask], psycho[mask]


def plot_test_results(levels):
    srt_levels = np.r_[levels[-20:], st.session_state.test.current_level]
    srt = np.mean(srt_levels)
    f, ax = plt.subplots()
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
    st.pyplot(f)


def plot_psychometric(levels, n_correct):
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

    f2, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
    inner(ax1, bin_words_correct, trials * 3, -11, -6, 1 / 10)
    inner(ax2, bin_correct, trials, -8, -3, 1 / 120)

    ax1.set_ylabel("percentage correct (digit)")
    ax2.set_ylabel("percentage correct (triplet)")
    st.pyplot(f2)


if st.session_state.start_test and st.session_state.test.done:
    st.markdown(
        f"""
        ### Resultaten test: {st.session_state.test.test_name}
        """
    )

    levels = np.array([h[0] for h in st.session_state.test.history])
    n_correct = np.array([check(h[3], h[4]) for h in st.session_state.test.history])

    plot_test_results(levels)
    plot_psychometric(levels, n_correct)

    cols = st.columns(2)
    # if not st.session_state.has_loaded:
    #     st.session_state.test.save()

    if cols[0].button("Save"):
        st.session_state.test.save()
        st.success("session saved!")

    if cols[1].button("Restart"):
        st.session_state.start_test = False
        st.rerun()
