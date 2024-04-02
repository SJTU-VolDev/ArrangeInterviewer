from init import init
from model import InterviewTime, Interviewee, Interviewer
from methods import arrangeInterviewerAndStaff
from output import outputInterviewerAndStaff
if __name__ == "__main__":
    init()
    arrangeInterviewerAndStaff()
    outputInterviewerAndStaff()
    print("Done.")