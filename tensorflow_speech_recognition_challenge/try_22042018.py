#!usr/bin/python3
import os
from os.path import isdir, join
from pathlib import Path
import pandas as pd

import numpy as np
import librosa
from scipy.fftpack import fft
from scipy import signal
from scipy.io import wavfile
from sklearn.decomposition import PCA

import matplotlib.pyplot as plt
# import seaborn as sns
import IPython.display as ipd
import librosa.display

from keras import backend as K
from keras.layers import GRU
from keras.models import Sequential
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
from keras.layers.core import Activation
from keras.layers.core import Flatten
from keras.layers.core import Dense, Dropout
from keras.utils import np_utils
from keras.optimizers import SGD, RMSprop, Adam
from tensorflow.python.platform import gfile
from os import listdir
from os.path import isfile, join
import csv
from keras.models import load_model

# import plotly.offline as py
# py.init_notebook_mode(connected=True)
# import plotly.graph_objs as go
# import plotly.tools as tls


# global variables
NB_EPOCH = 5
BATCH_SIZE = 128
VERBOSE = 1
OPTIMIZER = Adam()
VALIDATION_SPLIT = 0.2
AUDIO_ROWS, AUDIO_COLS = 99, 161
NB_CLASSES = 12
DROPOUT = 0.3
INPUT_SHAPE = (AUDIO_ROWS, AUDIO_COLS)
label_to_index_map = {}
THRESHOLD = 500




# define a LeNet network
class LeNet:
    def build(input_shape, classes):
        model = Sequential()
        
        model.add(Conv1D(20, kernel_size=5, padding='same', input_shape=input_shape)) #layer 1
        model.add(Activation('relu'))
        model.add(MaxPooling1D(pool_size=2, strides=2))
#         model.add(Dropout(DROPOUT))
        
        model.add(Conv1D(50, kernel_size=5, border_mode='same')) #layer 2
        model.add(Activation('relu'))
        model.add(MaxPooling1D(pool_size=2, strides=2))
        model.add(Dropout(DROPOUT))
        
        model.add(Conv1D(100, kernel_size=5, border_mode='same')) #layer 3
        model.add(Activation('relu'))
        model.add(MaxPooling1D(pool_size=2, strides=2))
#         model.add(Dropout(DROPOUT))
        
        model.add(Conv1D(200, kernel_size=5, border_mode='same')) #layer 4
        model.add(Activation('relu'))
        model.add(MaxPooling1D(pool_size=2, strides=2))
        model.add(Dropout(DROPOUT))
        
        # model.add(Conv1D(300, kernel_size=5, border_mode='same')) #layer 5
        # model.add(Activation('relu'))
        # model.add(MaxPooling1D(pool_size=2, strides=2))
        # model.add(Dropout(DROPOUT))
        
        # model.add(Conv1D(400, kernel_size=5, border_mode='same')) #layer 6
        # model.add(Activation('relu'))
        # model.add(MaxPooling1D(pool_size=2, strides=2))
        
        # model.add(Conv1D(500, kernel_size=5, border_mode='same')) #layer 7
        # model.add(Activation('relu'))
        # model.add(MaxPooling1D(pool_size=2, strides=2))
        
        
        # model.add(GRU(512, return_sequences=True))
        # model.add(Dropout(DROPOUT))

        model.add(GRU(256, return_sequences=True))
        model.add(Dropout(DROPOUT))

        model.add(GRU(128, return_sequences=True))
        model.add(Dropout(DROPOUT))
        
        model.add(GRU(64, return_sequences=True))
        model.add(Dropout(DROPOUT))

        model.add(Flatten())
        model.add(Dense(700))
        model.add(Activation('relu'))
        model.add(Dropout(DROPOUT))
        
        model.add(Dense(classes))
        model.add(Activation('softmax'))
        return model


def get_label_to_index_map(path):
    labels = os.listdir(path)
    index = 0
    for l in labels:
        label_to_index_map[l] = index
        index += 1

# one hot encoding 
def get_one_hot_encoding(label):
    encoding = [0] * NB_CLASSES
    encoding[label_to_index_map[label]] = 1
    return encoding



def log_specgram(audio, sample_rate, window_size=20,
                 step_size=10, eps=1e-10):
    nperseg = int(round(window_size * sample_rate / 1000))
    noverlap = int(round(step_size * sample_rate / 1000))
    freqs, times, spec = signal.spectrogram(audio,
                                    fs=sample_rate,
                                    window='hann',
                                    nperseg=nperseg,
                                    noverlap=noverlap,
                                    detrend=False)
    return freqs, times, np.log(spec.T.astype(np.float32) + eps)


# Wave and spectrogram of a wav file
def get_spectrogram(path):
    sample_rate, samples = wavfile.read(path)
    freqs, times, spectrogram = log_specgram(samples,sample_rate)
#     print(spectrogram.shape)
    spectrogram.resize(99, 161)
    # if(spectrogram.shape[0]!=99):
        # spectrogram.resize(99, 161)
        # print(spectrogram.shape)
        # print("========================================")
    # else:
        # print(spectrogram.shape)
        # print("----------------------------------------")
#     fig = plt.figure(figsize=(14, 8))
#     ax1 = fig.add_subplot(211)
#     ax1.set_title('Raw wave of ' + filename)
#     ax1.set_ylabel('Amplitude')
#     ax1.plot(np.linspace(0, sample_rate/len(samples), sample_rate), samples)

#     ax2 = fig.add_subplot(212)
#     ax2.imshow(spectrogram.T, aspect='auto', origin='lower', 
#                extent=[times.min(), times.max(), freqs.min(), freqs.max()])
#     ax2.set_yticks(freqs[::16])
#     ax2.set_xticks(times[::16])
#     ax2.set_title('Spectrogram of ' + filename)
#     ax2.set_ylabel('Freqs in Hz')
#     ax2.set_xlabel('Seconds')
    return spectrogram


# Mel power spectrogram of a wav file
def get_melpower_spectrogram(path):
    sample_rate, samples = wavfile.read(path)
    samples = samples.astype(float)
    S = librosa.feature.melspectrogram(samples, sr=sample_rate, n_mels=128)

    # Convert to log scale (dB). We'll use the peak power (max) as reference.
    log_S = librosa.power_to_db(S, ref=np.max)
    if(log_S.shape[1]!=32):
        new_array = np.zeros((128, 32))
        new_array[:,:log_S.shape[1]] = log_S
        print(new_array.shape)
        print("==========================================")
        return new_array
    else:
        print(log_S.shape)
        print("----------------------------------------")
#         log_S = log_S.reshape(128,32)
#         print(log_S.shape)

    #     plt.figure(figsize=(12, 4))
    #     librosa.display.specshow(log_S, sr=sample_rate, x_axis='time', y_axis='mel')
    #     plt.title('Mel power spectrogram ')
    #     plt.colorbar(format='%+02.0f dB')
    #     plt.tight_layout()
        return log_S



#loads train and test data 
def load_data(curr_path):
    #load data file by file in trainX and corresponding label in OHE format in trainY
    train_path = curr_path+"/train"
    train_path = os.path.join(train_path, "*", '*.wav')
    train_waves = gfile.Glob(train_path)
    train_X = []
    train_Y = []
    for w in train_waves:
        _, label = os.path.split(os.path.dirname(w))
        print(w, "-----", label)
        train_X.append(get_spectrogram(w))
        train_Y.append(get_one_hot_encoding(label))
        print("TRAIN : ",w," -- done!")
    
    #do similar as above for test folder
    test_X = [] 
    test_Y = []
    test_path = curr_path+"/test"
    test_path = os.path.join(test_path, "*", '*.wav')
    test_waves = gfile.Glob(test_path)
    for w in test_waves:
        _, label = os.path.split(os.path.dirname(w))
        print(w, "-----", label)
        test_X.append(get_spectrogram(w))
        test_Y.append(get_one_hot_encoding(label))
        print("TEST : ",w," -- done!")
    
    #return trainX, trainY, testX, testY
    return train_X, train_Y, test_X, test_Y


def load_data_kaggle(curr_path, normal_waves):
    #load data file by file in trainX and corresponding label in OHE format in trainY
    train_path = curr_path+"/train"
    train_path = os.path.join(train_path, "*", '*.wav')
    train_waves = gfile.Glob(train_path)
    train_X = []
    train_Y = []
    for w in train_waves:
        _, label = os.path.split(os.path.dirname(w))
        print(w, "-----", label)
        train_X.append(get_spectrogram(w))
        train_Y.append(get_one_hot_encoding(label))
        print("TRAIN : ",w," -- done!")
    
    #do similar as above for test folder
    test_X = [] 
    # test_Y = []
    #test_path = curr_path+"/test"
    #test_path = os.path.join(test_path, "*", '*.wav')
    #test_waves = gfile.Glob(test_path)
    for w in normal_waves:
        # _, label = os.path.split(os.path.dirname(w))
        # print(w, "-----", label)
        test_X.append(get_spectrogram(w))
        # test_Y.append(get_one_hot_encoding(label))
        print("TEST : ",w," -- done!")
    
    #return trainX, trainY, testX, testY
    return train_X, train_Y, test_X


 

def get_silent_waves(test_path):
    onlyfiles = [f for f in listdir(test_path) if isfile(join(test_path, f))]
    silent_waves = []
    normal_waves = []
    for f in onlyfiles:
        file_path = test_path+"/"+f
        print(file_path)
        y,sr = librosa.load(file_path)
        s = np.abs(librosa.stft(y))
        power_to_db = librosa.power_to_db(s**2)
        dB_val = np.min(power_to_db)
        print(dB_val)
        if dB_val < -60 :
            silent_waves.append(f)
        else :
            normal_waves.append(f)
    return silent_waves, normal_waves


#MAIN PROGRAM

final_result = {}

#get all the test file path+name
curr_path = os.getcwd()
test_path = curr_path+"/test"
new_test_path = os.path.join(test_path, '*.wav')
test_waves = gfile.Glob(new_test_path)

#filter out the silent audios
print(test_path)
silent_waves, normal_waves = get_silent_waves(test_path) # normal_waves are your test files
print(len(silent_waves),"-", len(normal_waves))

#Add silent waves in the dictionary
for i in silent_waves:
    final_result[i] = "silent"

#Load the model.h5 file 
model = load_model('my_model.h5')
model.compile(loss='categorical_crossentropy', optimizer=OPTIMIZER, metrics=['accuracy'])

#Test it on normal_waves file
test_X = []
for i in range(len(normal_waves)):
    w = normal_waves[i]
    print(w)
    w1 = test_path + "/" + w
    test_X.append(get_spectrogram(w1))

test_X = np.asarray(test_X)
classes = model.predict_classes(test_X)
print(classes)
print(len(classes))

#Add labels of normal waves result to dictionary
for i in range(len(classes)):
    final_result[normal_waves[i]] = classes[i]

#dictionary->csv file
# print(final_result)
# with open('final_result.csv', 'w') as f:  # Just use 'w' mode in 3.x
#     w = csv.DictWriter(f, final_result.keys())
#     w.writeheader()
#     w.writerow(final_result)
f = open('final_result.csv', 'w')






# get_label_to_index_map(curr_path+"/train")

# # print(label_to_index_map)
# # print(get_one_hot_encoding('bird'))
# # train_path = curr_path+"/train"
# # test_path = curr_path+"/test"
# # filename = "/bed/0a7c2a8d_nohash_0.wav"
# # sample_rate, samples = wavfile.read(train_path+filename)
# # print(sample_rate)
# # print(samples.shape)
# # input_data = get_melpower_spectrogram(samples, sample_rate)

# train_X, train_Y, test_X = load_data_kaggle(curr_path, normal_waves)
# print(len(train_X))
# print(len(train_Y))
# print(len(test_X))
# # print(len(test_Y))

# # train_path = os.path.join(train_path, "*", '*.wav')
# # print(train_path)
# # waves = gfile.Glob(train_path)
# # print(len(waves))



# train_X = np.asarray(train_X)
# train_Y = np.asarray(train_Y)
# test_X = np.asarray(test_X)
# # test_Y = np.asarray(test_Y)

# # train_X = train_X[:, np.newaxis, :, :]
# # test_X = test_X[:, np.newaxis, :, :]
# # train_Y = train_Y.reshape((train_X.shape[0],1))
# # test_Y = test_Y.reshape((test_X.shape[0],1))
# print(train_X.shape)
# print(train_Y.shape)
# print(test_X.shape)
# # print(test_Y.shape)

# model = LeNet.build(input_shape=INPUT_SHAPE, classes=NB_CLASSES)
# model.compile(loss='categorical_crossentropy', optimizer=OPTIMIZER, metrics=['accuracy'])
# history = model.fit(train_X, train_Y, batch_size=BATCH_SIZE, epochs=NB_EPOCH, 
#                     verbose=VERBOSE, validation_split=VALIDATION_SPLIT)
# # score = model.evaluate(test_X, test_Y, verbose=VERBOSE)
# # print("Test score : ", score[0])
# # print("Test accuracy : ", score[1])

# results = model.predict(voice_test_X,BATCH_SIZE,VERBOSE)
# print(results)
# #create_csv(test_X, voice_test_X, results)
