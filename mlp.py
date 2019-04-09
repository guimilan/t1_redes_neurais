import numpy as np
import imageio
import math
import matplotlib.pyplot as plt
import pickle
import os

#Classe que representa o multilayer perceptron
class MLP():
	#Construtor. Recebe o tamanho das cadamas de entrada, oculta e de saidas
	def __init__(self, input_length, hidden_length, output_length):
		self.input_length = input_length
		self.hidden_length = hidden_length
		self.output_length = output_length

		#Inicializa os pesos da camada oculta aleatoriamente, representando-os na forma de matriz
		#Os pesos e vies de cada neuronio sao dispostos em linhas
		#Em input_length+1, o +1 serve para representar o vies
		self.hidden_layer = np.random.uniform(-0.5, 0.5, (hidden_length, input_length+1))

		#Inicializa os pesos da camada de saida aleatoriamente, representado-os na forma de matriz
		#Os pesos e vies de cada neuronio sao dispostos em linhas
		#Em hidden_length+1, o +1 serve para representar o vies
		self.output_layer = np.random.uniform(-0.5, 0.5, (output_length, hidden_length+1))

	def save_to_disk(self, file_name):
		print('Saving model to', file_name)
		with open(file_name, 'wb') as file:
			pickle.dump(self, file)

	#Funcao de ativacao (sigmoide)
	def activ(self, net):
		return (1./(1.+math.exp(-net)))

	#Derivada da funcao de ativacao (sigmoide)
	def deriv_activ(self, fnet):
		one_vector = np.ones(fnet.shape)
		return fnet*(one_vector-fnet)

	def forward(self, input_vect):
		return self.forward_training(input_vect)[3]

	#Faz forward propagation (calcula a predicao da rede)
	def forward_training(self, input_vect):
		input_vect = np.array(input_vect)
		#Checa se o tamanho da entrada corresponde ao que eh esperado pela rede
		if(input_vect.shape[0] != self.input_length):
			message = 'Tamanho incorreto de entrada. Recebido: {} || Esperado: {}'.format(input_vect.shape[0], self.input_length)
			raise Exception(message)

		#Adiciona um componente "1" ao vetor de entrada para permitir calculo do bias
		#na camada oculta
		biased_input = np.zeros((input_vect.shape[0]+1))
		biased_input[0:input_vect.shape[0]] = input_vect[:]
		biased_input[input_vect.shape[0]] = 1

		#Calcula a transformacao da entrada pela camada oculta usando produto de matriz por vetor 
		#Wh x A = net, sendo Wh a matriz de pesos da camada oculta e A o vetor de entrada 
		hidden_net = np.dot(self.hidden_layer, biased_input)
		#Aplica a funcao de ativacao sobre a transformacao feita pela camada oculta
		hidden_fnet = np.array([self.activ(x) for x in hidden_net])

		#Adiciona um componente "1" ao vetor produzido pela camada oculta para permitir calculo do bias
		#na camada de saida
		biased_hidden_activ = np.zeros((self.hidden_length+1))
		biased_hidden_activ[0:self.hidden_length] = hidden_fnet[:]
		biased_hidden_activ[self.hidden_length] = 1
		
		#Calcula a transformacao feita pela camada de saida usando produto de matriz por vetor
		#Wo x H = net, sendo Wo a matriz de pesos da camada de saida e H o vetor produzido pela ativacao
		#da camada oculta
		out_net = np.dot(self.output_layer, biased_hidden_activ)
		#Aplica a funcao de ativacao nos valores produzidos pela transformacao da camada de saida
		out_fnet = np.array([self.activ(x) for x in out_net])

		#Retorna net e f(net) da camada oculta e da camada de saida
		return hidden_net, hidden_fnet, out_net, out_fnet

	#Faz backpropagation
	def fit(self, input_samples, target_labels, learning_rate, threshold):
		print('backpropagating')
		#Erro quadratico medio eh inicializado com um valor arbitrario (maior que o threshold de parada)
		#p/ comecar o treinamento
		mean_squared_error = 2*threshold

		#Inicializa o numero de epocas ja computadas
		epochs = 0

		#Enquanto não chega no erro quadratico medio desejado ou atingir 5000 epocas, continua treinando
		while(mean_squared_error > threshold and epochs < 5000):
			#Erro quadratico medio da epoca eh inicializado com 0
			mean_squared_error = 0
			
			#Passa por todos os exemplos do dataset
			for i in range(0, input_samples.shape[0]):
				if(i % 200 == 0):
					print('current sample', i)
				#Pega o exemplo da iteracao atual
				input_sample = input_samples[i]
				#Pega o label esperado para o exemplo da iteracao atual
				target_label = target_labels[i]

				#Pega net e f(net) da camada oculta e da camada de saida
				hidden_net, hidden_fnet, out_net, out_fnet = self.forward_training(input_samples[i])
				
				#Cria um vetor com o erro de cada neuronio da camada de saida
				error_array = (target_label - out_fnet)

				#Calcula a variacao dos pesos da camada de saida com a regra delta generalizada
				#delta_o_pk = (Ypk-Ok)*Opk(1-Opk), sendo p a amostra atual do conjunto de treinamento,
				#e k um neuronio da camada de saida. Ypk eh a saida esperada do neuronio pelo exemplo do dataset,
				#Opk eh a saida de fato produzida pelo neuronio
				delta_output_layer = error_array * self.deriv_activ(out_fnet)

				#Calcula a variacao dos pesos da camada oculta com a regra delta generalizada
				#delta_h_pj = f'(net_h)*(1-f(net_h))*somatoria(delta_o_k*wkj)
				output_weights = self.output_layer[:,0:self.hidden_length]

				hidden_layer_local_gradient = np.zeros(self.hidden_length)
				for hidden_neuron in range(0, self.hidden_length):
					for output_neuron in range(0, self.output_length):
							hidden_layer_local_gradient[hidden_neuron] += delta_output_layer[output_neuron]*\
								output_weights[output_neuron, hidden_neuron]
				
				delta_hidden_layer = self.deriv_activ(hidden_fnet) * hidden_layer_local_gradient
				
				hidden_fnet_with_bias = np.zeros(hidden_fnet.shape[0]+1)
				hidden_fnet_with_bias[0:self.hidden_length] = hidden_fnet[:]
				hidden_fnet_with_bias[self.hidden_length] = 1
				#Atualiza os pesos da camada de saida
				#Wkj(t+1) = wkj(t) + eta*deltak*Ij
				for neuron in range(0, self.output_length):
					for weight in range(0, self.output_layer.shape[1]):
						self.output_layer[neuron, weight] = self.output_layer[neuron, weight] + \
							learning_rate * delta_output_layer[neuron] * hidden_fnet_with_bias[weight]

				#Atualiza os pesos da camada oculta com a regra delta generalizada
				#Pega os pesos dos neuronios da camada de saida (bias da camada de saida nao entra)
				#Wji(t+1) = Wji(t)+eta*delta_h_j*Xi
				input_sample_with_bias = np.zeros(input_sample.shape[0]+1)
				input_sample_with_bias[0:input_sample.shape[0]] = input_sample[:]
				input_sample_with_bias[input_sample.shape[0]] = 1
				for neuron in range(0, self.hidden_length):
					for weight in range(0, self.hidden_layer.shape[1]):
						self.hidden_layer[neuron, weight] = self.hidden_layer[neuron, weight] + \
							learning_rate*delta_hidden_layer[neuron]*input_sample_with_bias[weight]
							#np.dot(delta_hidden_layer.T, input_sample_with_bias)

				#O erro da saída de cada neuronio é elevado ao quadrado e somado ao erro total da epoca
				#para calculo do erro quadratico medio ao final
				mean_squared_error = mean_squared_error + np.sum(error_array**2)			
			
			#Divide o erro quadratico total pelo numero de exemplos para obter o erro quadratico medio
			mean_squared_error = mean_squared_error/input_samples.shape[0]
			#print('Erro medio quadratico', mean_squared_error)
			epochs = epochs + 1
			#if(epochs % 1000 == 0):
			print('rmse', mean_squared_error)

		print('total epochs run', epochs)
		print('final rmse', mean_squared_error)
		return None

#Testa a mlp com funcoes logicas
def test_logic():
	mlp = MLP(*(2, 2, 1))

	print('\n\noutput before backpropagation')
	print('[0,0]=', mlp.forward([0,0]))
	print('[0,1]=', mlp.forward([0,1]))
	print('[1,0]=', mlp.forward([1,0]))
	print('[1,1]=', mlp.forward([1,1]))

	print('layers before backprop')
	print('hidden', mlp.hidden_layer)
	print('output layer', mlp.output_layer)
	print('\n')	

	x = np.array([[0,0],[0,1],[1,0],[1,1]])
	target = np.array([0, 0, 0, 1])
	mlp.fit(x, target, 5e-1, 10e-1)

	print('\n\noutput after backpropagation')
	print('[0,0]=', mlp.forward([0,0]))
	print('[0,1]=', mlp.forward([0,1]))
	print('[1,0]=', mlp.forward([1,0]))
	print('[1,1]=', mlp.forward([1,1]))
	print('layers after backprop')
	print('hidden', mlp.hidden_layer)
	print('output layer', mlp.output_layer)

#Carrega o dataset de digitos
def load_digits():
	data = np.zeros([1593, 256])
	labels = np.zeros([1593, 10])

	with open('semeion.data') as file:
		for image_index, line in enumerate(file):
			number_list = np.array(line.split())
			image = number_list[0:256].astype(float).astype(int)
			classes = number_list[256:266].astype(float).astype(int)
			data[image_index,:] = image[:]
			labels[image_index,:] = classes[:]
			
	return data, labels

def plot_image(image):
	news_image = image.reshape(16,16)
	plt.imshow(new_image)
	plt.show()

#Faz predicao da classe de todos os dados e compara com as classes esperadas
def measure_score(mlp, data, target):
	dataset_size = target.shape[0]
	score = 0
	
	for index, data in enumerate(data):
		expected_class = np.argmax(target[index])
		predicted_class = np.argmax(mlp.forward(data))
		if(expected_class == predicted_class):
			score += 1

	return score, (score/dataset_size)*100	

#Embaralha dois arrays de forma simetrica
def shuffle_two_arrays(data, labels):
	permutation = np.random.permutation(data.shape[0])
	print('created a permutation of shape', permutation.shape)
	return data[permutation], labels[permutation]

#Gera os indices de cada um dos k-folds
def k_folds_split(dataset_size, k):
	fold_size = int(dataset_size/k)
	folds = np.zeros((k, fold_size))

	for current_k in range(0, k):
		fold_indexes = range(current_k*fold_size, (current_k+1)*fold_size)
		folds[current_k] = fold_indexes

	return folds

#Gera os indices, dividindo os dados entre treino e teste utilizando os folds calculados
def train_test_split(folds):
	fold_qtt = folds.shape[0]
	fold_size = folds.shape[1]
	train_set_size = (fold_qtt-1)*fold_size
	test_set_size = fold_size

	train_sets = np.zeros((fold_qtt, train_set_size))
	test_sets = np.zeros((fold_qtt, test_set_size))

	for fold_to_skip in range(0, fold_qtt):
		train_set = np.zeros(train_set_size)
		test_set = np.zeros(test_set_size)
		added_folds = 0

		for fold_index, current_fold in enumerate(folds):
			if(fold_index != fold_to_skip):
				train_set[added_folds*fold_size:(added_folds+1)*fold_size] = current_fold
				added_folds += 1
			else:
				test_set[0:fold_size] = current_fold

		train_sets[fold_to_skip] = train_set
		test_sets[fold_to_skip] = test_set

	return train_sets, test_sets

def main():
	#test_logic()
	data, labels = load_digits()

	mlp = None
	if(not os.path.isfile('mlp.pickle')):
		print('No model file exists yet. Fitting new model...')		
		mlp = MLP(*[256, 128, 10])
		mlp.fit(data, labels, 5e-1, 5e-2)
		mlp.save_to_disk('mlp.pickle')
	else:
		print('Model file found on disk. Loading...')
		with open('mlp.pickle', 'rb') as file:
			mlp = pickle.load(file)


	shuffled_data, shuffled_labels = shuffle_two_arrays(np.array(range(0,50)), np.zeros((50)))
	folds = k_folds_split(shuffled_data.shape[0], 5)
	train_sets, test_sets = train_test_split(folds)
	
	print('train sets', train_sets)
	print('test sets', test_sets)

	score, accuracy = measure_score(mlp, data, labels)
	#print('Total score:', score)
	#print('Accuracy:', accuracy)

if __name__ == '__main__':
	main()