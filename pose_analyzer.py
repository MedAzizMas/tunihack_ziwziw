import numpy as np
import data as data

class PoseAnalyzer:
    def __init__(self):
        self.data_list = data.AngleData

    def compare_right_arm(self, right_arm):
        tadasan = [y for x, y in list(self.data_list[0].items()) if type(y) == int]
        if right_arm <= tadasan[0]:
            acc = (right_arm/tadasan[0])*100
        else:
            acc = 0
            
        if abs(tadasan[0]-right_arm) <= 10:
            print("Your right arm is accurate")
        else:
            print("Your right arm is not accurate")
        return acc

    def compare_left_arm(self, left_arm):
        tadasan = [y for x, y in list(self.data_list[0].items()) if type(y) == int]
        if left_arm <= tadasan[1]:
            acc = (left_arm/tadasan[1])*100
        else:
            acc = 0
            
        if abs(tadasan[1]-left_arm) <= 10:
            print("Your left arm is accurate")
        else:
            print("Your left arm is not accurate , try again")
        return acc

    def compare_right_leg(self, right_leg):
        tadasan = [y for x, y in list(self.data_list[0].items()) if type(y) == int]
        if right_leg <= tadasan[2]:
            acc = (right_leg/tadasan[2])*100
        else:
            acc = 0

        if abs(tadasan[2]-right_leg) <= 10:
            print("Your right leg is accurate")
        else:
            print("Your right leg is not accurate, try again")
        return acc

    def compare_left_leg(self, left_leg):
        tadasan = [y for x, y in list(self.data_list[0].items()) if type(y) == int]
        if left_leg <= tadasan[3]:
            acc = (left_leg/tadasan[3])*100
        else:
            acc = 0

        if abs(tadasan[3]-left_leg and left_leg < tadasan[3]) <= 10:
            print("Your left leg is accurate")
        else:
            print("Your left leg is not accurate, try again")
        return acc

    def calculate_accuracy(self, arr):
        acc_array = np.array([])
        for j in range(0, len(arr)-1, 4):
            sum_acc = sum(arr[j:j+4])
            acc_array = np.append(acc_array, (sum_acc/4)/4)
        return acc_array
    def calculate_total_accuracy(self, right_arm_acc, left_arm_acc, right_leg_acc, left_leg_acc):
        # Only calculate if we have all measurements
        if all(x is not None for x in [right_arm_acc, left_arm_acc, right_leg_acc, left_leg_acc]):
            total_acc = (right_arm_acc + left_arm_acc + right_leg_acc + left_leg_acc) / 4
            return min(max(total_acc, 0), 100)  # Ensure result is between 0-100
        return 0