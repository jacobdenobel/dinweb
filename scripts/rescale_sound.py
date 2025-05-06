import os
import argparse

import librosa
import soundfile as sf
import numpy as np


LOUD_DBFS = -15
TEST_DBFS = -20 
SOFT_DBFS = -40
FS = 44100


def rms_db(y):
    rms = np.sqrt(np.mean(y**2))
    return 20 * np.log10(rms)

def scale_to_target_dbfs(y, target_dbfs):
    current_dbfs = rms_db(y)
    diff = target_dbfs - current_dbfs
    gain = 10 ** (diff / 20)
    return y * gain
    
def rescale(path, db, save = None):
    y, sr = librosa.load(path, sr=FS)
    print(rms_db(y))
    y_scaled = scale_to_target_dbfs(y, db)
    print(rms_db(y_scaled))
    
    if save:
        sf.write(save, y_scaled, FS)
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--soft", action='store_true')
    parser.add_argument("--loud", action='store_true')
    parser.add_argument("--save", type=str, default=None)
    parser.add_argument("--save_inplace", action='store_true')
    args = parser.parse_args()
    
    
    if args.loud:
        db = LOUD_DBFS   
    elif args.soft:
        db = SOFT_DBFS
    else: 
        db = TEST_DBFS
        
    if args.save_inplace:
        args.save = args.path
    
    if os.path.isfile(args.path):   
        rescale(args.path, db, args.save)

    if os.path.isdir(args.path):
        if args.save and not os.path.isdir(args.save):
            os.makedirs(args.save)
        
        for f in os.listdir(args.path):
            path = os.path.join(args.path, f)
            save = args.save if args.save is None else os.path.join(args.save, f)
            if os.path.isfile(path):
                rescale(path, db, save)
            elif os.path.isdir(path):
                for f in os.listdir(path):
                    f_path = os.path.join(path, f)
                    f_save = args.save if args.save is None else os.path.join(save, f)
                    if os.path.isfile(f_path):
                        try:
                            rescale(f_path, db, f_save)
                        except:
                            print(f_path)
        
