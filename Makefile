.PHONY: setup interviewer interviewee_1 interviewee_2

VENV := venv/bin/activate
REQS := requirements.txt

setup:
	@if [ ! -d "venv" ]; then python3 -m venv venv && . $(VENV) && pip install -r $(REQS); fi

interviewer: setup
	python3 schedule_manager.py

interviewee_1: setup
	python3 interviewee_scheduler.py

interviewee_2: setup
	python3 second_interview.py
