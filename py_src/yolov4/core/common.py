import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.layers import Layer
from typing import Union


class BatchNormalization(tf.keras.layers.BatchNormalization):
    """
    "Frozen state" and "inference mode" are two separate concepts.
    `layer.trainable = False` is to freeze the layer, so the layer will use
    stored moving `var` and `mean` in the "inference mode", and both `gama`
    and `beta` will not be updated !
    """

    def call(self, x, training=False):
        if not training:
            training = tf.constant(False)
        training = tf.logical_and(training, self.trainable)
        return super().call(x, training)


class Mish(Layer):
    def __init__(self, **kwargs):
        super(Mish, self).__init__(**kwargs)

    def call(self, inputs):
        return inputs * tf.tanh(tf.math.log(1 + tf.exp(inputs)))


class YOLOConv2D(Layer):
    def __init__(
        self,
        filters: int,
        kernel_size: Union[int, tuple],
        strides: Union[int, tuple] = 1,
        activation: str = "mish",
        **kwargs
    ):
        super(YOLOConv2D, self).__init__(**kwargs)

        self.filters = filters

        if isinstance(kernel_size, int):
            self.kernel_size = (kernel_size, kernel_size)
        else:
            self.kernel_size = kernel_size

        if isinstance(strides, int):
            self.strides = (strides, strides)
        else:
            self.strides = strides

        self.activation = activation

        self.sequential = tf.keras.Sequential()

        if self.strides[0] == 2:
            self.sequential.add(layers.ZeroPadding2D(((1, 0), (1, 0))))

        self.sequential.add(
            layers.Conv2D(
                filters=self.filters,
                kernel_size=self.kernel_size,
                padding="same" if self.strides[0] == 1 else "valid",
                strides=self.strides,
                use_bias=False if self.activation is not None else True,
                kernel_regularizer=tf.keras.regularizers.l2(0.0005),
                kernel_initializer=tf.random_normal_initializer(stddev=0.01),
                bias_initializer=tf.constant_initializer(0.0),
            )
        )

        if self.activation is not None:
            self.sequential.add(layers.BatchNormalization())

        if self.activation == "mish":
            self.sequential.add(Mish())
        elif self.activation == "leaky":
            self.sequential.add(layers.LeakyReLU(alpha=0.1))
        elif self.activation == "relu":
            self.sequential.add(layers.ReLU())

    def build(self, input_shape):
        self.input_dim = input_shape[-1]

    def call(self, x):
        return self.sequential(x)
