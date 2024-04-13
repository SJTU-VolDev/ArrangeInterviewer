from init import init, inputInterviewee
from model import InterviewTime, Interviewee, Interviewer
from methods import arrangeInterviewerAndStaff, arrangeInterviewee
from output import outputInterviewerAndStaff, outputInterviewee
import os
if __name__ == "__main__":
    
    if os.path.exists(os.path.join('result','面试官安排.xlsx')) == False:
        print("未检测到面试官安排表,正在生成面试官安排表")
        init()
        arrangeInterviewerAndStaff()
        outputInterviewerAndStaff()
        print("面试官安排表已生成")
    else:
        print("检测到面试官安排表,跳过生成步骤")
    print("正在生成面试者安排表")
    inputInterviewee()
    arrangeInterviewee()
    outputInterviewee()
    print("面试者安排表已生成")