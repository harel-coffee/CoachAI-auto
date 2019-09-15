import pandas as pd
import numpy as np
import math

def find_index(data, target):
	for idx in range(len(data)):
		if data[idx] == target:
			return idx

def get_hitting_pos(set_info, skeleton_info, top_is_Taiwan):
	hitting_pos = []
	for idx in range(len(set_info['frame_num'])):
		skeleton_idx = find_index(skeleton_info['frame'], set_info['frame_num'][idx])
		pos = []
		
		if skeleton_idx == None:
				pos.append('')
				pos.append('')
				pos.append('')
				pos.append('')
		else:
			if top_is_Taiwan:
				if set_info['player'][idx] == 'A':
					pos.append(skeleton_info['top_right_x'][skeleton_idx])
					pos.append(skeleton_info['top_right_y'][skeleton_idx])
					pos.append(skeleton_info['top_left_x'][skeleton_idx])
					pos.append(skeleton_info['top_left_y'][skeleton_idx])
				else:
					pos.append(skeleton_info['bot_right_x'][skeleton_idx])
					pos.append(skeleton_info['bot_right_y'][skeleton_idx])
					pos.append(skeleton_info['bot_left_x'][skeleton_idx])
					pos.append(skeleton_info['bot_left_y'][skeleton_idx])
			else:
				if set_info['player'][idx] == 'A':
					pos.append(skeleton_info['bot_right_x'][skeleton_idx])
					pos.append(skeleton_info['bot_right_y'][skeleton_idx])
					pos.append(skeleton_info['bot_left_x'][skeleton_idx])
					pos.append(skeleton_info['bot_left_y'][skeleton_idx])
				else:
					pos.append(skeleton_info['top_right_x'][skeleton_idx])
					pos.append(skeleton_info['top_right_y'][skeleton_idx])
					pos.append(skeleton_info['top_left_x'][skeleton_idx])
					pos.append(skeleton_info['top_left_y'][skeleton_idx])

		hitting_pos.append(pos)
	return hitting_pos

def Merge(set_num, total_set, setinfo, skeleton_file, top_is_Taiwan, savename):
	set_info = pd.read_csv(setinfo)
	skeleton_info = pd.read_csv(skeleton_file)
	
	right_delta_x = []
	right_delta_y = []
	left_delta_x = []
	left_delta_y = []

	right_x_speed = []
	right_y_speed = []
	left_x_speed = []
	left_y_speed = []
	
	right_speed = []
	left_speed = []

	hitting_pos = []

	if set_num != total_set:
		hitting_pos = np.array(get_hitting_pos(set_info, skeleton_info, top_is_Taiwan))
	else:
		first = pd.DataFrame([])
		second = pd.DataFrame([])
		for i in range(len(set_info['roundscore_A'])):
			if int(set_info['roundscore_A'][i]) == 11 or int(set_info['roundscore_B'][i]) == 11:
				first = set_info[:][:i]
				second = set_info[:][i:]
				break;
		# fix index
		second = second.reset_index(drop = True)
		first_part = get_hitting_pos(first, skeleton_info, top_is_Taiwan)
		top_is_Taiwan = not top_is_Taiwan
		second_part = get_hitting_pos(second, skeleton_info, top_is_Taiwan)

		hitting_pos = np.array(first_part+second_part)

	for i in range(len(hitting_pos)-1):
		if hitting_pos[i, 0] != '' and hitting_pos[i+1, 0] != '':
			right_delta_x.append(((float(hitting_pos[i+1, 0])-float(hitting_pos[i, 0]))%10)*10)
		if hitting_pos[i, 1] != '' and hitting_pos[i+1, 1] != '':
			right_delta_y.append(((float(hitting_pos[i+1, 1])-float(hitting_pos[i, 1]))%10)*10)
		if hitting_pos[i, 2] != '' and hitting_pos[i+1, 2] != '':
			left_delta_x.append(((float(hitting_pos[i+1, 2])-float(hitting_pos[i, 2]))%10)*10)
		if hitting_pos[i, 3] != '' and hitting_pos[i+1, 3] != '':
			left_delta_y.append(((float(hitting_pos[i+1, 3])-float(hitting_pos[i, 3]))%10)*10)

		if hitting_pos[i, 0] != '' and hitting_pos[i+1, 0] != '' and hitting_pos[i, 1] != '' and hitting_pos[i+1, 1] != '':
			sec_per_frame = 0.04
			x = float(hitting_pos[i+1, 0])-float(hitting_pos[i, 0])
			y = float(hitting_pos[i+1, 1])-float(hitting_pos[i, 1])
			right_x_speed.append((x/100)/sec_per_frame)
			right_y_speed.append((y/100)/sec_per_frame)
			right_speed.append((math.sqrt(x*x+y*y)/100)/sec_per_frame)

		if hitting_pos[i, 2] != '' and hitting_pos[i+1, 2] != '' and hitting_pos[i, 3] != '' and hitting_pos[i+1, 3] != '':
			sec_per_frame = 0.04
			x = float(hitting_pos[i+1, 2])-float(hitting_pos[i, 2])
			y = float(hitting_pos[i+1, 3])-float(hitting_pos[i, 3])
			left_x_speed.append((x/100)/sec_per_frame)
			left_y_speed.append((y/100)/sec_per_frame)
			left_speed.append((math.sqrt(x*x+y*y)/100)/sec_per_frame)

	set_info['now_right_x'] = list(hitting_pos[:, 0])
	set_info['now_right_y'] = list(hitting_pos[:, 1])

	set_info['now_left_x'] = list(hitting_pos[:, 2])
	set_info['now_left_y'] = list(hitting_pos[:, 3])

	set_info['next_right_x'] = pd.Series(list(hitting_pos[1:, 0]))
	set_info['next_right_y'] = pd.Series(list(hitting_pos[1:, 1]))

	set_info['next_left_x'] = pd.Series(list(hitting_pos[1:, 2]))
	set_info['next_left_y'] = pd.Series(list(hitting_pos[1:, 3]))

	set_info['right_delta_x'] = pd.Series(right_delta_x)
	set_info['right_delta_y'] = pd.Series(right_delta_y)

	set_info['left_delta_x'] = pd.Series(left_delta_x)
	set_info['left_delta_y'] = pd.Series(left_delta_y)

	set_info['right_x_speed'] = pd.Series(right_x_speed)
	set_info['right_y_speed'] = pd.Series(right_y_speed)
	#set_info['right_speed'] = pd.Series(right_speed)

	set_info['left_x_speed'] = pd.Series(left_x_speed)
	set_info['left_y_speed'] = pd.Series(left_y_speed)
	#set_info['left_speed'] = pd.Series(left_speed)
	set_info.to_csv(savename, index=False, encoding = 'utf-8')

def run(set_num, total_set, top_is_Taiwan):
	Merge(set_num, total_set, '../data/set'+str(set_num)+'.csv', '../data/set'+str(set_num)+'_skeleton.csv', top_is_Taiwan, '../data/set'+str(set_num)+'_with_skeleton.csv')

def exec(number_of_sets):
	top_Taiwan = True
	for i in range(number_of_sets):
		run(i+1, number_of_sets,top_Taiwan)
		top_Taiwan = not top_Taiwan

exec(3)