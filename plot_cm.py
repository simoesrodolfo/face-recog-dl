import matplotlib.pyplot as plt
import numpy as np # linear algebra
import itertools
#from ensembleGenerator import get_current_time_str

import datetime

def get_current_time_str():
    return datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S")

def plot_confusion_matrix(cm, classes,
                          CLASSES,
                          MODEL_NAME,
                          EPOCHS,
                          BATCH_SIZE,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
    
    #This function prints and plots the confusion matrix.
    #Normalization can be applied by setting `normalize=True`.
    
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    plt.figure(figsize=(CLASSES+20, CLASSES+20))
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    #plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('Classe Real')
    plt.xlabel('Classe Predita')
    plt.savefig(get_current_time_str() + 'main1_k_fold_' + str(CLASSES) + '_' + MODEL_NAME + '_' + str(EPOCHS) + '_' + str(
        BATCH_SIZE) + 'CM.png')
    plt.close()
