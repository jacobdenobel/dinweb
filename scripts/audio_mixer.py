import os
import argparse

import librosa
import soundfile as sf
import numpy as np

from rescale_sound import rms_db, scale_to_target_dbfs, TEST_DBFS

ROOT = os.path.dirname(os.path.dirname(__file__))
BASE_FOLDER = os.path.join(ROOT, 'din/static/audio/calibrated')
TEST_FOLDER = os.path.join(BASE_FOLDER, 'din')
NOISE_FILE = os.path.join(TEST_FOLDER, 'tripletnoise.wav')
SOURCE_FILES = [
    os.path.join(TEST_FOLDER, 'triplets', f)
    for f in
    os.listdir(os.path.join(TEST_FOLDER, 'triplets'))
    if os.path.isfile(os.path.join(TEST_FOLDER, 'triplets', f))
]

def mix(stim, noise, snr, relative_scaling=True):
    if relative_scaling:
        noise_power = np.mean(noise ** 2)
        stim_power = np.mean(stim ** 2)
        
        target_stim_power = noise_power * 10 ** (snr / 10)
        gain = np.sqrt(target_stim_power / stim_power)
    else:
        gain = 10 ** (snr / 20)
        
    stim_scaled = stim * gain
    mixed = stim_scaled + noise_segment
    return mixed
            



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min_snr", type=int, default=-20)
    parser.add_argument("--max_snr", type=int, default=10)
    parser.add_argument("--increment", type=int, default=1)
    parser.add_argument("--dont_rescale", action='store_true')
    parser.add_argument("--silence", type=float, default=.0)
    parser.add_argument("--save", action='store_true')
    args = parser.parse_args()
    
    np.random.seed(1993)
    
    noise, noise_sr = librosa.load(NOISE_FILE, sr=None)
    
    print("db_noise", rms_db(noise))
    for stim_file in sorted(SOURCE_FILES):    
        name = os.path.basename(stim_file)
        stim, stim_sr = librosa.load(stim_file, sr=None)
        
        stim = np.r_[
            np.zeros(int(stim_sr * args.silence)),
            stim,
            np.zeros(int(stim_sr * args.silence)),
        ]
        
        assert noise_sr == stim_sr
        assert len(noise) >= len(stim)
        
        print(name, "db ->", rms_db(stim))        
        
        for snr in range(args.min_snr, args.max_snr + args.increment, args.increment):
            print("mixing to snr", snr)
            
            start = np.random.randint(0, len(noise) - len(stim))
            noise_segment = noise[start:start+len(stim)].copy()
            mixed = mix(stim, noise_segment, snr)
                        
            print(rms_db(mixed))
            if not args.dont_rescale:
                mixed = scale_to_target_dbfs(mixed, TEST_DBFS)
                print(rms_db(mixed))
                
            if args.save:
                save_dir = os.path.join(TEST_FOLDER, f'snr{snr:+03d}')
                if not os.path.isdir(save_dir):
                    os.makedirs(save_dir)
                
                sf.write(os.path.join(save_dir, name), mixed, stim_sr)