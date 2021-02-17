import os
import argparse
import time

import tensorflow as tf
import tensorflow.keras as keras
from tensorflow.compat.v1 import ConfigProto
from tensorflow.compat.v1 import InteractiveSession
from tensorflow.compat.v1.keras import backend
import tensorflow.compat.v1 as tf1
import tensorflow.compat.v1.keras.callbacks as callbacks
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
from tensorflow.keras.mixed_precision import experimental as mixed_precision
from tensorflow.keras.preprocessing.image import ImageDataGenerator

'''
import torch
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.datasets as datasets
'''

# Tensorflow keras models
from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.applications import DenseNet169
from tensorflow.keras.applications import DenseNet201
from tensorflow.keras.applications import InceptionV3
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications import ResNet101
from tensorflow.keras.applications import ResNet152
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications import VGG16
from tensorflow.keras.applications import VGG19

# Pytorch vision models
'''
from torchvision.models import densenet121
from torchvision.models import densenet169
from torchvision.models import densenet201
from torchvision.models import inception_v3
from torchvision.models import mobilenet_v2
from torchvision.models import resnet101
from torchvision.models import resnet152
from torchvision.models import resnet50
from torchvision.models import vgg16
from torchvision.models import vgg19
'''

# only in Tensorflow
from tensorflow.keras.applications import Xception
from tensorflow.keras.applications import InceptionResNetV2
from tensorflow.keras.applications import MobileNet
from tensorflow.keras.applications import NASNetLarge
from tensorflow.keras.applications import NASNetMobile
from tensorflow.keras.applications import ResNet101V2
from tensorflow.keras.applications import ResNet152V2
from tensorflow.keras.applications import ResNet50V2

# only in Pytorch
'''
from torchvision.models import alexnet
from torchvision.models import vgg11
from torchvision.models import vgg11_bn
from torchvision.models import vgg13
from torchvision.models import vgg13_bn
from torchvision.models import vgg16_bn
from torchvision.models import vgg19_bn
from torchvision.models import resnet18
from torchvision.models import resnet34
from torchvision.models import squeezenet1_0
from torchvision.models import squeezenet1_1
from torchvision.models import densenet161
from torchvision.models import googlenet
from torchvision.models import shufflenet_v2_x0_5
from torchvision.models import shufflenet_v2_x1_0
from torchvision.models import shufflenet_v2_x1_5
from torchvision.models import shufflenet_v2_x2_0
from torchvision.models import resnext50_32x4d
from torchvision.models import resnext101_32x8d
from torchvision.models import wide_resnet50_2
from torchvision.models import wide_resnet101_2
from torchvision.models import mnasnet0_5
from torchvision.models import mnasnet0_75
from torchvision.models import mnasnet1_0
from torchvision.models import mnasnet1_3
'''

# arument setting
parser = argparse.ArgumentParser(description='System Software Lab. deep learning workload execution')
# high level argument
parser.add_argument("-d", "--data", required=True, help="path to the input image")
parser.add_argument("--profiling", default='/root/research/munkyu/profiling_real', help='profiling directory')
parser.add_argument("-p", "--platform", default='tensorflow', help="select platform")
parser.add_argument("-m", "--model", default='resnet', help="select model")
parser.add_argument("-l", "--layer", default='50', help="select layer")
parser.add_argument("-f", "--fraction", type=float, default=1, help="select layer")
parser.add_argument("-g", "--grow", default=0, type=int, help="select layer")
parser.add_argument("--gpus", default=0, nargs='*', type=int, help="select one gpu")
parser.add_argument("--workers", default=20, type=int, help="select cpu number")

# low level argument
parser.add_argument('-b', '--batch-size', default=64, type=int, metavar='N',
                    help='mini-batch size (default: 64), this is the total '
                         'batch size of all GPUs on the current node when '
                         'using Data Parallel or Distributed Data Parallel')
parser.add_argument('--epochs', default=200, type=int, metavar='N', help='number of total epochs to run')
parser.add_argument('--steps', default=None, type=int, metavar='N', help='number of steps')
parser.add_argument('--validations', default=10, type=int, metavar='N', help='number of total validations to run')
parser.add_argument('--lr', '--learning-rate', default=0.001, type=float, metavar='LR', help='initial learning rate', dest='lr')
parser.add_argument('--loss', default='categorical_crossentropy', help='loss function select')
parser.add_argument('--precision', default='float32', type=str, metavar='N', help='precision select')
parser.add_argument('--loop', default=0, type=int, metavar='N', help='if this is TRUE, execute again and again')
#parser.add_argument('--opt', default='')
args = parser.parse_args()

# main function
def main():
    memory_start_time = time.time()
    train, validation = dataLoad(plat=args.platform, dataset='imagenet')
    memory_end_time = time.time()
    dataload_time = memory_end_time - memory_start_time

    log.write("dataload time is %10.5f\n\n" %dataload_time);

    model = build(plat=args.platform, model=args.model, layer= args.layer)
    #setting(model)
    #train(model, train, validation)
    if args.platform=='tensorflow':
        #with tf.device('/gpu:' + str(args.gpu)):
        #with tf.device('/gpu:0'):
            customHistory = CustomHistory()
            customHistory.init()
        
            '''
            model.fit(train, epochs=args.epochs, steps_per_epoch=args.steps, workers=args.workers,
                        validation_data=validation, validation_steps=args.validations, callbacks=[customHistory],
                        use_multiprocessing=True)

            model.fit(train, epochs=args.epochs, steps_per_epoch=args.steps, workers=args.workers,
                        callbacks=[customHistory])

            model.evaluate(validation, steps=args.steps, use_multiprocessing=True, workers=args.workers,
                        callbacks=[customHistory])
            '''
            example_result = model.predict(validation, steps=args.steps, callbacks=[customHistory], workers=args.workers)
            print(example_result)


            customHistory.printAverage()

    elif args.platform=='pytorch':
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.train()
        
        if (args.precision == 'float16'):
            model = model.half()
        criterion = torch.nn.CrossEntropyLoss()
        optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
        losses = AverageMeter('Loss', ':.4e')
        top1 = AverageMeter('Acc@1', ':6.2f')
        top5 = AverageMeter('Acc@5', ':6.2f')
        running_loss = 0.0
        Totaltime = 0
        if not args.steps : step = 0
        else : step = args.steps

        for epoch in range(0, args.epochs):
            print()
            print('%d epoch start' %(epoch+1))
            
            startTime = time.time()
            num_steps = 0
            stepTotalTime = 0
            stepSumtime = 0
            stepN = 0

            for i, (images, target) in enumerate(train):

                '''
                total = 0 
                correct = 0 
                '''

                if step == 0 :
                    pass
                elif i >= step :
                    break

                stepStartTime = time.time()
                images = images.to(device)
                target = target.to(device)
                optimizer.zero_grad()

                if (args.precision == 'float16'):
                    images = images.half()
                    target = target.half()

                output = model(images)
                
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()
                acc1, acc5 = accuracy(output.data, target, topk=(1, 5))

                '''
                _, predicted = output.max(1)
                total += target.size(0)
                correct += predicted.eq(target).sum().item()
                '''

                losses.update(loss.item(), images.size(0))
                top1.update(acc1[0], images.size(0))
                top5.update(acc5[0], images.size(0))
                running_loss += loss.item()

                stepEndTime = time.time()
                stepThisTime = stepEndTime - stepStartTime
                stepTotalTime += stepThisTime
                stepN += 1

                if i % 10 == 0:    # print every 640 images (10 batch)
                    '''
                    print(' Acc: %.3f%% (%d/%d)'
                        % ((100.*correct/total), correct, total))
                    '''
                    
                    print('\r steps : %5d | loss: %10.5f | time : %10.5fsec | top5 acc : %10.5f%% | top1 acc : %10.5f%% ' %
                            (i+1, (running_loss / len(images)), stepThisTime, top5.avg, top1.avg), end='')
                            
                    running_loss = 0.0
                    
            print("\n Mean training time : %10.5f" %(stepTotalTime / stepN))
            log.write(" Mean step time : %10.5f\n" %(stepTotalTime / stepN))
            stepSumtime += stepTotalTime/stepN
            print()

            endTime = time.time()
            thisTime = endTime - startTime
            Totaltime += thisTime            
            print('This epoch time :', thisTime)
            log.write(' one epoch time : %10.5f\n' %thisTime)

        print()    
        print('Finished Training')
        print("Average step time : ", stepSumtime/args.epochs)
        log.write("Average step time : %10.5f\n" %(stepSumtime/args.epochs))
        print("average epoch time :", Totaltime/args.epochs)
        log.write("Average epoch time : %10.5f\n" %(Totaltime/args.epochs))
            
        model.to(device)
        model.eval()
        
        losses = AverageMeter('Loss', ':.4e')
        top1 = AverageMeter('Acc@1', ':6.2f')
        top5 = AverageMeter('Acc@5', ':6.2f')
        valTotalTime = 0
        for i, (images, target) in enumerate(validation):
            if i >= args.validations :
                break
            valStartTime = time.time()
            images = images.to(device)
            target = target.to(device)

            if (args.precision == 'float16'):
                images = images.half()

            output = model(images)

            loss = criterion(output, target)
            acc1, acc5 = accuracy(output, target, topk=(1, 5))

            losses.update(loss.item(), images.size(0))
            top1.update(acc1[0], images.size(0))
            top5.update(acc5[0], images.size(0))

            valEndTime = time.time()
            valThisTime = valEndTime - valStartTime
            valTotalTime += valThisTime
            print('\r validations : {i:5d} | Acc@1 : {top1.avg:7.3f} | Acc@5 : {top5.avg:7.3f} | time : {time:7.3f}'
                      .format(i=i+1, top1=top1, top5=top5, time=valThisTime), end='')
        print('\n Mean validation time :', valTotalTime/args.validations)
        log.write(' Mean validation time : %10.5f\n' %(valTotalTime/args.validations))
                
    else : print("Unknown platform!")

# Data Load
def dataLoad(plat='tensorflow', dataset='imagenet'):
    traindir = os.path.join(args.data, 'train')
    valdir = os.path.join(args.data, 'val')
    if plat=='pytorch':
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                         std=[0.229, 0.224, 0.225])
        train_dataset = datasets.ImageFolder(
            traindir,
            transforms.Compose([
                transforms.RandomResizedCrop(224),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                normalize,
            ]))

        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=args.batch_size, num_workers=args.workers, pin_memory=True)

        val_loader = torch.utils.data.DataLoader(
            datasets.ImageFolder(valdir, transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                normalize,
            ])),
            batch_size=args.batch_size, shuffle=False,
            num_workers=args.workers, pin_memory=True)

        return train_loader, val_loader

    elif plat=='tensorflow':
        #mirrored_strategy = tf.distribute.MirroredStrategy(devices=["/gpu:0", "/gpu:1"])
        #with mirrored_strategy.scope(): 
            train_datagen = ImageDataGenerator(rescale=1./255)
            val_datagen = ImageDataGenerator(rescale=1./255)

            train_generator = train_datagen.flow_from_directory(traindir, batch_size=args.batch_size, target_size=(224, 224), color_mode='rgb')
            val_generator = val_datagen.flow_from_directory(valdir, batch_size=args.batch_size, target_size=(224, 224), color_mode='rgb')

            return train_generator, val_generator

# Model build
def build(plat='tensorflow', model='resnet', layer='50'):
    if plat=='tensorflow':
        #mirrored_strategy = tf.distribute.MirroredStrategy()
        #with mirrored_strategy.scope():
            if model=='densenet':
                if layer=='121':
                    buildingModel = DenseNet121(weights=None, include_top=True)
                elif layer=='169':
                    buildingModel = DenseNet169(weights=None, include_top=True)
                elif layer=='201':
                    buildingModel = DenseNet201(weights=None, include_top=True)
                else : print('Unknown layer!')

            elif model=='inception':
                buildingModel = InceptionV3(weights=None, include_top=True)

            elif model=='mobilenet':
                buildingModel = MobileNetV2(weights=None, include_top=True)

            elif model=='resnet':
                if layer=='50':
                    buildingModel = ResNet50(weights='imagenet', include_top=True)
                elif layer=='101':
                    buildingModel = ResNet101(weights=None, include_top=True)
                elif layer=='152':
                    buildingModel = ResNet152(weights=None, include_top=True)    
                else : print("Unknown layer!")

            elif model=='vgg':
                if layer=='16':
                    buildingModel = VGG16(weights=None, include_top=True)
                elif layer=='19':
                    buildingModel = VGG19(weights=None, include_top=True)
                else : print("Unknown layer!")

            opt = tf.keras.optimizers.SGD(lr=0.001, momentum=0.9)
            buildingModel.compile(loss=args.loss, optimizer=opt, metrics=[tf.keras.metrics.TopKCategoricalAccuracy(), 'accuracy'])

    elif plat=='pytorch':
        if model=='densenet':
            if layer=='121':
                buildingModel = densenet121(pretrained=False)
            elif layer=='169':
                buildingModel = densenet169(pretrained=False)
            elif layer=='201':
                buildingModel = densenet201(pretrained=False)
            else : print("Unknown layer!")
        elif model=='inception':
            buildingModel = inception_v3(pretrained=False)
        elif model=='mobilenet':
            buildingModel = mobilenet_v2(pretrained=False)
        elif model=='resnet':
            if layer=='50':
                buildingModel = resnet50(pretrained=False)
            elif layer=='101':
                buildingModel = resnet101(pretrained=False)
            elif layer=='152':
                buildingModel = resnet152(pretrained=False)
            else : print("Unknown layer!")
        elif model=='vgg':
            if layer=='16':
                buildingModel = vgg16(pretrained=False)
            elif layer=='19':
                buildingModel = vgg19(pretrained=False)
            else : print("Unknown layer!")
    else : print("Unknown platform!")
    return buildingModel

# training setting
def setting(settingModel):
    if args.platform=='tensorflow':
        mirrored_strategy = tf.distribute.MirroredStrategy(devices=["/gpu:0", "/gpu:1"])
        with mirrored_strategy.scope():

            #opt = tf.keras.optimizers.Adam()

            #policy = mixed_precision.Policy('mixed_float16')
            #mixed_precision.set_policy(policy)
            opt = tf.keras.optimizers.SGD(lr=0.001, momentum=0.9)
            settingModel.compile(loss=args.loss, optimizer=opt, metrics=[tf.keras.metrics.TopKCategoricalAccuracy(), 'accuracy'])

    elif args.platform=='pytorch' :
        pass
        
        GPU_NUM = args.gpu # 원하는 GPU 번호 입력
        device = torch.device(f'cuda:{GPU_NUM}' if torch.cuda.is_available() else 'cpu')
        torch.cuda.set_device(device) # change allocation of current GPU
        
    else : print("Unknown platform!")
    return

class CustomHistory(callbacks.Callback) :
    def init(self):
        self.epochN = 0
        self.firstTime = time.time()
        self.timeHistory = {0 : self.firstTime}
        self.sumTime = 0
        self.stepSumTime = 0
        self.averageStepTime = 0
        self.averageTime = 0

    def on_epoch_begin(self, batch, logTuple = {}) :
        self.startTime = time.time()
        self.stepN = 0
        self.stepTotalTime = 0

    def on_epoch_end(self, batch, logTuple = {}) : 
        self.epochN += 1
        self.thisTime = time.time() - self.startTime
        self.sumTime += self.thisTime
        self.timeHistory[self.epochN] = self.thisTime
        if self.stepN != 0 :
            stepAverageTime = self.stepTotalTime/self.stepN
            self.stepSumTime += stepAverageTime
            print()
            print(" mean step time :", stepAverageTime)
            log.write(" mean step time : %10.5f\n" %stepAverageTime)
            print(" one epoch time :", self.thisTime)
            log.write(" one epoch time : %10.5f\n" %self.thisTime)
    
    def on_batch_begin(self, batch, logs=None):
        self.stepStartTime = time.time()
        #print()
        #print("one step begin")

    def on_batch_end(self, batch, logs=None):
        self.stepEndTime = time.time()
        self.stepTotalTime += self.stepEndTime - self.stepStartTime
        self.stepN += 1
        #print("one step end")
    
    def printAverage(self) :
        if self.epochN != 0 :
            self.averageTime = self.sumTime/self.epochN
            self.averageStepTime = self.stepSumTime/self.epochN
            print("Average step time :", self.averageStepTime)
            log.write("Average step time : %10.5f\n" %self.averageStepTime)
            print("Average epoch time :", self.averageTime)
            log.write("Average epoch time : %10.5f\n" %self.averageTime)
        else :
            print("epoch number is 0")

'''
# calculate function will be in train function so it can measure deep learning speed(instance per epoch)
def calculate():
    if args.platform=='tensorflow':

    elif args.platform=='pytorch' :

    else : print("Unknown platform!")
    return

# training function
def train(trainModel, train, validation):
    if args.platform=='tensorflow':
        customHistory = CustomHistory()
        customHistory.init()
        trainModel.fit(train, epochs=args.epochs, batch_size=args.batch_size,
                       validation_data=validation, validation_steps=args.validations, callbacks=[customHistory])
    
    elif args.platform=='pytorch' :
        for(args.epochs){

        }
    
    #else : print("Unknown platform!")
    return
'''
def accuracy(output, target, topk=(1,)):
    """Computes the accuracy over the k top predictions for the specified values of k"""
    with torch.no_grad():
        maxk = max(topk)
        #batch_size = target.size(0)

        _, pred = output.topk(maxk, 1, True, True)
        pred = pred.t()
        correct = pred.eq(target.view(1, -1).expand_as(pred))

        res = []
        for k in topk:
            correct_k = correct[:k].view(-1).float().sum(0, keepdim=True)
            res.append(correct_k.mul_(100.0 / args.batch_size))
        return res

class AverageMeter(object):
    """Computes and stores the average and current value"""
    def __init__(self, name, fmt=':f'):
        self.name = name
        self.fmt = fmt
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count

    def __str__(self):
        fmtstr = '{name} {val' + self.fmt + '} ({avg' + self.fmt + '})'
        return fmtstr.format(**self.__dict__)

str_gpus = ""
devices = []

if __name__ == "__main__":
    total_time_start = time.time()

    for gpu in args.gpus:
        if len(str_gpus) != 0 :
            str_gpus = str_gpus + ','
        str_gpus = str_gpus + str(gpu)
        devices.append("/gpu:" + str(gpu))
    os.environ["CUDA_VISIBLE_DEVICES"]=str_gpus

    config = ConfigProto()
    config.gpu_options.per_process_gpu_memory_fraction = args.fraction
    if args.grow : config.gpu_options.allow_growth = True
    else : config.gpu_options.allow_growth = False
    session = InteractiveSession(config=config)
    tf1.keras.backend.set_session(session)
    tf1.keras.backend.set_floatx(args.precision)

    filename = args.profiling+"/profile-"+args.platform+"-"+args.model+args.layer+".txt"
    log = open(filename,'a')
    log.write("This process's ID is %d\n" %os.getpid())
    main()
    total_time_end = time.time()

    total_time = total_time_end - total_time_start
    log.write("\ntotal time is %10.5f\n\n" %total_time);

    log.close()