import numpy as np
import h5py
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers.core import Dense, Activation, Dropout, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import SGD
from keras.utils import np_utils
from keras import callbacks
from keras.utils.visualize_util import plot
from keras.layers import advanced_activations

obs_size = 64

print('Reading data')

## Initialising with value 0
f = h5py.File('keras_data/db_Oregon_X_0.hdf5', 'r')
X_train = np.array(f['data'])
f.close()
f = h5py.File('keras_data/db_Oregon_y_0.hdf5', 'r')
y_train = np.array(f['data'])
f.close()

for i in range(1,35):
	f = h5py.File('keras_data/db_Oregon_X_%d.hdf5' % i, 'r')
	X_train = np.vstack((X_train, np.array(f['data'])))
	f.close()
	f = h5py.File('keras_data/db_Oregon_y_%d.hdf5' % i, 'r')
	y_train = np.hstack((y_train, f['data']))
	f.close()

## Initialising with value 0
f = h5py.File('keras_data/db_Washington_X_0.hdf5', 'r')
X_test = np.array(f['data'])
f.close()
f = h5py.File('keras_data/db_Washington_y_0.hdf5', 'r')
y_test = np.array(f['data'])
f.close()

for i in range(1,26):
	f = h5py.File('keras_data/db_Washington_X_%d.hdf5' % i, 'r')
	X_test = np.vstack((X_test, np.array(f['data'])))
	f.close()
	f = h5py.File('keras_data/db_Washington_y_%d.hdf5' % i, 'r')
	y_test = np.hstack((y_test, f['data']))
	f.close()

# mean normalisation
mean_value = np.mean(X_train)
X_train = X_train - mean_value
X_test = X_test - mean_value

std_value = np.std(X_train)
X_train = X_train / std_value
X_test = X_test / std_value

print 'Creating the model'
# sequential wrapper model
model = Sequential()

# first convolutional layer
model.add(Convolution2D(256, 5, 5, 
			border_mode='valid',
			input_shape = (7, obs_size, obs_size)))
model.add(Activation('relu'))
model.add(Dropout(0.3))

# second convolutional layer
model.add(Convolution2D(64, 3, 3))
model.add(MaxPooling2D(pool_size=(3, 3)))
model.add(Activation('relu'))
model.add(Dropout(0.3))

# third convolutional layer
model.add(Convolution2D(128, 5, 5))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Activation('relu'))
model.add(Dropout(0.3))

# forth convolutional layer
model.add(Convolution2D(64, 3, 3))
model.add(MaxPooling2D(pool_size=(3, 3)))
model.add(Activation('relu'))
model.add(Dropout(0.3))

# convert convolutional filters to flat so they
# can be fed to fully connected layers

model.add(Flatten())

# first fully connected layer
model.add(Dense(128))
model.add(Activation('relu'))
model.add(Dropout(0.3))

# second fully connected layer
model.add(Dense(64))
model.add(Activation('relu'))
model.add(Dropout(0.3))

# third fully connected layer
model.add(Dense(1))
model.add(Activation('linear'))

# setting sgd optimizer parameters
sgd = SGD(lr=0.1, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='mean_squared_error', optimizer='rmsprop')

earlystop = callbacks.EarlyStopping(monitor='val_loss', patience = 5, 
	verbose=1, mode='min')
checkpoint = callbacks.ModelCheckpoint('/tmp/weights.hdf5', 
	monitor='val_loss', verbose=1, save_best_only=True, mode='auto')
history = callbacks.History()

print("Starting training")
model.fit(X_train, y_train, batch_size=128, validation_split=0.15, show_accuracy=False,
	callbacks = [earlystop, checkpoint, history])
print("Evaluating")
score = model.evaluate(X_test, y_test, batch_size=128)
predicted = model.predict(X_test)  
rmse = np.sqrt(((predicted - y_test) ** 2).mean())
print 'RMSE', rmse

fig, ax = plt.subplots()
ax.scatter(y_test, predicted) 
ax.set_xlabel('Actual', fontsize=20)
ax.set_ylim(0, max(predicted) )
ax.set_xlim(0, max(y_test))
ax.set_ylabel('Predicted', fontsize=20)
x = np.linspace(0, max(y_test))
ax.plot(x, x)
plt.savefig('scatter.pdf')

plt.cla()
plt.clf()

fix, ax = plt.subplots()
ax.plot(history.history['loss'], label = 'Training loss')
ax.plot(history.history['val_loss'], label = 'Validation loss')
ax.set_xlabel('Epoch', fontsize=20)
ax.set_ylabel('RMSE (people per km$^2$)', fontsize=20)
plt.legend()
plt.savefig('loss.pdf')

plot(model, to_file='model_architecture.png')

print 'Printing History'
print history.history

# save as JSON
json_string = model.to_json()
# save model weights
model.save_weights('model_weights.h5', overwrite=True)