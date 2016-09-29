import numpy as np
from keras.applications.resnet50 import ResNet50
from keras.layers import Input, Dense
from keras.layers.wrappers import TimeDistributed
from keras.layers.core import Reshape, Permute, Masking
from VladLayer import VladLayer
from keras.models import Model
from keras.layers.pooling import MaxPooling2D
from keras.engine.topology import merge

class Memory:
	def __init__(self, memory_size = 100):
		self.memory = []
		self.memory_size = memory_size	

	def remember(self, state, a, next_state, r):
		self.memory.append({'state': state, 'action':a, 'next_state': next_state, 'r': r})
		if len(self.memory) > self.memory_size:
			self.memory.pop(0)
	
	def batch(self, model, batch_size, gama = 0.9):
		print 'memory batch'

class VideoModel:
	def __init__(self, height = 224, width = 224, n_channels = 3, max_window_size = 10, step = 10, n_centers = 256, 
			pretrain = True, spp_struct = ((7, 7), (3, 3),  (2, 2), (1, 1))):
		print 'model'
		self.height = height
		self.width = width
		self.n_channels = n_channels
		self.max_window_size = max_window_size
		self.step = step
		self.n_centers = n_centers

		if pretrain:
			self.height = 224
			self.width = 224
			self.n_channels = 3

		if spp_struct is not None:
			self.spp_struct = spp_struct
	
	def __obtainSppParams(self, length, n_bins):
		stride = length // n_bins
		size = stride + length % n_bins
		return stride, size

	def __constructSppPooling(self, h, w,  n_bins):
		print n_bins
		stride_h, size_h = self.__obtainSppParams(h, n_bins[0])
		stride_w, size_w = self.__obtainSppParams(w, n_bins[1])		
		print size_h, size_w
		print stride_h, stride_w
		layer_pool = TimeDistributed(MaxPooling2D(pool_size = (size_h, size_w), strides = (stride_h, stride_w)))

		return layer_pool

	def spp(self, input, input_shape):
		l = input_shape[1]
		h = input_shape[3]
		w = input_shape[4]
		pools = []
		outputs = []	
		for i, n_bins in enumerate(self.spp_struct):
			pools.append(self.__constructSppPooling(h, w, n_bins))
			output = pools[i](input)

			layer_permute = TimeDistributed(Permute((2, 3, 1)))
			output = layer_permute(output)

			output_shape = layer_permute.output_shape
			layer_reshape =  TimeDistributed(Reshape((output_shape[2] * output_shape[3], output_shape[4])))
			outputs.append(layer_reshape(output))
			
			print layer_reshape.output_shape

		output = merge(outputs, mode = 'concat', concat_axis = 2)
		return output
		
		
	def constructNetwork(self):
		input = Input(shape = (self.max_window_size, self.n_channels, self.height, self.width))
		h = Masking()(input)
		res_net = ResNet50(weights='imagenet', include_top = False)
		res_net_output = res_net.get_layer('bn5c_branch2c').output
		res_net = Model(input = res_net.input, output = res_net_output)

		res_net_time = TimeDistributed(res_net)
		h = res_net_time(h)
		
		#model = Model(input = input, output = h)
		#data = np.random.random((2, 10, 3, 224, 224))
		#data = model.predict(data)
		h = self.spp(h, res_net_time.output_shape)
		

		#layer_permute = Permute((1, 3, 4, 2))
		#h = layer_permute(h)
		#output_shape = layer_permute.output_shape
		#print output_shape
		

		#h = Reshape((output_shape[1] * output_shape[2] * output_shape[3], output_shape[4]))(h)
		h = VladLayer(n_centers = self.n_centers)(h)
		#h = Reshape((self.n_centers * output_shape[4],))(h)
		
		data = np.random.random((5, 10, 3, 224, 224))		
		data[0, 9, :, :, :] = 0
		self.model = Model(input = input, output = h)
		data = self.model.predict(data)
		print data

if __name__ == '__main__':
	model = VideoModel()
	model.constructNetwork()
		
	
#	res_net = ResNet50(weights = 'imagenet', include_top = False)
#	model = Model(input = res_net.input, output = res_net.get_layer('bn5c_branch2c').output)

#	data = np.random.random((3, 3, 224, 224))
#	data = model.predict(data)
	

#	print data.shape
	
		
