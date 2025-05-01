function mixsnr(speech_dir, noise_dir, hrir_speech_dir, hrir_noise_dir, target_dir, snrs, num_samples, sil, seed, verbose)
% usage: mixsnr(speech_dir, noise_dir, hrir_speech_dir, hrir_noise_dir, target_dir, snrs, num_samples, sil, seed, verbose)
%
% Load wav files in "speech_dir" and "noise_dir".
% Padd the speech signal with "sil" seconds of silence.
% Mix the speech signals with random portions of the noise signals.
% until "num_samples" recordings are reached for each SNR in "snr".
% Optionally process speech and noise signals with impulse responses in "hrir_speech_dir" and "hrir_noise_dir", respectively.
% Save the results to target_dir.
% A random "seed" must be provided.
% The output is structured for use with FADE.
%

% Copyright (C) 2014-2018 Marc René Schädler
if ~is_octave()
  rng(seed, 'twister');
end

min_noise_duration = 60; % seconds
crossfade_overlap = 0.25; % seconds

speech_files = dir([speech_dir filesep '*.wav']);
speech_files = {speech_files.name};
[~, shuffle_idx] = sort(rand(1,numel(speech_files)));
speech_files = speech_files(shuffle_idx);

noise_files = dir([noise_dir filesep '*.wav']);
noise_files = {noise_files.name};

num_speech_files = length(speech_files);
num_noise_files = length(noise_files);
num_hrir_speech_files = length(hrir_speech_files);
num_hrir_noise_files = length(hrir_noise_files);
num_snrs = length(snrs);

speech = cell(size(speech_files));
noise = cell(size(noise_files));
hrir_speech = cell(size(hrir_speech_files));
hrir_noise = cell(size(hrir_noise_files));

total = num_noise_files.*num_snrs.*num_samples;


for i=1:num_noise_files
  [signal, fs] = audioread([noise_dir filesep noise_files{i}]);
  signal = single(signal);
 
  assert(checkfs(fs),'different sample frequencies!');
  % extend noise to minimum length
  if size(signal,1) < fs.*min_noise_duration
    signal = crossfade_extend(signal, round(fs.*crossfade_overlap), ceil(fs.*min_noise_duration));
  end
  noise{i} = signal;
  [~, noise_files{i}] = fileparts(noise_files{i});
  if ~isempty(strfind(noise_files{i}, '_'))
    noise_files{i} = strrep(noise_files{i},'_','-');
  end
end

% Load speech files

for i=1:num_speech_files
  [signal, fs] = audioread([speech_dir filesep speech_files{i}]);
  signal = single(signal);
  assert(checkfs(fs), 'different sample frequencies!');
  speech{i} = [zeros(round(fs*sil(1)),size(signal,2)); signal; zeros(round(fs*sil(2)),size(signal,2))];
  [~, speech_files{i}] = fileparts(speech_files{i});
end



fs = checkfs;
t0 = 0;
tic;
for inoi=1:num_noise_files
  noise_signal = noise{inoi};
  noise_dir = [target_dir filesep noise_files{inoi}];
  if ~exist(noise_dir,'dir');
    mkdir(noise_dir);
  end
  for isnr=1:num_snrs
    snr = snrs(isnr);
    snr_dir = [noise_dir filesep sprintf('snr%+03i',snr)];
    % MUTEX to prevent concurrent threads to generate the same condition

    if unix(['mkdir "' snr_dir '" 2>/dev/null']) == 0
      for isam=1:num_samples
        rep = floor((isam-1)./num_speech_files);
        ispe = isam - num_speech_files.*rep;
        sample_dir = [snr_dir filesep sprintf('rep%02d',rep)];
        if ~exist(sample_dir,'dir');
          mkdir(sample_dir);
        end
        filename = [sample_dir filesep speech_files{ispe} '.wav'];
        speech_signal = speech{ispe};
        
        prespeech_signal = speech{randi(length(speech),1)};
        start = 1+floor(rand(1).*(size(noise_signal,1)-size(speech_signal,1)-1));
        stop = start+size(speech_signal,1)-1;
        noise_tmp = noise_signal(start:stop,:);
     
        % Apply gain and mix signals
        signal = speech_signal .* single(10.^(snr./20)) + noise_tmp;
        assert(checkchannels(size(signal,2)),'different number of channels!');
        audiowrite(filename, signal, fs, 'BitsPerSample', 32);
        fprintf('.');
      end
    end
  end
end

end

function signal = crossfade_extend(signal, crossfade, len)
while (size(signal,1) < len)
  fade = repmat(linspace(0,1,crossfade).',1,size(signal,2));
  signal = [ ...
    signal(1:end-crossfade,:); ...
    signal(1:crossfade,:).* sqrt(fade) + ...
    signal(end-crossfade+1:end,:) .* sqrt(1-fade); ...
    signal(crossfade:end,:) ...
    ];
end
end

function out = checkfs(in)
persistent fs;
if nargin < 1
  out = fs;
else
  if isempty(fs)
    fs = in;
  end
  out = fs == in;
end
end

function out = checkchannels(in)
persistent channels;
if nargin < 1
  out = channels;
else
  if isempty(channels)
    channels = in;
  end
  out = channels == in;
end
end
