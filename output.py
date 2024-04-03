from GlobalVar import InterviewTimeList, InterviewerList, IntervieweeList
import pandas as pd
from datetime import datetime
def outputInterviewerAndStaff():
    df = pd.DataFrame(columns=['日期','时间段','姓名', '身份','地点'])
    for x in InterviewTimeList:
        interviewers = []
        # 添加当前时间段的面试官
        for y in InterviewerList:
            pos = ''
            for z in y.interview_time:
                if z.interviewTime == x.datetime_str:
                    pos = z.position
                    break
            if pos != '':
                interviewers.append([y.name, pos])
        interviewers = sorted(interviewers,key=lambda x: x[1]) #按教室排序
        for y in interviewers:
            date = x.datetime[0].strftime("%m.%d")
            time_slot = x.datetime[0].strftime("%H") + '-' + x.datetime[1].strftime("%H")
            new_record = {
                '日期': date,
                '时间段': time_slot,
                '姓名': y[0],
                '身份':'面试官',
                '地点': y[1]
            }
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
        # 添加时间段的场务
        for y in InterviewerList:
            for z in y.staff_time:
                if z == x.datetime_str:
                    date = x.datetime[0].strftime("%m.%d")
                    time_slot = x.datetime[0].strftime("%H") + '-' + x.datetime[1].strftime("%H")
                    new_record = {
                        '日期': date,
                        '时间段': time_slot,
                        '姓名': y.name,
                        '身份': '场务',
                        '地点': x.staff_position
                    }
                    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
        
    df.to_excel(r'result\面试官安排.xlsx', index=False)

if __name__ == "__main__":
    outputInterviewerAndStaff()