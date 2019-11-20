import cv2
import numpy as np
from operator import itemgetter
import itertools
np.set_printoptions(precision=5, suppress=True)

def readImage(filename):
    img = cv2.imread(filename)
    print("img size = {}".format(np.shape(img)))
    #detect all white pixels
    img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    ret, img_thresh = cv2.threshold(img_gray, 220, 255, cv2.THRESH_BINARY)

    return img, img_thresh, img_gray

#### USING GRAY #####
#eliminate phase 1
def detectWhitepixel(img_thresh):
    taw = 8
    sigma_l = 220
    sigma_d = 15
    global max_row, max_col
    max_row = np.shape(img_thresh)[0]             #1080, y
    max_col = np.shape(img_thresh)[1]             #1920, x
    img_candidate = img_thresh.copy()

    for row in range(max_row):
        for col in range(max_col):
            candidate_flag = 1
            for taw_idx in range(1,taw+1):
                if row - taw_idx < 0 or row + taw_idx >= max_row or col - taw_idx < 0 or col + taw_idx >= max_col:
                    pass
                else:
                    if img_thresh[row][col] >= sigma_l and img_thresh[row][col] - img_thresh[row - taw_idx][col] > sigma_d and img_thresh[row][col] - img_thresh[row + taw_idx][col] > sigma_d: 
                        candidate_flag = 1
                    elif img_thresh[row][col] >= sigma_l and img_thresh[row][col] - img_thresh[row][col - taw_idx] > sigma_d and img_thresh[row][col] - img_thresh[row][col + taw_idx] > sigma_d:                       
                        candidate_flag = 1
                    else:
                        candidate_flag = 0
            
            if candidate_flag == 0:
                img_candidate[row][col] = 0

    return img_candidate

    # # eliminate phase 2 (not used yet)
    # # 1,0 : x direction gradient
    # sobelx = cv2.Sobel(img,cv2.CV_64F,1,0,ksize=5)
    # # 0,1 : y direction gradient
    # sobely = cv2.Sobel(img,cv2.CV_64F,0,1,ksize=5)

# Court line candidate dectector
def detectCourtline(img_candidate):
    #cv_pi/180
    lines = cv2.HoughLines(img_candidate,1,np.pi/180,200)
    print(np.shape(lines))

    # Classify horizon and vertical (pi/2-theta < 25 => horizontal)
    horizontal_line = []
    vertical_line = []
    angle_threshold = 25
    print("threshold = {}".format(angle_threshold/180*np.pi))

    for i in range(np.shape(lines)[0]):
        if float(abs(np.pi/2-lines[i][0][1])) <= float(angle_threshold/180*np.pi) :
            horizontal_line.append([lines[i][0][0],lines[i][0][1]])
        else:
            vertical_line.append([lines[i][0][0],lines[i][0][1]])

    # convert rho theta to slope and bias. Sort horizontal and vertical lines
    horizontal_rho2line =[]
    vertical_rho2line =[]
    given_y = max_row/2
    given_x = max_col/2

    for line in horizontal_line:
        rho = line[0]
        theta = line[1]
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        x1 = int(x0 + 1e4*(-b))
        y1 = int(y0 + 1e4*(a))
        x2 = int(x0 - 1e4*(-b))
        y2 = int(y0 - 1e4*(a))
        
        if x1 == x2:
            m = 1e9
        else:
            m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        distance_y = m * given_x + b
        horizontal_rho2line.append([m,b,distance_y])

    horizontal_line_sorted = sorted(horizontal_rho2line,key=itemgetter(2))

    for line in vertical_line:
        rho = line[0]
        theta = line[1]
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        x1 = int(x0 + 1e4*(-b))
        y1 = int(y0 + 1e4*(a))
        x2 = int(x0 - 1e4*(-b))
        y2 = int(y0 - 1e4*(a))

        if x1 == x2:
            m = 1e9
        else:
            m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        distance_x = (given_y - b) / m

        vertical_rho2line.append([m,b,distance_x])

    vertical_line_sorted = sorted(vertical_rho2line,key=itemgetter(2))

    print("sorted horizontal line = {}".format(np.shape(horizontal_line_sorted)))
    print("sorted vertical line = {}".format(np.shape(vertical_line_sorted)))

    # Line parameter refinement
    eliminate_flag = [0 for _ in range(len(horizontal_line_sorted))]
    distance_threshold = 10
    for line_first in range(len(horizontal_line_sorted)):
        if eliminate_flag[line_first] == 1:
            continue
        for line_second in range(line_first+1, len(horizontal_line_sorted)):
            if eliminate_flag[line_second] == 1:
                continue
            if horizontal_line_sorted[line_second][2] - horizontal_line_sorted[line_first][2] <= distance_threshold:
                eliminate_flag[line_second] = 1

    horizontal_line_eliminate = []
    for eliminate_idx in range(len(eliminate_flag)):
        if eliminate_flag[eliminate_idx] == 0:
            horizontal_line_eliminate.append(horizontal_line_sorted[eliminate_idx])

    eliminate_flag = [0 for _ in range(len(vertical_line_sorted))]
    for line_first in range(len(vertical_line_sorted)):
        if eliminate_flag[line_first] == 1:
            continue
        for line_second in range(line_first+1, len(vertical_line_sorted)):
            if eliminate_flag[line_second] == 1:
                continue
            if vertical_line_sorted[line_second][2] - vertical_line_sorted[line_first][2] <= distance_threshold:
                eliminate_flag[line_second] = 1

    vertical_line_eliminate = []
    for eliminate_idx in range(len(eliminate_flag)):
        if eliminate_flag[eliminate_idx] == 0:
            vertical_line_eliminate.append(vertical_line_sorted[eliminate_idx])

    print("eliminate horizontal line = {}".format(np.shape(horizontal_line_eliminate)))
    print("eliminate vertical line = {}".format(np.shape(vertical_line_eliminate)))

    return horizontal_line_sorted, vertical_line_sorted, horizontal_line_eliminate, vertical_line_eliminate

def computeScore(model_project, img_candidate):
    score = 0
    check_threshold = 2

    for project_coordinate in model_project[0]:
        flag = 0
        project_x = int(round(project_coordinate[0]))
        project_y = int(round(project_coordinate[1]))
        # print("now score = {}".format(score))
        
        if project_x < 0 or project_x >= max_col or project_y < 0 or project_y >= max_row:
            score -= 0
            continue
        for threshold_row in range(-check_threshold, check_threshold+1):
            for threshold_col in range(-check_threshold, check_threshold+1):
                if project_x + threshold_col < 0 or project_x + threshold_col >= max_col or project_y + threshold_row < 0 or project_y + threshold_row >= max_row:
                    continue
                if img_candidate[project_y + threshold_row][project_x + threshold_col] == 255:
                    flag = 1
        if flag == 1:
            score += 1
        else:
            score -= 0.5
    return score

def computeScore_debug(model_project, img_candidate):
    score = 0
    check_threshold = 2
    print("project = {}".format(model_project[0]))
    print("max col = {}".format(max_col))
    print("max row = {}".format(max_row))
    for project_coordinate in model_project[0]:
        flag = 0
        print("now score = {}".format(score))
        project_x = int(round(project_coordinate[0]))
        project_y = int(round(project_coordinate[1]))
        
        if project_x < 0 or project_x >= max_col or project_y < 0 or project_y >= max_row:
            score -= 0
            continue
        for threshold_row in range(-check_threshold, check_threshold+1):
            for threshold_col in range(-check_threshold, check_threshold+1):
                if project_x + threshold_col < 0 or project_x + threshold_col >= max_col or project_y + threshold_row < 0 or project_y + threshold_row >= max_row:
                    continue
                if img_candidate[project_y + threshold_row][project_x + threshold_col] == 255:
                    flag = 1
        if flag == 1:
            print("img candidate pixel add = {}".format(img_candidate[project_y][project_x]))
            score += 1
        else:
            print("img candidate pixel minus = {}".format(img_candidate[project_y][project_x]))
            score -= 0.5

def rejectTest(H):
    f_square = -1 * (H[0][0] * H[0][1] + H[1][0] * H[1][1]) / (H[2][0] * H[2][1])
    Beta_square = ((H[0][1] ** 2) + (H[1][1] ** 2) + f_square * (H[2][1] ** 2)) / ((H[0][0] ** 2) + (H[1][0] ** 2) + (f_square * (H[2][0] ** 2)))
    
    if Beta_square < (0.5 ** 2) or Beta_square > (2 ** 2):
        return False
    else:
        return True

def calculatehomographycandidate(horizontal_line_eliminate, vertical_line_eliminate, model_court_horizontal, model_court_vertical, court_all_points, img_candidate):
    model_court_combination = []
    for horizontal_idx in itertools.combinations(model_court_horizontal,2):
        for vertical_idx in itertools.combinations(model_court_vertical,2):
            model_court_combination.append([horizontal_idx, vertical_idx])

    # print(np.shape(model_court_combination))
    # print(model_court_combination)
    best_score = -1000
    best_homography = []
    best_court_model = []
    best_h1 = []
    best_h2 = []
    best_v1 = []
    best_v2 = []
    for horizontal_idx in itertools.combinations(horizontal_line_eliminate,2):
        for vertical_idx in itertools.combinations(vertical_line_eliminate,2):
            h1 = horizontal_idx[0]
            h2 = horizontal_idx[1]
            v1 = vertical_idx[0]
            v2 = vertical_idx[1]
            candidate_point1 = np.linalg.solve([[h2[0],-1], [v2[0],-1]], [-h2[1], -v2[1]])
            candidate_point2 = np.linalg.solve([[h1[0],-1], [v2[0],-1]], [-h1[1], -v2[1]])
            candidate_point3 = np.linalg.solve([[h2[0],-1], [v1[0],-1]], [-h2[1], -v1[1]])
            candidate_point4 = np.linalg.solve([[h1[0],-1], [v1[0],-1]], [-h1[1], -v1[1]])
            candidate_bunch = np.array([candidate_point1, candidate_point2, candidate_point3, candidate_point4], dtype="float32")

            for model_detail in model_court_combination:
                court_point1 = [model_detail[0][0], model_detail[1][0]]
                court_point2 = [model_detail[0][0], model_detail[1][1]]
                court_point3 = [model_detail[0][1], model_detail[1][0]]
                court_point4 = [model_detail[0][1], model_detail[1][1]]
                court_bunch = np.array([court_point1, court_point2, court_point3, court_point4], dtype="float32")

                homography = cv2.getPerspectiveTransform(court_bunch, candidate_bunch)
                reject_flag = rejectTest(homography)
                if reject_flag == False:
                    continue
                
                model_project = cv2.perspectiveTransform(court_all_points, homography)
                score = computeScore(model_project, img_candidate)
                
                #calculate score
                if score > best_score:
                    best_score = score
                    best_homography = homography.copy()
                    best_h1 = h1.copy()
                    best_h2 = h2.copy()
                    best_v1 = v1.copy()
                    best_v2 = v2.copy()
                    best_court_model = court_bunch.copy()
                    # computeScore_debug(model_project, img_candidate)
                    # print("best score = {}".format(best_score))
                    # print("court point = {}".format(court_bunch))
                    # print("best h1 = {}".format(h1))
                    # print("best h2 = {}".format(h2))
                    # print("best v1 = {}".format(v1))
                    # print("best v2 = {}".format(v2))
                    # print("best intersection = {}".format(candidate_bunch))
    
    return best_homography, [best_h1, best_h2, best_v1, best_v2], best_court_model

#output result
def outputImage(img, img_thresh, horizontal_line_sorted, vertical_line_sorted, horizontal_line_eliminate, vertical_line_eliminate, court_all_points, best_homography, best_line, best_court_model):
    img_output = img.copy()
    img_output[img_thresh == 255] = [0,255,255]
    cv2.imwrite('white_pixel_detection_all.jpg', img_output)

    img_output = img.copy()
    img_output[img_candidate == 255] = [0,255,255]
    cv2.imwrite('white_pixel_detection_phase1.jpg', img_output)

    img_output = img.copy()
    for line in horizontal_line_sorted:
        m = line[0]
        b = line[1]
        
        x1 = int(1e4)
        y1 = int(m * x1 + b)
        x2 = int(-1e4)
        y2 = int(m * x2 + b)
        cv2.line(img_output,(x1,y1),(x2,y2),(0,0,255),2)

    for line in vertical_line_sorted:
        m = line[0]
        b = line[1]
        
        x1 = int(1e4)
        y1 = int(m * x1 + b)
        x2 = int(-1e4)
        y2 = int(m * x2 + b)
        cv2.line(img_output,(x1,y1),(x2,y2),(0,255,255),2)
    cv2.imwrite('court_line_detection_phase1.jpg', img_output)

    img_output = img.copy()
    for line in horizontal_line_eliminate:
        m = line[0]
        b = line[1]
        
        x1 = int(1e4)
        y1 = int(m * x1 + b)
        x2 = int(-1e4)
        y2 = int(m * x2 + b)
        cv2.line(img_output,(x1,y1),(x2,y2),(0,0,255),2)

    for line in vertical_line_eliminate:
        m = line[0]
        b = line[1]
        
        x1 = int(1e4)
        y1 = int(m * x1 + b)
        x2 = int(-1e4)
        y2 = int(m * x2 + b)
        cv2.line(img_output,(x1,y1),(x2,y2),(0,255,255),2)
    cv2.imwrite('court_line_detection_phase2.jpg', img_output)

    img_output = img.copy()
    # print("best homography = {}".format(best_homography))
    # print("model original point = {}".format(court_all_points))
    
    for line in best_line:
        m = line[0]
        b = line[1]
        
        x1 = int(1e4)
        y1 = int(m * x1 + b)
        x2 = int(-1e4)
        y2 = int(m * x2 + b)
        cv2.line(img_output,(x1,y1),(x2,y2),(0,0,255),2)
    
    model_project = cv2.perspectiveTransform(court_all_points, best_homography)
    for project_point in model_project[0]:
        cv2.circle(img_output, tuple(project_point), 2, (0,255,255), 5)
        
    # for best_court_point in best_court_model:
    #     print(tuple(best_court_point))
    cv2.imwrite('court_detection_result.jpg', img_output)

if __name__ == '__main__':
    model_court_horizontal = [0, 0.5, 3.05, 5.6, 6.1]
    model_court_vertical = [0, 0.76, 4.68, 8.68, 12.64, 13.40]
    court_all_points = [_ for _ in itertools.product(model_court_horizontal, model_court_vertical)]
    court_all_points = np.array([court_all_points], dtype="float32")

    filename = './original_chou.jpg'
    img, img_thresh, img_gray = readImage(filename)
    img_candidate = detectWhitepixel(img_thresh)
    horizontal_line_sorted, vertical_line_sorted, horizontal_line_eliminate, vertical_line_eliminate = detectCourtline(img_candidate)
    best_homography, best_line, best_court_model = calculatehomographycandidate(horizontal_line_eliminate, vertical_line_eliminate, model_court_horizontal, model_court_vertical, court_all_points, img_candidate)
    outputImage(img, img_thresh, horizontal_line_sorted, vertical_line_sorted, horizontal_line_eliminate, vertical_line_eliminate, court_all_points, best_homography, best_line, best_court_model)