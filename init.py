
from datetime import datetime, timedelta
from model import InterviewTime, Interviewer, Interviewee
from GlobalVar import InterviewTimeList, InterviewerList, IntervieweeList
import pandas as pd
import json

def splitTime():
    '''
    将面试时间段划分为单个面试时间
    '''
    with open(r'data\config.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
    with open(r'data\面试时间段.json', 'r', encoding='utf-8') as file:
        totTime = json.load(file)
    time_format = '%Y.%m.%d %H:%M'
    for x in totTime['面试时间段']:
        now = datetime.strptime(str(datetime.now().year) + "." + x['日期'] + " " + x['起始时间'], time_format)
        end = datetime.strptime(str(datetime.now().year) + "." + x['日期'] + " " + x['结束时间'], time_format)
        delta = timedelta(minutes=int(config['单场时间']))
        while now + delta <= end:
            now.strftime(time_format)
            InterviewTimeList.append(InterviewTime(now=now, end=now+delta, positions=x["地点"]))
            now += delta

    #for x in InterviewTimeList:
    #    print(x.datetime, x.position)


def inputInterviewee():
    '''
    读取面试者信息
    '''
    data = pd.read_excel(r'data\面试者信息.xlsx')
    for i in range(len(data)):
        interviewee = Interviewee(data["姓名"][i], data["学号"][i], data["电话"][i], data["邮箱"][i])
        IntervieweeList.append(interviewee)
    #for x in IntervieweeList:
    #   print(x.name, x.id, x.tel, x.email, x.jaccount)

def makeTimeFormat(t):
    '''
    将时间格式化为datatime格式
    '''
    #"11月10号周五18：00-20：00"
    year = str(datetime.now().year)
    date = t.split('周')[0]
    starttime = t.split('周')[1][1:].split('-')[0]
    endtime = t.split('周')[1][1:].split('-')[1]
    ta = datetime.strptime(year+'年'+date+' '+starttime, '%Y年%m月%d号 %H：%M')
    tb = datetime.strptime(year+'年'+date+' '+endtime, '%Y年%m月%d号 %H：%M')
    return [ta,tb]

    
def inputInterviewer():
    data = pd.read_excel(r'data\面试官信息.xlsx')
    for i in range(len(data)):
        interviewer = Interviewer(data["姓名"][i])
        time_slot = data["面试时间"][i].split('、')
        for t in time_slot:
            [ta,tb] = makeTimeFormat(t)
            interviewer.available_time.append([ta,tb])
        InterviewerList.append(interviewer)
    #for x in InterviewerList:
    #    print(x.name,x.available_time)
            
def init():
    splitTime()
    inputInterviewer()
    inputInterviewee()

if __name__ == '__main__':
    splitTime()
    inputInterviewer()
    inputInterviewee()
    
    print('done')
