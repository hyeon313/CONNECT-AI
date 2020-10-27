import numpy as np
import matplotlib.pyplot as plt
import os
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Input, Conv2DTranspose, Concatenate, BatchNormalization, UpSampling2D, LeakyReLU
from tensorflow.keras.layers import  Dropout, Activation
from tensorflow.keras.optimizers import Adam, SGD
from tensorflow.keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, EarlyStopping
from tensorflow.keras import backend as K
from tensorflow.keras.utils import plot_model, to_categorical
import glob
import random
import cv2
from random import shuffle
import voxel

config = tf.ConfigProto()
config.gpu_options.allow_growth = True
sess = tf.Session(config=config)

def data_convert():
    py_raw = voxel.PyVoxel()

    py_raw.ReadFromRaw("C:/Users/yjm45/Desktop/LV/LV ct label/LV ground truth/01/RAW/KHJ_3959345.raw")
    img = py_raw.m_Voxel
    img = np.expand_dims(img, axis=-1)

    py_raw.ReadFromBin("C:/Users/yjm45/Desktop/LV/LV ct label/LV ground truth/01/BIN/LV3.bin")
    LV = py_raw.m_Voxel
    LV = np.where(LV==2, 1, LV) 

    py_raw.ReadFromBin("C:/Users/yjm45/Desktop/LV/LV ct label/LV ground truth/01/BIN/LV Only3.bin")
    LV_only = py_raw.m_Voxel
    LV_only = np.where(LV_only==2, 1, LV_only) 

    mask = LV + LV_only
    mask = to_categorical(mask)

    return img, mask



def data_load():
    img = np.load("C:/Users/jhLee/Desktop/final/merge/imgs.npy")
    mask = np.load("C:/Users/jhLee/Desktop/final/merge/masks.npy")

    img = np.expand_dims(img, axis=-1)
    mask = np.expand_dims(mask, axis=-1)
    mask = to_categorical(mask)

    return img, mask
    
def dice_coef(y_true, y_pred, smooth=1):
    y_pred = K.argmax(y_pred, axis=-1)
    y_true = y_true[:,:,:,1]

    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    y_true_f = K.cast(y_true_f, 'float32')
    y_pred_f = K.cast(y_pred_f, 'float32')

    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

def dice_loss(y_true, y_pred):
    smooth = 1.
    y_pred = K.argmax(y_pred, axis=-1)
    y_true = y_true[:,:,:,1]
    
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    y_true_f = K.cast(y_true_f, 'float32')
    y_pred_f = K.cast(y_pred_f, 'float32')
    
    intersection = y_true_f * y_pred_f
    score = (2. * K.sum(intersection) + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)
    return tf.math.exp(1  - score) - 1.0
    # return 1. - score

def bce_dice_loss(y_true, y_pred):
    return categorical_crossentropy(y_true, y_pred) + dice_loss(y_true, y_pred)

def build_unet(sz=(512,512,1)):
    x = Input(sz)
    inputs = x
  
    #down sampling

    f = 8
    layers = []
  
    for i in range(0, 6):
        x = Conv2D(f, 3, activation='relu', padding='same') (x)
        x = Conv2D(f, 3, activation='relu', padding='same') (x)
        layers.append(x)
        x = MaxPooling2D() (x)
        f = f*2
        ff2 = 64 
    
    #bottleneck 
    j = len(layers) - 1
    x = Conv2D(f, 3, activation='relu', padding='same') (x)
    x = Conv2D(f, 3, activation='relu', padding='same') (x)
    x = Conv2DTranspose(ff2, 2, strides=(2, 2), padding='same') (x)
    
    x = Concatenate(axis=3)([x, layers[j]])
    j = j -1 
  
    #upsampling 
    for i in range(0, 5):
        ff2 = ff2//2
        f = f // 2 
        x = Conv2D(f, 3, activation='relu', padding='same') (x)
        x = Conv2D(f, 3, activation='relu', padding='same') (x)
        x = Conv2DTranspose(ff2, 2, strides=(2, 2), padding='same') (x)
        x = Concatenate(axis=3)([x, layers[j]])
        j = j -1 
    
  
    #classification 
    x = Conv2D(f, 3, activation='relu', padding='same') (x)
    x = Conv2D(f, 3, activation='relu', padding='same') (x)
    outputs = Conv2D(3, 1, activation='softmax') (x)
    
    #model creation 
    model = Model(inputs=[inputs], outputs=[outputs])
    model.compile(optimizer = 'rmsprop', loss = 'categorical_crossentropy', metrics = [dice_coef])
  
    return model


if __name__ == '__main__':
    import os
    os.environ["CUDA_VISIBLE_DEVICES"]="0"
    # source, target = data_convert()

    source, target = data_load()
    
    model = build_unet()
    model.summary()

    model.fit(source, target, epochs=10, validation_split=0.7, batch_size=8)
