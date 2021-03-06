#!/usr/bin/env python
# coding: utf-8

# imports
import os
import gc
import math
# Mover arquivos
from datetime import datetime
# CNN
import tensorflow as tf

from tensorflow.keras import optimizers

from tensorflow.keras.applications import VGG16, ResNet50, InceptionV3

from sklearn.model_selection import StratifiedKFold
import datetime

from dataprocess import get_mounted_data, directory_mover
from TFpath import transform_image_to_tfrecord_image_path
from models import create_new_model, DeepFace, LeNet5, AlexNet, VGGFace, VGGFaceHalf

from write_plot_history import write_results
import matplotlib.pyplot as plt
import numpy as np
import itertools

def plot_confusion_matrix(cm, class_names):
  """
  Returns a matplotlib figure containing the plotted confusion matrix.

  Args:
    cm (array, shape = [n, n]): a confusion matrix of integer classes
    class_names (array, shape = [n]): String names of the integer classes
  """
  figure = plt.figure(figsize=(8, 8))
  plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
  plt.title("Confusion matrix")
  plt.colorbar()
  tick_marks = np.arange(len(class_names))
  plt.xticks(tick_marks, class_names, rotation=45)
  plt.yticks(tick_marks, class_names)

  # Normalize the confusion matrix.
  cm = np.around(cm.astype('float') / cm.sum(axis=1)[:, np.newaxis], decimals=2)

  # Use white text if squares are dark; otherwise black.
  threshold = cm.max() / 2.
  for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
    color = "white" if cm[i, j] > threshold else "black"
    plt.text(j, i, cm[i, j], horizontalalignment="center", color=color)

  plt.tight_layout()
  plt.ylabel('True label')
  plt.xlabel('Predicted label')
  return figure

def log_confusion_matrix(epoch, logs):
  # Use the model to predict the values from the validation dataset.
  test_pred_raw = model.predict(test_images)
  test_pred = np.argmax(test_pred_raw, axis=1)

  # Calculate the confusion matrix.
  cm = sklearn.metrics.confusion_matrix(test_labels, test_pred)
  # Log the confusion matrix as an image summary.
  figure = plot_confusion_matrix(cm, class_names=class_names)
  cm_image = plot_to_image(figure)

  # Log the confusion matrix as an image summary.
  with file_writer_cm.as_default():
    tf.summary.image("Confusion Matrix", cm_image, step=epoch)

def get_model_name(name, k, batch):
    return 'model_TFrecord' + name + '_' + str(k) + '_' + str(batch) + '.h5'

def get_current_time_str():
    return datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S")

def run_k_fold(multi_data, X, Y, CLASSES, epoch, MODEL, BATCH_SIZE, num_folds):
    VALIDATION_ACCURACY = []
    VALIDATION_LOSS = []
    HISTORY = []
    MODEL_NAME = MODEL
    FOLDS = num_folds
    EPOCHS = epoch
    save_dir = os.path.join(os.getcwd(), 'models/')
    VERBOSE = 1

    skf = StratifiedKFold(n_splits=FOLDS, random_state=7, shuffle=True)

    fold_var = 1
    for train_index, val_index in skf.split(X, Y):
        print("=======EPOCHS ", EPOCHS, " Start--k: ", fold_var)

        training_data = multi_data.iloc[train_index]
        validation_data = multi_data.iloc[val_index]

        print(training_data.shape)
        print(validation_data.shape)

        directory_mover(training_data,"training_data_"+MODEL_NAME+str(BATCH_SIZE)+'_'+str(EPOCHS)+'_'+str(fold_var))
        directory_mover(validation_data,"validation_data_"+MODEL_NAME+str(BATCH_SIZE)+'_'+str(EPOCHS)+'_'+str(fold_var))

        # tfrecord
        ds_train = transform_image_to_tfrecord_image_path(os.path.join(os.getcwd(),"new/working/","training_data_"+MODEL_NAME+str(BATCH_SIZE)+'_'+str(EPOCHS)+'_'+str(fold_var)), BATCH_SIZE)
        ds_validation = transform_image_to_tfrecord_image_path(os.path.join(os.getcwd(),"new/working/","validation_data_"+MODEL_NAME+str(BATCH_SIZE)+'_'+str(EPOCHS)+'_'+str(fold_var)), BATCH_SIZE)

        logdir = "logs/image/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        # Define the basic TensorBoard callback.
        tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=logdir)
        file_writer_cm = tf.summary.create_file_writer(logdir + '/cm')
        cm_callback = tf.keras.callbacks.LambdaCallback(on_epoch_end=log_confusion_matrix)

        model = get_model(MODEL, CLASSES)
        # rmsprop = RMSprop(lr=1e-3, decay=1e-6)
        sgd = optimizers.SGD(lr=1e-3, decay=1e-6, momentum=0.9, nesterov=True)
        model.compile(optimizer=sgd, loss='categorical_crossentropy', metrics=['acc'])
        # CREATE CALLBACKS
        checkpoint = tf.keras.callbacks.ModelCheckpoint(save_dir + get_model_name(MODEL_NAME, fold_var, BATCH_SIZE),monitor='val_acc', verbose=VERBOSE, save_best_only=True, mode='max')
        earlystopping = tf.keras.callbacks.EarlyStopping(monitor='val_loss', mode='min', verbose=VERBOSE, patience=300)
        callbacks_list = [checkpoint, earlystopping, tensorboard_callback, cm_callback]

        history = model.fit(ds_train,
                            epochs=EPOCHS,
                            steps_per_epoch=(training_data.shape[0] // BATCH_SIZE) + 1,
                            callbacks=callbacks_list,
                            validation_data=ds_validation,
                            validation_steps=(validation_data.shape[0] // BATCH_SIZE) + 1,
                            verbose=VERBOSE
                            #GPU Test luisss
                            #max_queue_size=BATCH_SIZE,                # maximum size for the generator queue
                            #workers=12,                        # maximum number of processes to spin up when using process-based threading
                            #use_multiprocessing=False
                            )

        HISTORY.append(history)

        # LOAD BEST MODEL to evaluate the performance of the model model_"+MODEL_NAME+"_"+str(fold_var)+".h5"
        model.load_weights(
            os.getcwd() + "/models/model_TFrecord" + MODEL_NAME + "_" + str(fold_var) + '_' + str(BATCH_SIZE) + ".h5")

        #results = model.evaluate(ds_validation)
        # results = model.evaluate_generator(valid_data_generator)
        #results = dict(zip(model.metrics_names, results))

        VALIDATION_ACCURACY.append(1)
        VALIDATION_LOSS.append(2)

        write_results(
            get_current_time_str() + 'main_TFrecord_k_fold_' + str(CLASSES) + '_' + MODEL_NAME + '_' + str(EPOCHS) + '_' + str(
                BATCH_SIZE) + '.txt', VALIDATION_ACCURACY, VALIDATION_LOSS, HISTORY)

        del history
        del model
        #tf.keras.backend.clear_session()
        gc.collect()
        #tf.compat.v1.reset_default_graph()
        fold_var += 1

def get_model(model_name, num_classes):
    if model_name == "create_new_model":
        return create_new_model(num_classes)
    elif model_name == "AlexNet":
        return AlexNet(num_classes)
    elif model_name == "LeNet5":
        return LeNet5(num_classes)
    elif model_name == "VGG16":
        return VGG16(num_classes)
    elif model_name == "ResNet50":
        return ResNet50(num_classes)
    elif model_name == "InceptionV3":
        return InceptionV3(num_classes)
    elif model_name == "DeepFace":
        return DeepFace(num_classes)
    elif model_name == "VGGFace":
        return VGGFace(num_classes)
    elif model_name == "VGGFaceHalf":
        return VGGFace(num_classes)

"""
params = {
    epoch
    min_images_per_person
        number of classes
    model
    batch_size
    hold_out
    k-fold
}
"""

def main():
    epoch = 1
    min_images_per_person = [30]#[30,25]  # [25,20]
    models = ["LeNet5"]#["LeNet5","AlexNet","DeepFace"]#["LeNet5","AlexNet","DeepFace","VGGFace"]
    num_folds = 2

    batch_sizes = [30]#[2,4,8,30]
    for min_per_person in min_images_per_person:
        for batch in batch_sizes:
            for model in models:
                multi_data = get_mounted_data(min_per_person, min_per_person)
                Y = multi_data[['name']]
                X = multi_data[['image_path']]
                CLASSES = Y.groupby('name').nunique().shape[0]
                print("### run_k_fold ", " epoch ", epoch, " min_per_person ", min_per_person, " CLASSES ", CLASSES,
                      "model ", model, " batch_size ", batch)
                run_k_fold(multi_data, X, Y, CLASSES, epoch, model, batch, num_folds)
                #tf.keras.backend.clear_session()
                gc.collect()

if __name__ == "__main__":
    main()