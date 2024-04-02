import networkx as nx
import json
from GlobalVar import InterviewTimeList, InterviewerList, IntervieweeList
from collections import Counter
from datetime import datetime
from model import InterviewTime, Interviewer, Interviewee, Interviewer_interviewtime

def checkTimeConflict(interviewer, t):
    '''
    检查面试官是否有时间冲突
    '''
    #time_format = "%Y-%m-%d %H:%M:%S"
    #begin = datetime.strptime(time.split('-')[0],time_format)
    #end = datetime.strptime(time.split('-')[1],time_format)
    for x in interviewer.available_time:
        if x[0] <= t[0] and x[1] >= t[1]:
            return True
    return False
# def findDupilicateAndCount(lst):
#     '''
#     找到列表中的重复元素并计数
#     '''
#     # 使用字典来计数相同的datetime字段
#     datetime_count = {}

#     # 遍历列表中的每个InterviewTime对象
#     for interview in lst:
#         datetime_key = interview.datetime_str
#         # 如果这个datetime字段已经存在于字典中，增加计数
#         if datetime_key in datetime_count:
#             datetime_count[datetime_key] += 1
#         else:
#             # 否则，初始化计数为1
#             datetime_count[datetime_key] = 1
#     return datetime_count
def checkStaffTimeConflict(interviewer, t):
    if len(interviewer.interview_time) > 0:
        for y in interviewer.interview_time:
            time_format = "%Y.%m.%d %H:%M:%S"
            begin = datetime.strptime(y.interviewTime.split('-')[0],time_format)
            end = datetime.strptime(y.interviewTime.split('-')[1],time_format)
            if begin >= t[0] and end <= t[1]:
                return False
    for x in interviewer.staff_available_time:
        if x[0] <= t[0] and x[1] >= t[1]:
            return True
    return False
def arrangeInterviewer():
    '''
    为面试官安排面试时段
    '''
    with open(r'data\config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
    G = nx.DiGraph()
    source = "source"
    sink = "sink"
    #counter = findDupilicateAndCount(InterviewTimeList)

    for x in InterviewerList:
        G.add_edge(source, x.name, capacity=int(config['面试官场次上限'])) #限制面试官的场次数
        for t in InterviewTimeList:
            G.add_edge(t.datetime_str,sink,capacity=len(t.positions)*int(config['教室面试官上限'])) #限制时间段的面试官数
            if checkTimeConflict(x, t.datetime):
                G.add_edge(x.name,t.datetime_str,capacity=1) #面试官有空则可以排入

    
    flow_value,flowResult = nx.maximum_flow(G, source, sink)#最大流算法
    #print(flowResult)
    to_add = {} #每个时间段有多少面试官可供分配
    for u,v in G.edges():
            #print(u,v,flowResult[u][v])
            if u != source and v != sink and flowResult[u][v] == 1:
                interviewer = [x for x in InterviewerList if x.name == u][0]
                # interviewer.interview_time.append(v)
                if v in to_add:
                    to_add[v].append(interviewer)
                else:
                    to_add[v] = [interviewer]
    #为面试官分配教室
    for t, interviewers in to_add.items():
        #print(t, interviewers)
        interviewtime = [x for x in InterviewTimeList if x.datetime_str == t][0]
        positions = interviewtime.positions
        #面试官和时间地点一一配对
        for i in range(len(interviewers)):
            interviewer = interviewers[i]
            position = positions[i % len(positions)]
            interviewer.interview_time.append(Interviewer_interviewtime(interviewtime.datetime_str, position))

    
    #输出结果
    # for x in InterviewerList:
    #     print(x.name)
    #     for y in x.interview_time:
    #         print(y.interviewTime, y.position)
    #     print()
def arrangeStaff():
    '''
    为场务安排时间段
    '''
    with open(r'data\config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
    G = nx.DiGraph()
    source = "source"
    sink = "sink"
    for x in InterviewerList:
        if len(x.interview_time) >= int(config['面试官场次上限']):
            continue
        G.add_edge(source, x.name, capacity=int(config['面试官场次上限']) - len(x.interview_time)) #限制场务的场次数
        for t in InterviewTimeList:
            G.add_edge(t.datetime_str,sink,capacity=int(config['单场场务人数'])) #限制时间段的场务数
            if checkStaffTimeConflict(x, t.datetime):
                G.add_edge(x.name,t.datetime_str,capacity=1) #场务有空则可以排入
    
    flow_value,flowResult = nx.maximum_flow(G, source, sink)#最大流算法
    #print(flowResult)
    to_add = {} #每个时间段有多少场务可供分配
    for u,v in G.edges():
            #print(u,v,flowResult[u][v])
            if u != source and v != sink and flowResult[u][v] == 1:
                interviewer = [x for x in InterviewerList if x.name == u][0]
                # interviewer.interview_time.append(v)
                if v in to_add:
                    to_add[v].append(interviewer)
                else:
                    to_add[v] = [interviewer]
    for t, interviewers in to_add.items():
        #print(t, interviewers)
        interviewtime = [x for x in InterviewTimeList if x.datetime_str == t][0]
        for i in range(len(interviewers)):
            interviewer = interviewers[i]
            interviewer.staff_time.append(interviewtime.datetime_str)

def arrangeInterviewerAndStaff():
    '''
    为面试官和场务安排时间段
    '''
    arrangeInterviewer()
    arrangeStaff()
    #输出结果
    # for x in InterviewerList:
    #     print(x.name)
    #     print("面试时间段：")
    #     for y in x.interview_time:
    #         print(y.interviewTime, y.position)
    #     print("场务时间段：")
    #     print(x.staff_time)
            


            


        

            

