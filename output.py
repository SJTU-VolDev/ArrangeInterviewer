from GlobalVar import InterviewTimeList, InterviewerList, IntervieweeList
import pandas as pd
from datetime import datetime
def outputInterviewerAndStaff():
    df = pd.DataFrame(columns=['日期','时间段','面试官', '面试地点'])
    for x in InterviewTimeList:
        interviewers = []
        for y in InterviewerList:
            pos = ''
            for z in y.interview_time:
                if z.interviewTime == x.datetime_str:
                    pos = z.position
                    break
            if pos != '':
                interviewers.append([y.name, pos])
        interviewers = sorted(interviewers,key=lambda x: x[1])
        for y in interviewers:
            date = x.datetime[0].strftime("%m.%d")
            time_slot = x.datetime[0].strftime("%H") + '-' + x.datetime[1].strftime("%H")
            new_record = {'日期': date,'时间段': time_slot, '面试官': y[0], '面试地点': y[1]}
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    df.to_excel(r'result\面试官安排.xlsx', index=False)

if __name__ == "__main__":
    outputInterviewerAndStaff()