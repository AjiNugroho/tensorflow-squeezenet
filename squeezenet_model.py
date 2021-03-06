import tensorflow as tf 
import numpy as np

"""
Class file for SqueezeNet Model
"""

"""
Fire Module Definition
"""
def fire_module(inputs,s1x1,e1x1,e3x3,name="fire"):
    w_init = tf.truncated_normal_initializer(mean=0.0, stddev=(1.0/int(inputs.shape[2])))
    
    with tf.variable_scope(name):
        #squeeze layer
        squeeze_out = tf.layers.conv2d(inputs,filters=s1x1,kernel_size=1,strides=1,padding="VALID",kernel_initializer=w_init)
        relu_sq = tf.nn.relu(squeeze_out)
    
        #expand layer
        k1_exp = tf.layers.conv2d(relu_sq,filters=e1x1,kernel_size=1,strides=1,padding="VALID",kernel_initializer=w_init)
        k1_relu = tf.nn.relu(k1_exp)
        k3_exp = tf.layers.conv2d(relu_sq,filters=e3x3,kernel_size=3,strides=1,padding="SAME",kernel_initializer=w_init)
        k3_relu = tf.nn.relu(k3_exp)
        
        return tf.concat([k1_relu,k3_relu],axis=3)

"""
General Convolution Operation
"""
def general_conv(inputs,filters,kernel,stride=1,padding='VALID',name="conv",relu = True,weight="Xavier"):
    if str(weight) == str("Xavier"):
        w_init = tf.truncated_normal_initializer(mean=0.0,stddev=(1.0/int(inputs.shape[2])))
    else:
        w_init = tf.truncated_normal_initializer(mean=0.0,stddev=0.01)
        
    with tf.variable_scope(name):
        conv = tf.layers.conv2d(inputs,filters,kernel,stride,padding,kernel_initializer=w_init)
        if relu == True:
                conv = tf.nn.relu(conv)
        return conv

"""
SqueezeNet Class Definition
"""
class SqueezeNet:
    
    def __init__(self,input_shape,out_classes,lr_rate,train):
        self.lr_rate = tf.placeholder(tf.float32,name="lr_rate")
        self.out_classes = out_classes
        self.inputs = tf.placeholder(tf.float32,shape=(None,input_shape[0],input_shape[1],input_shape[2]))
        self.labels = tf.placeholder(tf.float32,shape=(None,self.out_classes))
        self.loss_v1 = self.model_loss(self.inputs,self.labels,train)     
        self.v1_opt = self.model_opti(self.loss_v1,self.lr_rate)
        
        
    #Model Definiton of SqueezeNet V1    
    def model_arc_v1(self,inputs,train,reuse=False):
        
        with tf.variable_scope("squeezenet_v1",reuse=reuse):
            conv1 = general_conv(inputs,filters=64,kernel=3,stride=2,padding="SAME",name="conv1",relu=True,weight="Xavier")
            pool1 = tf.layers.max_pooling2d(conv1,pool_size=3,strides=2,name="pool1")
            
            fire2 = fire_module(pool1,16,64,64,name="fire2")
            fire3 = fire_module(fire2,16,64,64,name="fire3")
            
            pool2 = tf.layers.max_pooling2d(fire3,pool_size=3,strides=2,name="pool2")
            
            fire4 = fire_module(pool2,32,128,128,name="fire4")
            fire5 = fire_module(fire4,32,128,128,name="fire5")
            
            pool3 = tf.layers.max_pooling2d(fire5,pool_size=3,strides=2,name="pool3")
            
            fire6 = fire_module(pool3,48,192,192,name="fire6")
            fire7 = fire_module(fire6,48,192,192,name="fire7")
            fire8 = fire_module(fire7,64,256,256,name="fire8")       
            fire9 = fire_module(fire8,64,256,256,name="fire9")
            drop = tf.layers.dropout(fire9,rate=0.5,training=train)
        
            conv10 = general_conv(drop,filters=200,kernel=1,stride=1,padding="SAME",name="conv10",relu=True,weight="Gaussian")
        
            avg_pool = tf.layers.average_pooling2d(conv10,pool_size=13,strides=1,name="pool_end")
        
            pool_shape = tf.shape(avg_pool)
            logits = tf.reshape(avg_pool,shape=(pool_shape[0],pool_shape[3]))
        
            return logits       

    #Function to calculate loss 
    def model_loss(self,inputs,label,train):
        logits_v1 = self.model_arc_v1(inputs,train)
        
        loss_v1 = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=logits_v1,labels=label))
        
        return loss_v1
    
    #Function to calculate prediction form models
    def model_prediction(self,inputs,train):
        logits_v1 = self.model_arc_v1(inputs,train,True)
        
        predict_v1 = tf.nn.softmax(logits_v1)
        
        return predict_v1
    
    #Function to optimize the models. 
    def model_opti(self,loss_v1,lr_rate):
        
        #train_vars = tf.trainable_variables()

        #v1_vars = [var for var in train_vars if var.name.startswith('squeezenet_v1')]        
        v1_vars = tf.Variable()
        #Using Adam Optimizer 
        with tf.control_dependencies(tf.get_collection(tf.GraphKeys.UPDATE_OPS)):

            v1_train_opt = tf.train.AdamOptimizer(lr_rate).minimize(loss_v1,var_list=v1_vars)
            
        return v1_train_opt
    
    def load(self, data_path, session, ignore_missing=False):
        '''Load network weights.
        data_path: The path to the numpy-serialized network weights
        session: The current TensorFlow session
        ignore_missing: If true, serialized weights for missing layers are ignored.
        '''
        data_dict = np.load(data_path).item()
        for op_name in data_dict:
            with tf.variable_scope(op_name, reuse=True):
                for param_name, data in data_dict[op_name].iteritems():
                    try:
                        var = tf.get_variable(param_name)
                        session.run(var.assign(data))
                    except ValueError:
                        if not ignore_missing:
                            raise

        
        
        
        
        
