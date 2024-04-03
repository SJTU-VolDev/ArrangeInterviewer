from datetime import datetime, timedelta
class InterviewTime:
    '''
    面试时间类
    存储一个面试时间段的日期、时间、地点、面试者信息、面试官信息
    '''
    datetime = [] #开始时间和结束时间,datetime格式
    datetime_str = "" #开始时间和结束时间,字符串格式
    positions = []
    staff_position = ''
    interviewers = []
    interviewees = []
    def __init__(self, now, end, positions, staff_position):
        self.datetime = [now, end]
        self.positions = positions
        self.datetime_str = now.strftime("%Y.%m.%d %H:%M:%S") + "-" + end.strftime("%Y.%m.%d %H:%M:%S")
        self.interviewers = []
        self.interviewees = []
        self.staff_position = staff_position

class Interviewee:
    '''
    面试者类
    存储一个面试者的姓名、学号、面试时间
    '''
    name = ''
    id = ''
    email = ''
    tel = ''
    jaccount = ''
    interview_time = ''
    def __init__(self, name, id, tel, email):
        self.name = name
        self.id = id
        self.tel = tel
        self.email = email
        self.jaccount = email.split('@')[0]
        self.interview_time = ''
   
        
class Interviewer_interviewtime:
    '''
    面试官和面试时间段的对应类
    存储一个面试时间段和一个面试地点的对应关系
    '''
    interviewTime = ''
    position = ''
    def __init__(self, interviewTime, position):
        self.interviewTime = interviewTime
        self.position = position

class Interviewer:
    '''
    面试官类
    存储一个面试官的姓名、有空时间、面试时间
    '''
    name = ''
    available_time = [] #面试官有空的时间段
    interview_time = []
    staff_available_time = [] #场务有空的时间段
    staff_time = [] #场务的时间段
    def __init__(self, name):
        self.name = name
        self.available_time = []
        self.interview_time = []
        self.staff_available_time = []
        self.staff_time = []