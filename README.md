## Tasks

### General

- [x] to create an script which is pushing 1 mail for notify or summarization.
- [x] develop summarization function using gpt4o-mini
- [x] store summarization reulst in store DB 
- [x] develop notification fuction. 
- [x] store notification result into store DB
- [x] use sqlligt for sumamry storing as there is no need for 
- [x] add to main script init db function for fresh start

### notification
- [x] study human in the loop(HIL) threads an check pointers, define a working process for notifications to be treated. 
- [x] add notification as well to sqldb for statuses, rebuil work wiht DB, DB used for notification an tracking, checkpointers to do HIL.
- [x] add interuption after notification node.
- [x] notification_processor.py check for new triggers, load check point with current state. 
- [x] ISSUE: fix issue with empty check pointers - added last data 
- [ ] ISSUE: keep list of all check points for any run, as now we have - ValueError: No checkpointer set
- [ ] notification_processor.py update state according with human feedback, update reflection, resume execution.
- [ ] define which functions can be used for mails which were notified - calendar schedule, draft an answer, delete mail, forwared mail. 
- [ ] define reflection persitence and functionality, and UI to interact with it (TG, WEB).
- [ ] defein notification functionality, take data from DB by status, send to channel, update status. 

- [ ] write summary function which will take all summary details for certian period and send to channle, more detials... 
- [ ] working on reflection, reflection graph, take prompts from long term memory. UI to edit it.

- [ ] working on actions wiht mails, functional library, check in case it is possible to be done in bulk. 
- [ ] build statistics functions to draw as much insights as possible for assitant.
- [ ] add unit tests
- [ ] add an alarming on budget sepnt - try to use langfuse
- [ ] productualize tool, make pipes and deplyment scripts, more detials...



