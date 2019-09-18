import csv
import pandas as pd
import numpy as np
import xgboost as xgb
import itertools
import functions

from sklearn.externals import joblib
from sklearn.metrics import *
from xgboost import plot_importance
import matplotlib.pyplot as plt

from functions import *

needed = ['now_right_x', 'now_right_y', 'now_left_x', 'now_left_y', 
		'next_right_x', 'next_right_y', 'next_left_x', 'next_left_y', 
		'right_delta_x', 'right_delta_y', 'left_delta_x', 'left_delta_y',
		'right_x_speed', 'right_y_speed','right_speed',
		'left_x_speed', 'left_y_speed', 'left_speed', 'hit_height', 'type', 'avg_ball_speed']

test_needed = ['now_right_x', 'now_right_y', 'now_left_x', 'now_left_y', 
		'next_right_x', 'next_right_y', 'next_left_x', 'next_left_y', 
		'right_delta_x', 'right_delta_y', 'left_delta_x', 'left_delta_y',
		'right_x_speed', 'right_y_speed','right_speed',
		'left_x_speed', 'left_y_speed', 'left_speed', 'avg_ball_speed']

def LoadData(filename, ball_height_predict):
	data = pd.read_csv(filename)
	ball_height = pd.read_csv(ball_height_predict)
	data = data[needed]
	data.dropna(inplace=True)
	data.reset_index(drop=True, inplace=True)
	data['Predict'] = ball_height['Predict']
	data = data[data.type != '未擊球']
	x_predict = data[test_needed+['Predict']]
	
	return x_predict

def plot_Confusion_Matrix(set_now, model_type, cm, groundtruth, grid_predictions, classes):
    plt.imshow(cm, cmap=plt.cm.Blues)
    plt.title('Confusion matrix')
    plt.colorbar()
    plt.xlabel('Actual Class')
    plt.ylabel('Predicted Class')
    plt.xticks(np.arange(len(classes)-1), classes)
    plt.yticks(np.arange(len(classes)-1), classes)

    for j, i in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        if i == j:
            plt.text(i+0.03, j+0.2, str(format(cm[j, i], 'd'))+'\n'+str( round(precision_score(groundtruth, grid_predictions, average=None)[i]*100,1))+'%', 
            color="white" if cm[j, i] > cm.max()/2. else "black", 
            horizontalalignment="center")
        else:
            plt.text(i, j, format(cm[j, i], 'd'), 
            color="white" if cm[j, i] > cm.max()/2. else "black", 
            horizontalalignment="center")

    plt.savefig('../data/img/'+str(model_type)+'_set'+str(set_now)+'_balltype_confusion_matrix.png')
    plt.close(0)

def plot_chart(set_now, model_type, model, groundtruth, grid_predictions, labels):
    # confusion matrix
    plot_Confusion_Matrix(set_now, model_type, confusion_matrix(groundtruth, grid_predictions), groundtruth, grid_predictions, labels)
    plt.clf()
    plt.close()

def XGBoost(filename, x_predict, xgboost_model_name, xgboost_outputname, set_now):
    data = pd.read_csv(filename)
    data = data[needed]
    data.dropna(inplace=True)
    data.reset_index(drop=True, inplace=True)
    data = data[data.type != '未擊球']

    label = [1, 2, 3, 4, 5, 6, 7, 8]
    type_to_num = {'cut': 1, 'drive': 2, 'lob': 3, 'long': 4, 'netplay': 5, 'rush': 6, 'smash': 7, 'error': 8}
    num_to_type = {1: 'cut', 2: 'drive', 3: 'lob', 4: 'long', 5: 'netplay', 6: 'rush', 7: 'smash', 8: 'error'}
    real_num = []
    real_eng = []
    predict_result_eng = []

    xgboost_model = joblib.load(xgboost_model_name)
    prediction = xgboost_model.predict(x_predict)

    for ball in data['type']:
    	real_eng.append(num_to_type[type_to_num[ball_type_convertion(ball)]])
    	real_num.append(type_to_num[ball_type_convertion(ball)])

    for ball in prediction:
    	predict_result_eng.append(num_to_type[ball])

    # output
    result = pd.DataFrame([])
    result['Real'] = real_num
    result['Predict'] = prediction
    
    result.to_csv(xgboost_outputname, index=None)

    # print precision and recall
    print("Accuracy: "+str(accuracy_score(real_num, prediction)))
    print("Precision: "+str(precision_score(real_num, prediction, labels = label, average=None)))
    print("Recall: "+str(recall_score(real_num, prediction, labels = label, average=None)))
    
    # plot result chart
    plot_chart(set_now, "XGB", xgboost_model, real_eng, predict_result_eng, list(type_to_num.keys()))

def Run(set_now, filename, svm_option, svm_model_name, svm_prediction_result_file, svm_outputname, xgboost_option, xgboost_model_name, xgboost_prediction_result_file, xgboost_outputname):
	
	if svm_option and svm_model_name != '':
		print("SVM predicting set"+str(set_now)+"...")
		x_predict = LoadData(filename, svm_prediction_result_file)
		SVM(filename, x_predict, svm_model_name, svm_outputname, set_now)
		print("SVM predict set"+str(set_now)+" done!")

	if xgboost_option and xgboost_model_name != '':
		print("XGBoost predicting set"+str(set_now)+"...")
		x_predict = LoadData(filename, xgboost_prediction_result_file)
		XGBoost(filename, x_predict, xgboost_model_name, xgboost_outputname, set_now)
		print("XGBoost predict set"+str(set_now)+" done!")

def exec(predict_set):
	for i in predict_set:
		Run(i ,'../data/set'+str(i)+'_with_skeleton.csv', False, '../model/SVM_balltype.joblib.dat', '../data/result/SVM_set'+str(i)+'_skeleton_out.csv', '../data/result/SVM_set'+str(i)+'_balltype_out.csv', True, '../model/XGB_balltype.joblib.dat', '../data/result/XGB_set'+str(i)+'_skeleton_out.csv', '../data/result/XGB_set'+str(i)+'_balltype_out.csv')

exec([1, 2, 3])	