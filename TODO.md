# Login Flow Fix Progress

## Steps:
- [x] Create TODO.md
- [x] Edit app.py: Fix account query to use registration_id, check None or first_name NULL, fix url_for('cd')
- [x] Fix cd() bugs: reg_user indices, idinput → reg_id, contacts indices
- [ ] Test: Run `python app.py`, register new user, login → redirects to /complete_details
- [ ] Test incomplete account → complete_details
- [ ] Test complete account → dashboard
- [ ] attempt_completion

