import numpy as np
import h5py
from random import shuffle as S
import keras
from keras import optimizers
from keras.callbacks import ModelCheckpoint, CSVLogger
from keras import backend as K
from keras.utils import plot_model
from keras.models import Sequential, Model
from keras.layers import Input, Conv2D, BatchNormalization, Activation, Lambda, MaxPooling2D, Flatten, Dense, Dropout, Concatenate, Add, AveragePooling2D


def generate_arrays_from_file(images, labels, ids_list, shuffle=True):
    x = np.zeros((32, 49, 49, 3))
    y = np.zeros((32, 11))
    batch_id = 0
    while 1:
        if shuffle:
            S(ids_list)
        x = np.zeros((32, 49, 49, 3))
        y = np.zeros((32, 11))
        for id_list in ids_list:
            for i in range(len(images[id_list])):
                x[i%32, ...] = images[id_list][i]
                y[i%32, ...] = keras.utils.to_categorical(labels[id_list][i], num_classes=11)
                if i%32 == 0:
                    yield (x, y)
                    x = np.zeros((32, 49, 49, 3))
                    y = np.zeros((32, 11))

def custom_conv2d(x, filters, kernel, strides, padding, normalize, activation):
    x = Conv2D(filters, kernel, strides=strides, padding=padding)(x)
    if (normalize==True):
	    x = BatchNormalization()(x)
    if (activation!=None):
        x = Activation(activation)(x)
    return x

# 299x299x3 => 49x49x3
def inception_resnet_v2_stem(x):
    x = custom_conv2d(x, 32, (3, 3), (2, 2), 'valid', True, 'relu')
    # V
    x = custom_conv2d(x, 32, (3, 3), (1, 1), 'same', True, 'relu')
    x = custom_conv2d(x, 64, (3, 3), (1, 1), 'same', True, 'relu')

    x_a = MaxPooling2D(pool_size=(3, 3), strides=(2, 2), padding='valid')(x)
    x_b = custom_conv2d(x, 96, (3, 3), (2, 2), 'valid', True, 'relu')

    x = Concatenate(axis=-1)([x_a, x_b])

    x_a = custom_conv2d(x, 64, (1, 1), (1, 1), 'same', True, 'relu')
    x_a = custom_conv2d(x_a, 96, (3, 3), (1, 1), 'valid', True, 'relu')
    x_b = custom_conv2d(x, 64, (1, 1), (1, 1), 'same', True, 'relu')
    x_b = custom_conv2d(x_b, 64, (7, 1), (1, 1), 'same', True, 'relu')
    x_b = custom_conv2d(x_b, 64, (1, 7), (1, 1), 'same', True, 'relu')
    x_b = custom_conv2d(x_b, 96, (3, 3), (1, 1), 'valid', True, 'relu')

    x = Concatenate(axis=-1)([x_a, x_b])

    x_a = custom_conv2d(x, 192, (3, 3), (1, 1), 'same', True, 'relu')

    x_b = MaxPooling2D(pool_size=(3, 3), strides=(1, 1), padding='same')(x)
    x = Concatenate(axis=-1)([x_a, x_b])
    return x

def inception_resnet_v2_a(x, scale=0.17):

	x_a = Activation('relu')(x)

	x_b_1 = custom_conv2d(x, 32, (1, 1), (1, 1), 'same', True, 'relu')

	x_b_2 = custom_conv2d(x, 32, (1, 1), (1, 1), 'same', True, 'relu')
	x_b_2 = custom_conv2d(x_b_2, 32, (3, 3), (1, 1), 'same', True, 'relu')

	x_b_3 = custom_conv2d(x, 32, (1, 1), (1, 1), 'same', True, 'relu')
	x_b_3 = custom_conv2d(x_b_3, 48, (3, 3), (1, 1), 'same', True, 'relu')
	x_b_3 = custom_conv2d(x_b_3, 64, (3, 3), (1, 1), 'same', True, 'relu')

	x_b = Concatenate(axis=-1)([x_b_1, x_b_2, x_b_3])

	x_b = custom_conv2d(x, 384, (1, 1), (1, 1), 'same', True, None)

	# x_a = Lambda(lambda x: x * scale)(x_a)

	x = Add()([x_a, x_b])

	x = Activation('relu')(x)

	return x

def inception_resnet_v2_reduction_a(x):

	# V
    x_a = MaxPooling2D(pool_size=(3, 3), strides=(2, 2), padding='same')(x)

    x_b = custom_conv2d(x, 384, (3, 3), (2, 2), 'same', True, 'relu')

    x_c = custom_conv2d(x, 256, (1, 1), (1, 1), 'same', True, 'relu')
    x_c = custom_conv2d(x_c, 256, (3, 3), (1, 1), 'same', True, 'relu')
    # V
    x_c = custom_conv2d(x_c, 384, (3, 3), (2, 2), 'same', True, 'relu')

    x = Concatenate(axis=-1)([x_a, x_b, x_c])
    return x

def inception_resnet_v2_b(x, scale=0.1):

	x_a = Activation('relu')(x)

	x_b_1 = custom_conv2d(x, 192, (1, 1), (1, 1), 'same', True, 'relu')

	x_b_2 = custom_conv2d(x, 128, (1, 1), (1, 1), 'same', True, 'relu')
	x_b_2 = custom_conv2d(x_b_2, 160, (1, 7), (1, 1), 'same', True, 'relu')
	x_b_2 = custom_conv2d(x_b_2, 192, (7, 1), (1, 1), 'same', True, 'relu')

	x_b = Concatenate(axis=-1)([x_b_1, x_b_2])

	x_b = custom_conv2d(x, 1152, (1, 1), (1, 1), 'same', True, None)   #1154

	# x_a = Lambda(lambda x: x * scale)(x_a)

	x = Add()([x_a, x_b])

	x = Activation('relu')(x)

	return x

def inception_resnet_v2_reduction_b(x):

	x_a = MaxPooling2D(pool_size=(3, 3), strides=(2, 2), padding='valid')(x)

	x_b = custom_conv2d(x, 256, (1, 1), (1, 1), 'same', True, 'relu')
	x_b = custom_conv2d(x_b, 384, (3, 3), (2, 2), 'valid', True, 'relu')

	x_c = custom_conv2d(x, 256, (1, 1), (1, 1), 'same', True, 'relu')
	x_c = custom_conv2d(x_c, 288, (3, 3), (2, 2), 'valid', True, 'relu')

	x_d = custom_conv2d(x, 256, (1, 1), (1, 1), 'same', True, 'relu')
	x_d = custom_conv2d(x_d, 288, (3, 3), (1, 1), 'same', True, 'relu')
	x_d = custom_conv2d(x_d, 320, (3, 3), (2, 2), 'valid', True, 'relu')

	x = Concatenate(axis=-1)([x_a, x_b, x_c, x_d])

	return x

def inception_resnet_v2_c(x, scale=0.2):

	x_a = Activation('relu')(x)

	x_b_1 = custom_conv2d(x, 192, (1, 1), (1, 1), 'same', True, 'relu')

	x_b_2 = custom_conv2d(x, 192, (1, 1), (1, 1), 'same', True, 'relu')
	x_b_2 = custom_conv2d(x_b_2, 224, (1, 3), (1, 1), 'same', True, 'relu')
	x_b_2 = custom_conv2d(x_b_2, 256, (3, 1), (1, 1), 'same', True, 'relu')

	x_b = Concatenate(axis=-1)([x_b_1, x_b_2])

	x_b = custom_conv2d(x, 2144, (1, 1), (1, 1), 'same', True, None)#2048

	# x_a = Lambda(lambda x: x * scale)(x_a)

	x = Add()([x_a, x_b])

	x = Activation('relu')(x)

	return x

def inception_resnet_v2():
    # pour chaque bloc du réseau appliquer les parametres du document
	i = Input(shape=(49, 49, 3))

	x = inception_resnet_v2_stem(i)
	for j in range(1): #i remplacer par j
	    x = inception_resnet_v2_a(x)
	x = inception_resnet_v2_reduction_a(x)
	# x10
	for j in range(1):
		x = inception_resnet_v2_b(x)
	#x = inception_resnet_v2_reduction_b(x)
	# x5
	#for j in range(1):
	#	x = inception_resnet_v2_c(x)
	x = AveragePooling2D(pool_size=(5, 5), strides=(1, 1), padding='valid')(x) # (8,8) remplacer (5,5)
	x = Flatten()(x)
	x = Dropout(0.2)(x)
	x = Dense(11)(x)
	o = Activation('softmax')(x)

	model = Model(inputs=i, outputs=o)

	model.summary()

	return model


def load_mean_std(h5_path):
    # charger mean/std image
    f = h5py.File(h5_path, 'r') # idem
    mean_image = np.copy(f['mean']).transpose(1, 2, 0)
    std_image = np.copy(f['std']).transpose(1, 2, 0)
    f.close()
    return mean_image, std_image

def load_data(txt_path):
    images = []
    annotations = []
    h5_files = [line.rstrip('\r\n') for line in open(txt_path)]
    for h5_file in h5_files:
        # normaliser le training set
        f = h5py.File('/media/isen/Data_windows/PROJET_M1_DL/Affect-Net/MAN/h5/' + h5_file, 'r')
        images.append(np.copy(f['data']))
        annotations.append(np.copy(f['label_classification']))
        f.close()
    id_ = list(range(0, len(images)))
    return images, annotations, id_

def normalize_image(image):
    return np.divide((image - mean_image), std_image)


if __name__ == "__main__":
    print('Loading dataset...')


    mean_image, std_image = load_mean_std('/media/isen/Data_windows/PROJET_M1_DL/Affect-Net/MAN/mean_std/mean_std.hdf5')


    images_training, annotations_training, id_training = load_data('/media/isen/Data_windows/PROJET_M1_DL/Affect-Net/MAN/h5_training.txt')

    images_validation, annotations_validation, id_validation = load_data('/media/isen/Data_windows/PROJET_M1_DL/Affect-Net/MAN/h5_validation.txt')

    # normalisation
    # for images in images_training:
    #     for image in images:
    #         image = normalize_image(image)
    #
    # for images in images_validation:
    #     for image in images:
    #         image = normalize_image(image)


    print('Network...')
    model = inception_resnet_v2()

    print('Optimization...')
    adam = optimizers.Adam(lr=0.0001, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=0.0)
    model.compile(optimizer=adam, loss='categorical_crossentropy', metrics=['acc'])

    model.summary()
    #plot_model(model, to_file='model.png')


    indexlist = [line.rstrip('\r\n') for line in open('training.csv')]
    db_size = len(indexlist)

    print('Training...')
    #tbCallback=keras.callbacks.TensorBoard(log_dir='/media/isen/Data_windows/PROJET_M1_DL/Affect-Net/MAN/TBlogs', histogram_freq=0, batch_size=32, write_graph=True, write_grads=False, write_images=False, embeddings_freq=0, embeddings_layer_names=None, embeddings_metadata=None)

    # poids, loss, accuracy, val_loss, val_accuracy
    csv_logger = CSVLogger('inception_resnet.log', append=True)
    checkpointer = ModelCheckpoint(filepath='snapshots/{epoch:03d}-{val_loss:.6f}.h5', verbose=1, save_best_only=True)
    hist = model.fit_generator(generate_arrays_from_file(images_training, annotations_training, id_training), int(db_size/32)-1, epochs=400, callbacks=[csv_logger, checkpointer], validation_data=generate_arrays_from_file(images_validation, annotations_validation, id_validation), validation_steps=int(5500/32)-1, max_queue_size=1, workers=1, use_multiprocessing=False, initial_epoch=0) # a modifie 171 par 569

    print('Recording...')
    model.save('inception_resnet.h5')
