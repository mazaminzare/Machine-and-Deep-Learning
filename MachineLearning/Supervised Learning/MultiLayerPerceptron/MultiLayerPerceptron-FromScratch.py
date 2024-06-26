import numpy as np
import pandas as pd


class DenseLayer:
    def __init__(self, neurons):
        self.neurons = neurons

    def relu(self, inputs):
        """
         ReLU Activation Function
        """
        return np.maximum(0, inputs)

    def softmax(self, inputs):
        """
        Softmax Activation Function
        """
        exp_scores = np.exp(inputs)
        probs = exp_scores / np.sum(exp_scores, axis=1, keepdims=True)
        return probs

    def relu_derivative(self, dA, Z):
        """
        ReLU Derivative Function
        """
        dZ = np.array(dA, copy=True)
        dZ[Z < 0] = 0
        return dZ
        raise NotImplementedError

    def forward(self, inputs, weights, bias, activation):
        """
        Single Layer Forward Propagation
        """
        Z_curr = np.dot(inputs, weights.T) + bias

        if activation == "relu":
            A_curr = self.relu(inputs=Z_curr)
        elif activation == 'softmax':
            A_curr = self.softmax(inputs=Z_curr)

        return A_curr, Z_curr

    def backward(self, dA_curr, W_curr, Z_curr, A_prev, activation):
        """
        Single Layer Backward Propagation
        """
        if activation == 'softmax':
            dW = np.dot(A_prev.T, dA_curr)
            db = np.sum(dA_curr, axis=0, keepdims=True)
            dA = np.dot(dA_curr, W_curr)
        elif activation == 'relu':
            dZ = self.relu_derivative(dA_curr, Z_curr)
            dW = np.dot(A_prev.T, dZ)
            db = np.sum(dZ, axis=0, keepdims=True)
            dA = np.dot(dZ, W_curr)

        return dA, dW, db


class Network:
    def __init__(self):
        self.network = []  ## layers
        self.architecture = []  ## mapping input neurons --> output neurons
        self.params = []  ## W, b
        self.memory = []  ## Z, A
        self.gradients = []  ## dW, db

    def add(self, layer):
        """
        Add layers to the network
        """
        self.network.append(layer)

    def _compile(self, data):
        """
        Initialize model architecture
        """

        for idx, layer in enumerate(self.network):
            if idx == 0:
                self.architecture.append({'input_dim': data.shape[1],
                                          'output_dim': self.network[idx].neurons,
                                          'activation': 'relu'})
            elif 0 < idx < len(self.network) - 1:
                self.architecture.append({'input_dim': self.network[idx - 1].neurons,
                                          'output_dim': self.network[idx].neurons,
                                          'activation': 'relu'})
            else:
                self.architecture.append({'input_dim': self.network[idx - 1].neurons,
                                          'output_dim': self.network[idx].neurons,
                                          'activation': 'softmax'})

        return self

    def _init_weights(self, data, init_method="xavier"):
        """
        Initialize the model parameters
        """
        self._compile(data)
        np.random.seed(99)
        if init_method == "random":
            for i in range(len(self.architecture)):
                self.params.append(
                    {
                        'W': np.random.uniform(low=-1, high=1,
                                               size=(self.architecture[i]['output_dim'],
                                                     self.architecture[i]['input_dim'])),
                        'b': np.zeros((1, self.architecture[i]['output_dim']))
                    }
                )
        # better to use in Tanh or Sigmoid
        elif init_method == "xavier":
            for i in range(len(self.architecture)):
                self.params.append(
                    {
                        'W': np.random.randn(self.architecture[i]['output_dim']
                                             , self.architecture[i]['input_dim']) * np.sqrt(
                            1 / self.architecture[i]['input_dim']),
                        'b': np.zeros((1, self.architecture[i]['output_dim']))

                    }
                )

        # better to use in Relu
        elif init_method == "he":
            for i in range(len(self.architecture)):
                self.params.append(
                    {
                        'W': np.random.randn(self.architecture[i]['output_dim']
                                             , self.architecture[i]['input_dim']) * np.sqrt(
                            2 / self.architecture[i]['input_dim']),
                        'b': np.zeros((1, self.architecture[i]['output_dim']))

                    }
                )

        return self

    def _forwardprop(self, data):
        """
        Performs one full forward pass through network
        """

        A_curr = data

        for i in range(len(self.params)):
            A_perv = A_curr
            A_curr, Z_curr = self.network[i].forward(
                inputs=A_perv,
                weights=self.params[i]['W'],
                bias=self.params[i]['b'],
                activation=self.architecture[i]['activation']
            )
            self.memory.append({'inputs': A_perv, 'Z': Z_curr})

        return A_curr

    def _backprop(self, predicted, actual):
        """
        Performs one full backward pass through network
        """
        num_samples = len(actual)

        ## compute the gradient on predictions

        dscores = predicted
        dscores[range(num_samples), actual] -= 1
        dscores /= num_samples

        dA_perv = dscores

        for idx, layer in reversed(list(enumerate(self.network))):
            dA_curr = dA_perv

            A_perv = self.memory[idx]['inputs']
            Z_curr = self.memory[idx]['Z']
            W_curr = self.params[idx]['W']

            activation = self.architecture[idx]['activation']

            dA_perv, dW_curr, db_curr = layer.backward(dA_curr, W_curr, Z_curr, A_perv, activation)

            self.gradients.append({'dW': dW_curr, 'db': db_curr})

    def _update(self, lr=0.01):
        """
        Update the model parameters --> lr * gradient
        """

        for idx, layer in enumerate(self.network):
            self.params[idx]['W'] -= lr * list(reversed(self.gradients))[idx]['dW'].T
            self.params[idx]['b'] -= lr * list(reversed(self.gradients))[idx]['db']

    def _get_accuracy(self, predicted, actual):
        """
        Calculate accuracy after each iteration
        """
        return np.mean(np.argmax(predicted, axis=1) == actual)

        raise NotImplementedError

    def _calculate_loss(self, predicted, actual):
        """
        Calculate cross-entropy loss after each iteration
        """
        samples = len(actual)
        correct_logprobs = -np.log(predicted[range(samples), actual])
        data_loss = np.sum(correct_logprobs) / samples
        return data_loss

    def train(self, X_train, y_train, epochs):
        """
        Train the model using SGD
        """
        self.loss = []
        self.accuracy = []

        self._init_weights(X_train)

        for i in range(epochs):
            yhat = self._forwardprop(X_train)
            self.accuracy.append(self._get_accuracy(predicted=yhat, actual=y_train))
            self.loss.append(self._calculate_loss(predicted=yhat, actual=y_train))

            self._backprop(predicted=yhat, actual=y_train)
            self._update(lr=0.01)
            if i % 20 == 0:
                s = f'EPOCH: {i}, ACCURACY: {self.accuracy[-1]}, LOSS: {self.loss[-1]}'
                print(s)

    def test(self, X_test, y_test):
        """
        Test the model
        """
        self.loss = []
        self.accuracy = []


        yhat = self._forwardprop(X_test)
        self.accuracy.append(self._get_accuracy(predicted=yhat, actual=y_test))
        self.loss.append(self._calculate_loss(predicted=yhat, actual=y_test))

        s = f'Test Results: ACCURACY: {self.accuracy[-1]}, LOSS: {self.loss[-1]}'
        print(s)


from sklearn.preprocessing import LabelEncoder


def get_data(path):
    data = pd.read_csv(path, index_col=0)
    cols = list(data.columns)
    target = cols.pop()
    X = data[cols].copy()
    y = data[target].copy()
    y = LabelEncoder().fit_transform(y)
    return np.array(X), np.array(y)


def model_summery(model):
    print("Network Architecture")
    [print(layer) for layer in model.architecture]
    print("=============================")
    print("Network Parameters Shape")
    [print(params['W'].shape, params['b'].shape) for params in model.params]


X, y = get_data("iris.csv")
epochs = 1000
model = Network()
model.add(DenseLayer(6))
model.add(DenseLayer(8))
model.add(DenseLayer(10))
model.add(DenseLayer(3))
# Train Model
print("Training the Model")
model.train(X, y, epochs)
# Test Model
print("Testing the Model")
model.test(X, y)