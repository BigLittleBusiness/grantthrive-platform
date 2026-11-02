"""Approved GrantThrive Help & Guidance knowledge base.

This module is source-controlled so serving guidance has no runtime dependency on
the approval source document. Questions and answers are preserved verbatim as
plain text from the approved 1 November 2026 FAQ.
"""

COHORTS = [{'id': 'system_administrator',
  'label': 'System Administrator',
  'description': 'Platform-wide administration, council provisioning, registrations, system configuration and '
                 'protected form submissions.',
  'questions': [{'id': 'system_administrator-01',
                 'question': 'How do I sign in to the System Administration dashboard?',
                 'answer': 'Open the System Administration sign-in page and enter your authorised System Administrator '
                           'email address and password. Only accounts with the System Administrator role can use this '
                           'area. If MFA is enabled, enter the current code from your authenticator app.'},
                {'id': 'system_administrator-02',
                 'question': 'Why do I see “Access Denied” after signing in?',
                 'answer': 'The administration dashboard is restricted to System Administrator accounts. Sign out and '
                           'sign in with an authorised System Administrator account. If you believe your role needs to '
                           'change, contact Customer Service.'},
                {'id': 'system_administrator-03',
                 'question': 'What should I do if my email or password is not accepted?',
                 'answer': 'Check that you are using the correct System Administrator email address and current '
                           'password. Avoid repeated guesses: local sign-in is temporarily locked after five failed '
                           'attempts, and server-side rate limits also apply. Wait and try again if rate-limited; if '
                           'access still fails with the correct credentials, contact Customer Service.'},
                {'id': 'system_administrator-04',
                 'question': 'My account has been deactivated. Can I reactivate it myself?',
                 'answer': 'No. Another active System Administrator can restore an inactive account from System '
                           'Admins. If no active System Administrator is available, contact Customer Service.'},
                {'id': 'system_administrator-05',
                 'question': 'What do I do if my session expires or the dashboard logs me out?',
                 'answer': 'Sign in again. If a session token expires, becomes invalid, or the account is no longer '
                           'active, the console returns to the sign-in screen. Use Log out when you finish, especially '
                           'on a shared device.'},
                {'id': 'system_administrator-06',
                 'question': 'Can I have my email remembered on this device?',
                 'answer': 'Yes. Select Remember my email on this device on the sign-in page. This remembers only the '
                           'email address; you must still enter your password and any required authenticator code. Do '
                           'not use it on a shared or public device.'},
                {'id': 'system_administrator-07',
                 'question': 'How do I set up authenticator MFA for my administrator account?',
                 'answer': 'Open Settings, select Set up authenticator MFA, add the displayed setup key to your '
                           'authenticator app, then enter the current six-digit code and select Confirm and enable '
                           'MFA. Treat the setup key as you would a password.'},
                {'id': 'system_administrator-08',
                 'question': 'How do I turn off MFA?',
                 'answer': 'Open Settings, enter a current authenticator code, then select Disable MFA. A valid '
                           'current code is required. If you no longer have access to the authenticator app, contact '
                           'Customer Service.'},
                {'id': 'system_administrator-09',
                 'question': 'How can I reset a System Administrator password?',
                 'answer': 'In System Admins, select the account, choose Edit, and enter a new password. Leave the '
                           'password blank when changing only the name or email address. Administrator passwords must '
                           'be at least 12 characters and include uppercase and lowercase letters, a number, and a '
                           'special character. If no active System Administrator can make the change, contact Customer '
                           'Service.'},
                {'id': 'system_administrator-10',
                 'question': 'How do I get around the admin dashboard?',
                 'answer': 'Use the left navigation for Overview, Council Management, Council Registrations, Form '
                           'Submissions, System Admins, Pricing Management, SMS / Twilio, and Settings. You can '
                           'collapse the navigation, and Alerts returns to live action items on Overview.'},
                {'id': 'system_administrator-11',
                 'question': 'What does the Overview dashboard show?',
                 'answer': 'Overview shows current counts for active users, active councils, grant programs, and '
                           'submitted applications. It also lists pending council registrations, new public form '
                           'submissions, failed form notifications, and trials ending within seven days. Select '
                           'Refresh to reload the data.'},
                {'id': 'system_administrator-12',
                 'question': 'How do I review a pending council registration?',
                 'answer': 'Open Council Registrations and search by name, email, organisation, or requested '
                           'subdomain. Open the record, then select Approve to activate an eligible registration or '
                           'Reject to remove it. You can add a rejection reason for the registrant notification.'},
                {'id': 'system_administrator-13',
                 'question': 'What happens when I approve a council administrator registration?',
                 'answer': 'Approval activates the account. Where a Council Administrator registration has no existing '
                           'council, GrantThrive creates an active council tenant, links the administrator, and starts '
                           'a 14-day trial. The requested plan and billing cycle are retained; a welcome email may '
                           'then be sent.'},
                {'id': 'system_administrator-14',
                 'question': 'The requested council subdomain is taken. How can I approve the registration?',
                 'answer': 'In Council Registrations, select Edit next to the requested subdomain, enter a different '
                           'available identifier, save it, then approve the registration. The identifier must be 3–64 '
                           'characters, use lowercase letters, numbers, and hyphens only, cannot start or end with a '
                           'hyphen, and cannot use reserved names such as `app`, `admin`, or `support`.'},
                {'id': 'system_administrator-15',
                 'question': 'How do I create a new council tenant?',
                 'answer': 'Open Council Management and select Provision New Council. Enter the council name, tenant '
                           'identifier, state, and plan; add optional contact, website, branding, and LGA details as '
                           'needed; then select Provision Council. Council name and state are required, and the tenant '
                           'identifier must be unique and valid.'},
                {'id': 'system_administrator-16',
                 'question': 'Can I create a council and its first Council Administrator together?',
                 'answer': 'Yes. While provisioning a council, expand Provision a Council Admin User (optional) and '
                           'enter the person’s name, email address, and temporary password. The account is created as '
                           'a Council Administrator for that new council. Use a password of at least 10 characters '
                           'that meets the password-strength rules.'},
                {'id': 'system_administrator-17',
                 'question': 'How do I find or update an existing council?',
                 'answer': 'In Council Management, search by council name, tenant identifier, or LGA code, or filter '
                           'by state, plan, or active status. Select View, then Edit Profile to update plan, contact '
                           'details, website, logo URL, or brand colours. The current console does not provide a '
                           'tenant-identifier edit control; contact Customer Service if one is required.'},
                {'id': 'system_administrator-18',
                 'question': 'How do I add a user to a council?',
                 'answer': 'Open Council Management, select View for the council, open the Users tab, and choose '
                           'Provision User. Enter the person’s name, email, password, and role, then select Provision. '
                           'Available roles are Council Admin, Council Staff, and Community Member; the email cannot '
                           'already belong to an account.'},
                {'id': 'system_administrator-19',
                 'question': 'How do I deactivate a council, and what happens to its data?',
                 'answer': 'In Council Management, select Deactivate for the active council and confirm. The council '
                           'portal becomes inaccessible, while council data is retained as a soft deletion. There is '
                           'no restore control in the System Administrator console; contact Customer Service for an '
                           'action unavailable through the council controls.'},
                {'id': 'system_administrator-20',
                 'question': 'How do I add, edit, deactivate, or restore a System Administrator?',
                 'answer': 'Open System Admins to search and filter accounts, select Add System Admin, or use the '
                           'edit, deactivate, and restore controls. System Administrators have unrestricted platform '
                           'access, so assign this role only to authorised GrantThrive staff.'},
                {'id': 'system_administrator-21',
                 'question': 'Why can’t I deactivate my own System Administrator account or the last active '
                             'administrator?',
                 'answer': 'These are safeguards. You cannot deactivate your own account, and the platform must retain '
                           'at least one active System Administrator. Create another authorised System Administrator '
                           'before deactivating the departing account.'},
                {'id': 'system_administrator-22',
                 'question': 'How do I handle a contact enquiry or waitlist signup?',
                 'answer': 'Open Form Submissions, filter by status or form type, and select View to see protected '
                           'details. Set the status to New, In progress, or Resolved, add or update an internal note '
                           'if needed, and select Save changes. Keep notes concise and do not copy protected details '
                           'into unprotected channels.'},
                {'id': 'system_administrator-23',
                 'question': 'Who can see public contact and waitlist information?',
                 'answer': 'Only System Administrators can access the protected form-submission records and detailed '
                           'submissions. A failed notification does not remove a submission; open the protected record '
                           'in Form Submissions and handle it there.'},
                {'id': 'system_administrator-24',
                 'question': 'How do I change subscription pricing?',
                 'answer': 'Open Pricing Management, update the displayed plan name or pricing fields in whole '
                           'Australian dollars, select Save, review the changes, then select Apply Changes. Changes '
                           'update the public pricing page and apply to new sign-ups. Use Change History to review '
                           'recorded updates.'},
                {'id': 'system_administrator-25',
                 'question': 'Can I reset all pricing to the defaults?',
                 'answer': 'Yes. In Pricing Management, select Reset to Defaults and confirm. This restores editable '
                           'plans to the compiled default prices and updates the public pricing page. Use it only when '
                           'restoring the defined defaults is intended.'},
                {'id': 'system_administrator-26',
                 'question': 'How do I configure or test platform SMS?',
                 'answer': 'Open SMS / Twilio, enter the Account SID and Auth Token, then provide either a Messaging '
                           'Service SID or a Twilio From number. Save the configuration, use the global SMS switch as '
                           'needed, and enter a phone number in Send Test SMS to verify saved credentials. Councils '
                           'can manage their notification preferences but cannot manage shared platform credentials.'},
                {'id': 'system_administrator-27',
                 'question': 'What happens if I clear the central Twilio credentials or switch off global SMS?',
                 'answer': 'Turning off Global SMS Enable stops outbound SMS across the platform, regardless of '
                           'individual council preferences. Clearing all credentials removes the saved configuration '
                           'and disables SMS for every council. The console asks for confirmation; there is no undo '
                           'control.'},
                {'id': 'system_administrator-28',
                 'question': 'Can I turn on AI grant suggestions or use AI to make funding decisions?',
                 'answer': 'AI grant suggestions are advisory drafting support only. They are never applied '
                           'automatically and must be reviewed by council officers. AI must never approve, reject, '
                           'rank, allocate, or otherwise decide funding. The System Administrator Settings page does '
                           'not provide a live control to enable the AI pilot; contact Customer Service for an '
                           'approved deployment or configuration request.'},
                {'id': 'system_administrator-29',
                 'question': 'What should I tell a council about community voting results?',
                 'answer': 'Community voting is advisory and non-binding. It may inform council decision-making, but '
                           'it does not approve, reject, rank for funding, or allocate grants. Formal funding outcomes '
                           'remain the responsibility of council decision-makers.'},
                {'id': 'system_administrator-30',
                 'question': 'Can public grant-map locations include an applicant’s private address?',
                 'answer': 'No. A grant appears on the public map only when it is published, mapping is explicitly '
                           'enabled, a public location name and valid coordinates are supplied, and the council has '
                           'approved public display. Use a suburb, precinct, or facility location—not an applicant’s '
                           'private address or other private applicant location.'}]},
 {'id': 'council_administrator',
  'label': 'Council Administrator',
  'description': 'Council-owned grant programs, staff access, application decisions, communications, billing and '
                 'council settings.',
  'questions': [{'id': 'council_administrator-01',
                 'question': 'How do I sign in as a Council Administrator?',
                 'answer': 'Go to the GrantThrive portal sign-in page, enter your council email address and password, '
                           'then select Sign In. A successful sign-in opens the Council Administration Dashboard. '
                           'Check your connection and retry if the page reports a connection problem.'},
                {'id': 'council_administrator-02',
                 'question': 'Why does my account say it is awaiting approval or deny access?',
                 'answer': 'A pending account cannot sign in until activated; wait for the approval notification '
                           'before trying again. If you see Access denied, sign out and use the Council Administrator '
                           'account for the relevant council. If an account that should be active remains unavailable, '
                           'contact Customer Service.'},
                {'id': 'council_administrator-03',
                 'question': 'How is a new Council Administrator account set up?',
                 'answer': 'For a council’s first representative, choose Council during registration and provide an '
                           'official Australian `.gov.au` or New Zealand `.govt.nz` email, council details, position, '
                           'subdomain, and plan selection. The request is pending approval before sign-in. If an '
                           'administrator already exists for the organisation, contact the Council Administrator to be '
                           'added as council staff rather than registering another first administrator.'},
                {'id': 'council_administrator-04',
                 'question': 'I forgot my password. What should I do?',
                 'answer': 'Select Forgot password? on the sign-in page, enter your account email, and submit the '
                           'request. Check your inbox and spam folder for the reset link. Use it to set a new password '
                           'of at least 10 characters with uppercase and lowercase letters, a number, and a symbol. '
                           'Request a new link if the first one is invalid, used, or expired.'},
                {'id': 'council_administrator-05',
                 'question': 'How do I update my profile or change my password while signed in?',
                 'answer': 'Open My Profile. In Profile Information, update your name, phone number, department, or '
                           'position and select Save Changes. To change your password, open Change Password, enter '
                           'your current password, then enter and confirm a new password that meets the on-screen '
                           'requirements.'},
                {'id': 'council_administrator-06',
                 'question': 'Can I change the email address I use to sign in?',
                 'answer': 'No. Your sign-in email is read-only in My Profile and cannot be changed there. Contact '
                           'Customer Service if it must be changed.'},
                {'id': 'council_administrator-07',
                 'question': 'Where do I start common administration tasks?',
                 'answer': 'Start from the Council Administration Dashboard. Its shortcuts open grant creation, '
                           'application review, staff approvals, staff management, communications, billing, profile '
                           'settings, QR codes, analytics, voting, and the grant map. Dashboard figures relate to your '
                           'own council; use Retry if the dashboard cannot load.'},
                {'id': 'council_administrator-08',
                 'question': 'How do I read or clear my notifications?',
                 'answer': 'Select the bell on the dashboard to open recent notifications. Select a notification to '
                           'mark it read and, where available, open its linked portal page. Use Mark all read to clear '
                           'unread indicators, or Retry if the list fails to load.'},
                {'id': 'council_administrator-09',
                 'question': 'What do I need before I can create a grant program?',
                 'answer': 'In Create Grant Program, provide a title, category, description, eligibility criteria, '
                           'total funding amount, and application deadline. You can also select required documents and '
                           'add a project duration and review-process description. Correct any missing or invalid '
                           'information identified by the wizard before continuing.'},
                {'id': 'council_administrator-10',
                 'question': 'Can I save a grant as a draft and publish it later?',
                 'answer': 'Yes. Select Save Draft while preparing the grant; drafts are not available to applicants. '
                           'When ready, select Publish Grant Program in the final review step. If saving or publishing '
                           'fails, correct the displayed error and try again.'},
                {'id': 'council_administrator-11',
                 'question': 'How do I set up reviewers and approval requirements for a grant?',
                 'answer': 'In the Assessment Team step, select active Council Administrators or Council Staff as '
                           'reviewers and set the required number of approvals. The threshold cannot exceed the number '
                           'of selected reviewers. Selected reviewers are assigned when an application is submitted; '
                           'if no reviewers are selected, staff can self-assign and the grant uses one required '
                           'approval.'},
                {'id': 'council_administrator-12',
                 'question': 'Can AI write or decide a grant program for me?',
                 'answer': 'The AI Assistant can provide drafting suggestions after you add a title, category, or '
                           'description. Review each suggestion and decide whether to apply it. AI is advisory only, '
                           'is never applied automatically, and must never make funding decisions. Do not submit '
                           'sensitive information, funding-allocation instructions, or embedded instructions in an AI '
                           'request.'},
                {'id': 'council_administrator-13',
                 'question': 'How do I show a grant on the public map without exposing private locations?',
                 'answer': 'Map display is optional and should be enabled only after council consent for public '
                           'display. Enter a public location name and valid coordinates for a suburb, precinct, or '
                           'facility. Never enter an applicant’s private address or another private applicant '
                           'location. A marker is public only when the grant is published, mapping is enabled, valid '
                           'coordinates are present, and the council plan permits mapping.'},
                {'id': 'council_administrator-14',
                 'question': 'How do I create and share a grant QR code?',
                 'answer': 'Open QR Code Management, select a grant, and wait for the preview. You can choose a style, '
                           'download a PNG, copy the grant URL, share it, or regenerate the code. The QR code opens '
                           'the grant’s public URL; test it before distributing it. Create a grant first if none are '
                           'available to select.'},
                {'id': 'council_administrator-15',
                 'question': 'Why can’t I open a grant or application from another council?',
                 'answer': 'Council Administrator access is limited to grants, applications, staff, and council '
                           'information belonging to your own council. This protects applicant and council data '
                           'between tenants. Access to another council’s records is not available through the Council '
                           'Administrator portal.'},
                {'id': 'council_administrator-16',
                 'question': 'How do I review an application?',
                 'answer': 'Open Pending Approvals, select or self-assign the application where appropriate, then '
                           'choose Review. Enter a score, recommendation, and assessment comments, then submit the '
                           'review. A review records an assessment; it is not a funding decision by itself.'},
                {'id': 'council_administrator-17',
                 'question': 'How do I assign an application to a reviewer?',
                 'answer': 'In Pending Approvals, select Assign, choose a staff member from your council, add optional '
                           'notes, and confirm. Assigning moves a submitted application into review. Council Staff can '
                           'self-assign but cannot assign another staff member, and a person who has recused '
                           'themselves cannot be reassigned to that application.'},
                {'id': 'council_administrator-18',
                 'question': 'What should I do if I have a conflict of interest on an application?',
                 'answer': 'If assigned, select Recuse in Pending Approvals, record a brief reason where appropriate, '
                           'and confirm. A recused reviewer cannot be reassigned to the same application. Use the '
                           'assignment controls to allocate the review to another suitable council reviewer.'},
                {'id': 'council_administrator-19',
                 'question': 'Who can approve or reject a grant application?',
                 'answer': 'A Council Administrator can use Approve or Reject in Pending Approvals for applications '
                           'that are submitted or under review. Council Staff can review applications but cannot make '
                           'the final approval or rejection. AI suggestions and community voting are advisory only and '
                           'cannot be the decision-maker.'},
                {'id': 'council_administrator-20',
                 'question': 'How do I add a staff member?',
                 'answer': 'Go to Manage Staff and select Add Staff Member. Enter the person’s first name, last name, '
                           'email address, and role. You may enter a password or leave it blank to generate a '
                           'temporary password. Provide a displayed temporary password only through your council’s '
                           'approved secure process and ask the person to change it at first sign-in.'},
                {'id': 'council_administrator-21',
                 'question': 'Can I change a staff member’s role, deactivate them, or reset their password?',
                 'answer': 'Yes. In Manage Staff, select Edit to update a staff member’s name, role, or active status. '
                           'Deactivation prevents portal access. Select Reset PW to set a new password for a staff '
                           'member in your council, then provide it through an approved secure channel.'},
                {'id': 'council_administrator-22',
                 'question': 'How do I approve or reject a pending staff account request?',
                 'answer': 'Open Staff Approvals and review the pending person’s name, email, role, and available '
                           'employment details. Select Approve to activate the account, or Reject and optionally '
                           'provide a reason. Rejection removes the pending account record and sends the requester a '
                           'notification.'},
                {'id': 'council_administrator-23',
                 'question': 'How do I start or manage a council subscription?',
                 'answer': 'Open Account & Billing. If there is no active subscription, select a plan and billing '
                           'cycle, then choose Continue to secure checkout. After returning from checkout, GrantThrive '
                           'updates the subscription status. For an active subscription, select Manage billing to open '
                           'the billing portal. If checkout is cancelled, no charge is made.'},
                {'id': 'council_administrator-24',
                 'question': 'What should I do if billing will not load or checkout cannot be completed?',
                 'answer': 'Use Retry on Account & Billing and confirm that you are signed in as the administrator for '
                           'that council. If the account is not linked to a council, billing is unavailable, or the '
                           'payment provider continues to reject the request after retrying, contact Customer '
                           'Service.'},
                {'id': 'council_administrator-25',
                 'question': 'How do I update the council’s contact details?',
                 'answer': 'In Account & Billing, use Contact Details and select Edit. Update the council contact '
                           'email, phone number, or website URL, then save. These details do not change your personal '
                           'sign-in email.'},
                {'id': 'council_administrator-26',
                 'question': 'How do I activate or cancel the SMS notifications add-on?',
                 'answer': 'Open Account & Billing and review the SMS tiers. On an eligible paid plan, select a tier, '
                           'review the confirmation, and confirm activation. SMS is not available during the free '
                           'trial. You can cancel an active SMS add-on from the same page; separate provider '
                           'credentials are not entered in the council portal.'},
                {'id': 'council_administrator-27',
                 'question': 'How do I control SMS alerts or test that they work?',
                 'answer': 'Open Communication Settings. When SMS is enabled for your council, choose alert events, '
                           'set business-hours limits, select a timezone, and save. Use Send Test to send a test SMS '
                           'to the phone number in your administrator profile; add a phone number in My Profile first '
                           'if none is available. The Usage tab shows recent SMS use.'},
                {'id': 'council_administrator-28',
                 'question': 'Can I turn off or customise GrantThrive’s email notification templates?',
                 'answer': 'Transactional emails are sent automatically on the council’s behalf. The Council '
                           'Administrator portal has no self-service switch or template editor for these emails. '
                           'Contact Customer Service to request a change to council email branding or notification '
                           'templates.'},
                {'id': 'council_administrator-29',
                 'question': 'What can I export from Analytics?',
                 'answer': 'Open Analytics to view council grant and application metrics, trends, category and status '
                           'distributions, and performance summaries. Select Refresh to reload current data. Select '
                           'Export Data to download the displayed analytics as a JSON file. Use underlying grant and '
                           'application records for formal decisions rather than dashboard recommendations.'},
                {'id': 'council_administrator-30',
                 'question': 'Can community voting decide which application receives funding?',
                 'answer': 'No. Community voting is advisory and non-binding. It can inform council decision-making, '
                           'but it does not approve, reject, rank for funding, or allocate grants. Final funding '
                           'decisions must be made by the council.'}]},
 {'id': 'council_staff_assessor',
  'label': 'Council Staff / Assessor',
  'description': 'Application review, assessment workflows, reviewer conduct, profile and role-limited portal access.',
  'questions': [{'id': 'council_staff_assessor-01',
                 'question': 'What can I do as Council Staff or an Assessor?',
                 'answer': 'You can view your council’s grants and applications, use the pending-review queue, '
                           'self-assign to eligible reviews, recuse yourself, and submit or update assessment reviews. '
                           'Staff portal features may also include your profile, notifications, forum, voting view, '
                           'grant map, and resources. You cannot make final decisions, assign another reviewer, manage '
                           'staff, or create, edit, publish, or archive grants; those actions require a Council '
                           'Administrator.'},
                {'id': 'council_staff_assessor-02',
                 'question': 'How do I sign in to the staff portal?',
                 'answer': 'Open the GrantThrive portal sign-in page, enter your email address and password, and '
                           'select Sign In. A successful sign-in directs Council Staff to the Staff Dashboard. If you '
                           'are already signed in and open an authentication page, the portal redirects you to your '
                           'role-based dashboard.'},
                {'id': 'council_staff_assessor-03',
                 'question': 'Why does sign-in say my email address or password is incorrect?',
                 'answer': 'Check that you are using the email address associated with your GrantThrive account and '
                           're-enter your password. The sign-in screen uses one general message and does not confirm '
                           'whether an email address is registered. Use Forgot password? if you still cannot sign in.'},
                {'id': 'council_staff_assessor-04',
                 'question': 'My account is awaiting approval. What should I do?',
                 'answer': 'A pending account cannot access the portal until it is approved and activated. Contact '
                           'your Council Administrator to confirm your staff access request or to be added as Council '
                           'Staff.'},
                {'id': 'council_staff_assessor-05',
                 'question': 'I forgot my password. How do I reset it?',
                 'answer': 'On the sign-in page, select Forgot password?, enter your account email address, and select '
                           'Send reset link. Check your inbox and spam folder, then use the link to set a new '
                           'password. The page shows the same confirmation whether or not an account exists for that '
                           'email address.'},
                {'id': 'council_staff_assessor-06',
                 'question': 'My password-reset link is invalid or expired. Can I use it again?',
                 'answer': 'No. Request a new reset link from Forgot password? and use the newest link. A reset token '
                           'is single-use and expires after one hour.'},
                {'id': 'council_staff_assessor-07',
                 'question': 'What password rules apply when I change or reset my password?',
                 'answer': 'Use at least 10 characters, including an uppercase letter, lowercase letter, number, and '
                           'special character. When changing a password from your profile, enter your current '
                           'password, then enter and confirm the new one.'},
                {'id': 'council_staff_assessor-08',
                 'question': 'How do I update my name, phone number, department, or position?',
                 'answer': 'Open Profile from the staff navigation, update the available fields, and select Save '
                           'Changes. You can update first name, last name, phone number, department, and position. If '
                           'the latest profile cannot be loaded, select Retry before saving changes.'},
                {'id': 'council_staff_assessor-09',
                 'question': 'How do I change my email address?',
                 'answer': 'Email is read-only in the Profile page and cannot be changed in the staff portal. Contact '
                           'Customer Service if your account email must be changed.'},
                {'id': 'council_staff_assessor-10',
                 'question': 'Why was I signed out or sent back to the login page?',
                 'answer': 'The portal checks your saved session when it loads. If it is expired, invalid, inactive, '
                           'or rejected, the portal clears it and returns you to sign-in. Sign in again, and use '
                           'Logout when finished on a shared or public device.'},
                {'id': 'council_staff_assessor-11',
                 'question': 'Where do I find the staff tools and navigation?',
                 'answer': 'Use the top staff navigation bar for Dashboard, Grants, Pending Approvals, Admin '
                           'Approvals, Voting, Grant Map, Resources, Forum, and Profile. On a smaller screen, open the '
                           'menu button. Select Dashboard to return to your staff landing page.'},
                {'id': 'council_staff_assessor-12',
                 'question': 'Why do I see “Access denied” or get sent somewhere else?',
                 'answer': 'The staff portal checks the role on your current account. Sign out and sign in with the '
                           'correct Council Staff account if you have more than one account. For a different role or '
                           'access not available to Council Staff, contact your Council Administrator.'},
                {'id': 'council_staff_assessor-13',
                 'question': 'Where can I see applications assigned to me?',
                 'answer': 'Open Dashboard for the My Assigned Applications overview and summary counts. For '
                           'assignment, recusal, and review actions, open Pending Approvals.'},
                {'id': 'council_staff_assessor-14',
                 'question': 'What is shown in Pending Approvals, and how can I filter it?',
                 'answer': 'Pending Approvals shows submitted and under-review applications for your council. Filter '
                           'by All, Assigned to me, or Unassigned, and select Refresh to reload. If there are no '
                           'matches, select Show all applications to return to the full pending list.'},
                {'id': 'council_staff_assessor-15',
                 'question': 'How do I take an unassigned application for review?',
                 'answer': 'In Pending Approvals, find the application and select Self-assign. It is assigned to you '
                           'and, if still submitted, moves to Under Review. You can then use Review or Recuse for that '
                           'application.'},
                {'id': 'council_staff_assessor-16',
                 'question': 'I have a conflict of interest. How do I recuse myself?',
                 'answer': 'For an application assigned to you, select Recuse, enter a brief reason, and confirm. The '
                           'queue will show the recusal, and you cannot self-assign the same application again through '
                           'the normal staff action. Do not continue its assessment.'},
                {'id': 'council_staff_assessor-17',
                 'question': 'How do I submit an assessment review?',
                 'answer': 'In Pending Approvals, self-assign if needed, select Review, enter a score from 0 to 100, '
                           'choose a recommendation, add assessment comments, and select Submit Review. '
                           'Recommendations are approve, approve with conditions, reject, or defer. Your review is an '
                           'assessment record, not the final funding decision.'},
                {'id': 'council_staff_assessor-18',
                 'question': 'Can I correct a review after submitting it?',
                 'answer': 'Yes. Reopen Review for the application and submit the corrected score, recommendation, or '
                           'comments. GrantThrive updates your existing review rather than creating a second review '
                           'from you.'},
                {'id': 'council_staff_assessor-19',
                 'question': 'Can I approve or reject an application myself?',
                 'answer': 'No. Council Staff can submit assessment reviews and recommendations, but final approval '
                           'and rejection are restricted to a Council Administrator or system-level administrator. '
                           'Contact the Council Administrator when a final decision must be recorded.'},
                {'id': 'council_staff_assessor-20',
                 'question': 'How do I assign an application to another assessor?',
                 'answer': 'Council Staff can only self-assign; you cannot assign another person. Contact the Council '
                           'Administrator to allocate a different reviewer. An administrator can select another active '
                           'Council Staff member or Council Administrator from the council’s staff list.'},
                {'id': 'council_staff_assessor-21',
                 'question': 'Why can’t I submit a review for an application?',
                 'answer': 'Refresh Pending Approvals and check the status. Reviews can be submitted only while an '
                           'application is Submitted or Under Review, and only for applications in your own council. '
                           'If it is no longer reviewable or needs another reviewer, contact the Council Administrator '
                           'rather than attempting to change the final status.'},
                {'id': 'council_staff_assessor-22',
                 'question': 'What applicant information can I access, and how should I handle it?',
                 'answer': 'You can access application information only for grants belonging to your council. Use it '
                           'only for authorised assessment work and do not share it outside the authorised council '
                           'process. The system denies access across council boundaries.'},
                {'id': 'council_staff_assessor-23',
                 'question': 'Can I download an applicant’s supporting documents?',
                 'answer': 'The current Pending Approvals screen does not provide a document-download control. If you '
                           'need a supporting document that is unavailable through the staff screen, contact the '
                           'Council Administrator. Do not ask an applicant to send assessment material through an '
                           'unapproved channel.'},
                {'id': 'council_staff_assessor-24',
                 'question': 'How do notifications and reviewer reminders work?',
                 'answer': 'Select the bell on the Dashboard to open notifications. You can open a notification, mark '
                           'one as read, or choose Mark all read; select Retry if the list does not load. Assigned '
                           'reviewers may receive an in-app and email reminder for review work waiting more than 48 '
                           'hours. A reminder does not decide or change an application outcome.'},
                {'id': 'council_staff_assessor-25',
                 'question': 'Can I change a grant’s details, assessment team, or publication status?',
                 'answer': 'No. Council Staff can view grants for their council but cannot create, edit, publish, '
                           'unpublish, archive, or configure reviewers. Contact the Council Administrator for grant '
                           'content, dates, publication, assessment-team, or approval-threshold changes.'},
                {'id': 'council_staff_assessor-26',
                 'question': 'Do community votes decide whether an application receives funding?',
                 'answer': 'No. Community voting is advisory and non-binding. It can inform council decision-making, '
                           'but it does not approve, reject, rank for funding, or allocate grants. Final decisions '
                           'remain with the council.'},
                {'id': 'council_staff_assessor-27',
                 'question': 'Can I put an applicant’s project location on the public Grant Map?',
                 'answer': 'No. Only published grants explicitly enabled by the council for map display, with a public '
                           'location name and valid coordinates, can appear on the public map. Never use a private or '
                           'precise applicant location. Council Staff cannot configure mapping; contact the Council '
                           'Administrator to request a map-location change.'},
                {'id': 'council_staff_assessor-28',
                 'question': 'How do I take part in a community forum as staff?',
                 'answer': 'Open Forum from the staff navigation, choose a forum, and post if it is active. You can '
                           'edit or delete your own posts. Closed forums do not accept new messages. Forum content is '
                           'scoped to your council, and the current screen has no staff-facing forum-creation '
                           'control.'},
                {'id': 'council_staff_assessor-29',
                 'question': 'Can AI make, recommend, or automatically apply a funding decision?',
                 'answer': 'No. AI support is advisory drafting support only. Suggestions are not applied '
                           'automatically and must be checked by a council officer. AI must never decide funding. If '
                           'an AI feature is unavailable, continue without it; do not enter sensitive personal '
                           'information, grant-allocation requests, or embedded instructions into an AI request.'},
                {'id': 'council_staff_assessor-30',
                 'question': 'A dashboard, queue, forum, map, or notification page will not load. What should I do?',
                 'answer': 'Use the screen’s retry action first: Retry on dashboard, forum, and notification views; '
                           'Refresh in Pending Approvals; or Try again on the Grant Map and grant pages. Check your '
                           'connection, then sign out and sign in again if needed. If the issue continues, contact '
                           'Customer Service with the page name and displayed error message. Do not use someone else’s '
                           'account.'}]},
 {'id': 'applicant',
  'label': 'Applicant',
  'description': 'Finding grants, account access, applications, drafts, supporting documents and application status.',
  'questions': [{'id': 'applicant-01',
                 'question': 'How do I create an Applicant account?',
                 'answer': 'Select Register here from the sign-in page, choose Community Member, and complete the '
                           'registration steps. Enter personal details, a password, and organisation details; select '
                           'Individual if applying as an individual. After successful registration, select Continue to '
                           'portal to browse grants and manage applications.'},
                {'id': 'applicant-02',
                 'question': 'Why can’t I continue with my registration?',
                 'answer': 'Complete every required field shown, including first and last name, email, phone number, '
                           'password and confirmation, organisation type, and address. Enter an organisation name when '
                           'registering for an organisation. If the email is already in use, sign in or use Forgot '
                           'password?. If registration still fails after correcting highlighted fields, contact '
                           'Customer Service; applicant accounts cannot be merged or replaced through self-service.'},
                {'id': 'applicant-03',
                 'question': 'What password should I use?',
                 'answer': 'For registration, use at least 12 characters with an uppercase letter, lowercase letter, '
                           'number, and special character. Re-enter the same password in the confirmation field. '
                           'Follow the requirements displayed in the password-reset form when resetting a password.'},
                {'id': 'applicant-04',
                 'question': 'I can’t sign in. What should I check?',
                 'answer': 'Enter the email address and password used at registration and try again. The sign-in page '
                           'uses one general message for incorrect credentials, so check both. If it cannot reach the '
                           'server, check your connection and retry. If your account is shown as awaiting approval and '
                           'the issue does not resolve, contact Customer Service.'},
                {'id': 'applicant-05',
                 'question': 'I forgot my password. How do I reset it?',
                 'answer': 'Select Forgot password? on the sign-in page, enter your account email address, and select '
                           'Send reset link. Check your inbox and spam folder, then open the link and set a new '
                           'password. The portal shows the same confirmation whether or not an account exists for the '
                           'email address.'},
                {'id': 'applicant-06',
                 'question': 'My password-reset link is invalid or expired. What do I do?',
                 'answer': 'Return to Forgot password and request a new link. Reset links expire after one hour and '
                           'cannot be reused after a successful reset. Use the newest link and meet the password '
                           'requirements shown; contact Customer Service if you still cannot reset your password.'},
                {'id': 'applicant-07',
                 'question': 'Why was I signed out while using the portal?',
                 'answer': 'A session can expire or become invalid, and the portal then returns you to the sign-in '
                           'page. Sign in again and reopen your work from Dashboard or Browse Grants. Save application '
                           'drafts regularly before leaving the application form.'},
                {'id': 'applicant-08',
                 'question': 'Where do I find my applications and other Applicant features?',
                 'answer': 'Use the top navigation for Dashboard, Browse Grants, Voting, Grant Map, Winners, '
                           'Resources, Forum, and Transparency. To see every application you have started, open Browse '
                           'Grants and select My applications. The Dashboard also shows recent applications and '
                           'outstanding actions.'},
                {'id': 'applicant-09',
                 'question': 'How do I find a suitable grant?',
                 'answer': 'Open Browse Grants. Search by grant title, description, or tags; filter by category, '
                           'status, and funding amount; and sort by deadline, amount, or popularity. Select Details to '
                           'review a grant, or Clear all filters if nothing matches.'},
                {'id': 'applicant-10',
                 'question': 'Why can’t I apply for a grant that is closed?',
                 'answer': 'Apply now is disabled for closed grants. An application may also be refused if the grant '
                           'is no longer open when you save or submit. Return to Browse Grants and select an open '
                           'opportunity. Grant details show the published deadline, eligibility information, supplied '
                           'required documents, and any published timeline.'},
                {'id': 'applicant-11',
                 'question': 'Where can I check eligibility, documents, and the deadline before applying?',
                 'answer': 'Open a grant and select Details. Review Eligibility Criteria, Documents Required, '
                           'Application Process, funding information, location, and deadline. If a necessary detail '
                           'has not been published, contact the Council Administrator for grant-specific '
                           'clarification.'},
                {'id': 'applicant-12',
                 'question': 'How do I start an application?',
                 'answer': 'Sign in, find an open grant, and select Apply now. The form opens as a seven-step workflow '
                           'linked to that grant. If you reach the form without a grant selected, return to Browse '
                           'Grants and start from the opportunity.'},
                {'id': 'applicant-13',
                 'question': 'What information does the application form ask for?',
                 'answer': 'The seven steps are Organization, Contact Details, Project Details, Budget, Impact & '
                           'Planning, Documents, and Review & Submit. Use Previous and Next to move through the form. '
                           'Required fields are checked as you continue.'},
                {'id': 'applicant-14',
                 'question': 'Why is the form asking for an ABN, and what if it does not validate?',
                 'answer': 'The form checks that an ABN has 11 digits and, where available, whether it is valid and '
                           'active. Wait for the check before continuing. Correct an invalid or inactive ABN. If a '
                           'connection issue prevents the check, select Retry check; a valid format is not the same as '
                           'a completed live verification.'},
                {'id': 'applicant-15',
                 'question': 'How do I save an application as a draft?',
                 'answer': 'Select Save Draft at the bottom of the form. Before the first save, complete the core '
                           'draft information: organisation name, project title and description, amount requested, and '
                           'primary contact name and email. After edits, the portal also attempts to save '
                           'automatically after a short pause; check for Saving… or Saved. A draft remains editable '
                           'until submission.'},
                {'id': 'applicant-16',
                 'question': 'How do I return to a draft application?',
                 'answer': 'Open Browse Grants, select My applications, and choose Continue beside a Draft or In '
                           'progress application. You can also use Update on an eligible Dashboard item. Open the '
                           'saved application from its associated grant.'},
                {'id': 'applicant-17',
                 'question': 'My saved application will not load. What should I do?',
                 'answer': 'Use Retry when offered. If the message says the application belongs to a different grant '
                           'or must be opened from its grant, return to Browse Grants and reopen it through My '
                           'applications. If the problem continues, contact Customer Service. Do not create a new '
                           'application for a different grant to bypass the error.'},
                {'id': 'applicant-18',
                 'question': 'How do I upload supporting documents?',
                 'answer': 'Go to step 6, Documents, and select Browse Files. Save the application as a draft first. '
                           'Supported formats are PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, CSV, PNG, JPG, JPEG, GIF, '
                           'and WEBP. Each file must be 20 MB or smaller, and an application can have up to 20 '
                           'documents.'},
                {'id': 'applicant-19',
                 'question': 'Why did my document upload fail, or how do I remove a document?',
                 'answer': 'Check that the file is not empty, is no larger than 20 MB, and uses a supported extension. '
                           'The form identifies files that were not uploaded and can refresh the document list. To '
                           'remove an uploaded file, use its remove button in Uploaded Files. If storage is '
                           'unavailable or a valid upload continues to fail, wait and retry; contact Customer Service '
                           'if the issue persists.'},
                {'id': 'applicant-20',
                 'question': 'What must I do before I submit my application?',
                 'answer': 'At step 7, Review & Submit, review the organisation and project summary. Accept all three '
                           'declarations: that information is true and correct, privacy collection and use consent, '
                           'and agreement to the grant program terms and conditions. Then select Submit Application.'},
                {'id': 'applicant-21',
                 'question': 'Why did my application submission fail?',
                 'answer': 'Read the message beside the submit button, correct the stated issue, and try again. Common '
                           'blockers are an unsaved or incomplete draft, missing declarations, a closed grant, or an '
                           'existing application where multiple applications are not allowed. For a grant-specific '
                           'exception or deadline question, contact the Council Administrator.'},
                {'id': 'applicant-22',
                 'question': 'Can I edit, withdraw, or change an application after I submit it?',
                 'answer': 'Application form details can be edited only while the application is a draft. The portal '
                           'has no Applicant self-service control to change the submitted form, withdraw the '
                           'application, or alter its status. Contact the Council Administrator for a correction, '
                           'withdrawal, or other post-submission request; no outcome can be promised.'},
                {'id': 'applicant-23',
                 'question': 'How do I track my application status?',
                 'answer': 'Open Browse Grants and select My applications, or use My applications on the Dashboard. '
                           'Filter by Draft, In progress, Submitted, Under review, Approved, or Rejected. Status shows '
                           'workflow position; it does not provide a decision date unless the grant publishes one.'},
                {'id': 'applicant-24',
                 'question': 'How will I know if my application is approved or unsuccessful?',
                 'answer': 'Check My applications and the notification bell on the Dashboard. When a council records '
                           'an approval or rejection, GrantThrive creates an applicant notification. A council makes '
                           'the funding decision; being under review, receiving a score, or receiving community '
                           'attention does not mean funding has been awarded.'},
                {'id': 'applicant-25',
                 'question': 'Can I change the email address on my Applicant account?',
                 'answer': 'The Applicant portal does not provide a self-service email-change screen. Do not create a '
                           'second account just to use another email address. Contact Customer Service to request an '
                           'account-email change.'},
                {'id': 'applicant-26',
                 'question': 'Who can see my application and personal information?',
                 'answer': 'Your application list and full application details are limited to you as the application '
                           'owner and authorised council staff or administrators for the relevant council. Other '
                           'applicants cannot open or update your application or documents. Published approved '
                           'outcomes may include project information such as organisation, project title, grant, date, '
                           'category, and funding amount; do not post private information in public forums.'},
                {'id': 'applicant-27',
                 'question': 'Will my project or address appear on the public Grant Map?',
                 'answer': 'No private applicant or project address should appear on the public map. It shows only '
                           'published grants that a council has approved for map display and that have valid public '
                           'map coordinates. A public location needs council consent and a public location name. If '
                           'you believe a map listing reveals private information, contact the Council Administrator.'},
                {'id': 'applicant-28',
                 'question': 'How does community voting affect my application?',
                 'answer': 'Community voting is advisory and non-binding. It may inform council decision-making, but '
                           'it does not approve, reject, rank for funding, or allocate grants. Final funding decisions '
                           'are made by the council. Active voting sessions can have their own eligibility and '
                           'vote-limit rules.'},
                {'id': 'applicant-29',
                 'question': 'Can I use the community forum to ask or discuss grant topics?',
                 'answer': 'Open Forum to read public forums for your council. In an active public forum, you can post '
                           'a message, edit your own post, or delete your own post; messages are limited to 5,000 '
                           'characters. You cannot access a forum that is not public or post in a closed forum. A '
                           'forum cannot alter an application or obtain a funding decision.'},
                {'id': 'applicant-30',
                 'question': 'Can AI decide whether my application receives funding?',
                 'answer': 'No. The Applicant portal has no AI decision-maker. Any AI material used elsewhere in '
                           'GrantThrive is advisory only, must be reviewed by a person, and cannot approve, reject, '
                           'rank for funding, or allocate funding. Funding decisions remain with the council.'}]},
 {'id': 'community_member',
  'label': 'Community Member',
  'description': 'Community grant discovery, advisory voting, public map, forum, results, transparency and personal '
                 'applications.',
  'questions': [{'id': 'community_member-01',
                 'question': 'How do I create a Community Member account?',
                 'answer': 'Choose Community Member on the registration page and complete personal and organisation '
                           'details. You need an email address, phone number, password, organisation type, and '
                           'address; enter an organisation name if registering for an organisation rather than as an '
                           'individual. Successful registration activates the account and signs you in to the '
                           'Community Member dashboard.'},
                {'id': 'community_member-02',
                 'question': 'What password do I need when I register?',
                 'answer': 'Use at least 12 characters with an uppercase letter, lowercase letter, number, and special '
                           'character. Re-enter the same password in the confirmation field before continuing.'},
                {'id': 'community_member-03',
                 'question': 'I already have an account. Should I register again?',
                 'answer': 'No. If the email is already registered, sign in instead. If you cannot remember the '
                           'password, use Forgot password?. Registration rejects duplicate email accounts.'},
                {'id': 'community_member-04',
                 'question': 'Why can’t I sign in?',
                 'answer': 'Check the email address and password used at registration, then try again. The sign-in '
                           'page uses a general message for incorrect credentials. If an account you expect to use as '
                           'a Community Member remains shown as awaiting approval, contact Customer Service; do not '
                           'create another account.'},
                {'id': 'community_member-05',
                 'question': 'I forgot my password. What should I do?',
                 'answer': 'Select Forgot password?, enter your account email, and select Send reset link. Check your '
                           'inbox and spam folder, then use the link to set a new password. The confirmation message '
                           'is the same whether or not an account exists for that email.'},
                {'id': 'community_member-06',
                 'question': 'My password-reset link is invalid or expired. How do I recover access?',
                 'answer': 'Request a new reset link from Forgot password. Reset links are single-use and expire after '
                           'one hour. On the reset page, follow the displayed password rules, which require at least '
                           '10 characters including uppercase and lowercase letters, a number, and a special '
                           'character.'},
                {'id': 'community_member-07',
                 'question': 'I was signed out or sent back to the login page. What should I do?',
                 'answer': 'Sign in again. The portal validates saved sessions when it opens and clears a rejected '
                           'session. Reopen the relevant grant or saved application from My applications, and save '
                           'drafts before leaving an application whenever possible.'},
                {'id': 'community_member-08',
                 'question': 'Where can I find the main Community Member features?',
                 'answer': 'Use the top navigation for Dashboard, Browse Grants, Voting, Grant Map, Winners, '
                           'Resources, Forum, and Transparency. On a smaller screen, open the menu icon. Use Logout '
                           'when you have finished.'},
                {'id': 'community_member-09',
                 'question': 'How do I change the email address on my account?',
                 'answer': 'The Community Member portal has no email-change screen. Contact Customer Service to '
                           'request an account-email change, and do not create a second account solely to use another '
                           'email address.'},
                {'id': 'community_member-10',
                 'question': 'How do I find a grant that suits me?',
                 'answer': 'Open Browse Grants. Search by title, description, or tags; filter by category, status, and '
                           'funding amount; and sort by deadline, amount, or popularity. Select Details to read a '
                           'grant or Apply now to start an application for an open grant.'},
                {'id': 'community_member-11',
                 'question': 'Where can I check a grant’s eligibility, documents, and deadline?',
                 'answer': 'Open a grant and select Details. The page shows its published overview, funding amount, '
                           'dates, eligibility criteria, required documents, application process, and other published '
                           'information. Contact the Council Administrator for program-specific clarification where '
                           'information has not been published.'},
                {'id': 'community_member-12',
                 'question': 'Can I apply for a grant from a different council?',
                 'answer': 'No. You can browse and apply only within the council linked to your account, and only '
                           'published grants are listed. If you think your account is linked to the wrong council, '
                           'contact the Council Administrator; the portal has no self-service council-reassignment '
                           'action.'},
                {'id': 'community_member-13',
                 'question': 'How do I start, save, and continue an application draft?',
                 'answer': 'Select Apply now from an open grant, complete the form in stages, and select Save Draft. '
                           'Once required draft details are present, the form also attempts to save changes '
                           'automatically after edits. To continue later, choose Browse Grants, open My applications, '
                           'and select Continue for the draft.'},
                {'id': 'community_member-14',
                 'question': 'Why can’t I open my saved application?',
                 'answer': 'Open it from My applications under the grant it belongs to. The portal blocks a saved '
                           'application if the link points to a different grant or lacks the required grant '
                           'association. Use Back to grants or Retry; if it still cannot be loaded after retrying, '
                           'contact Customer Service.'},
                {'id': 'community_member-15',
                 'question': 'What supporting documents can I upload?',
                 'answer': 'After saving the required draft details, use Browse Files on the Documents step. You can '
                           'upload PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, CSV, PNG, JPG, JPEG, GIF, and WEBP '
                           'files. Each file must be 20 MB or smaller, and an application can hold up to 20 documents. '
                           'You can remove an uploaded document before submission.'},
                {'id': 'community_member-16',
                 'question': 'My document upload failed. What can I try?',
                 'answer': 'Check the file type and size, save the application draft, and retry. If only some files '
                           'fail, the page lists their names. If the portal reports that file storage is not '
                           'configured, or valid files continue to fail after retrying, contact Customer Service.'},
                {'id': 'community_member-17',
                 'question': 'Why is my ABN not being accepted?',
                 'answer': 'Enter all 11 ABN digits. The application form checks its format and, where live validation '
                           'is available, can identify an inactive ABN. Correct the number or use an active ABN. If '
                           'the check cannot complete because of a connection problem, select Retry check. An ABN may '
                           'be optional in registration but is required by the application form.'},
                {'id': 'community_member-18',
                 'question': 'What do I need to do before I submit an application?',
                 'answer': 'Complete the application, review the summary, and accept all three declarations: '
                           'information is true and correct, privacy consent, and the grant program terms and '
                           'conditions. Then select Submit Application. Submission is available only for a draft '
                           'associated with an open grant.'},
                {'id': 'community_member-19',
                 'question': 'Can I change or withdraw an application after I submit it?',
                 'answer': 'The Community Member screens provide no self-service change or withdrawal control after '
                           'submission. Drafts are editable; submitted applications cannot be edited through the '
                           'draft-update workflow. Contact the Council Administrator for a correction or withdrawal '
                           'request, as no program-specific outcome can be promised.'},
                {'id': 'community_member-20',
                 'question': 'Where can I see my application status and updates?',
                 'answer': 'Use the Dashboard or Browse Grants → My applications to see your own statuses, including '
                           'draft, submitted, under review, approved, and rejected. Open the notification bell to read '
                           'recent updates. You can mark one notification, or all notifications, as read.'},
                {'id': 'community_member-21',
                 'question': 'My application was unsuccessful or I need a decision explained. What can I do?',
                 'answer': 'The Dashboard can show an Unsuccessful status, but the portal does not provide an appeal, '
                           'reconsideration, or decision-explanation workflow. Contact the Council Administrator for '
                           'program-specific next steps or clarification. Do not treat community voting, a dashboard '
                           'status, or an AI suggestion as a funding decision.'},
                {'id': 'community_member-22',
                 'question': 'Who can see my application and personal details?',
                 'answer': 'You can access only your own applications and documents. Council staff and administrators '
                           'may access applications in their council for review; other Community Members cannot browse '
                           'your record. Published public results may show approved project outcomes, but not '
                           'application contact details. Private applicant locations must not be shown on the public '
                           'grant map.'},
                {'id': 'community_member-23',
                 'question': 'Does community voting decide which projects receive funding?',
                 'answer': 'No. Community voting is advisory and non-binding. It provides community input but does not '
                           'approve, reject, rank for funding, or allocate grants. Final funding decisions are made '
                           'through the council’s authorised review and approval process.'},
                {'id': 'community_member-24',
                 'question': 'How do I vote in an active community voting session?',
                 'answer': 'Open Voting, select an active session if more than one is available, select the permitted '
                           'options, then choose Submit my votes. The page shows session dates, time remaining, '
                           'participation, and current vote totals. For registration-required sessions, sign in with '
                           'an approved Community Member account linked to the same council.'},
                {'id': 'community_member-25',
                 'question': 'Why can’t I vote, or change a vote I already recorded?',
                 'answer': 'You cannot vote if a session is closed, your account is ineligible for a '
                           'registration-required session, or the vote is outside its permitted range. Follow the '
                           'on-screen message and retry only if the issue can be corrected. Once a vote is recorded, '
                           'the portal does not provide a self-service edit or withdrawal action. Contact the Council '
                           'Administrator only to ask about council options; no change can be promised.'},
                {'id': 'community_member-26',
                 'question': 'What does the Grant Map show, and can it reveal an applicant’s location?',
                 'answer': 'The Grant Map shows only published grants that a council has approved for map display and '
                           'that have valid coordinates. You can search mapped grants and filter by category or '
                           'status. It must never reveal a private or applicant location; public locations are '
                           'council-approved grant locations only.'},
                {'id': 'community_member-27',
                 'question': 'How do Community Forums work?',
                 'answer': 'Open Forum to view active public forums for your council. In an open forum, you can read '
                           'messages and post up to 5,000 characters. You can edit or delete only your own posts. You '
                           'cannot access private forums, create or close a forum, or edit or delete someone else’s '
                           'post.'},
                {'id': 'community_member-28',
                 'question': 'What can I see in Public Results, Transparency, and Winners?',
                 'answer': 'Use Public Results for published approved outcomes, funding totals, categories, and '
                           'completed grant programs. Transparency shows published grant, application, funding, voting '
                           'summaries, and recent grants. Winners lets you search and filter approved applications '
                           'returned for your account by year, category, and funding range. Use Retry or Try Again if '
                           'a page cannot load.'},
                {'id': 'community_member-29',
                 'question': 'Why is the Resource Hub empty?',
                 'answer': 'The Community Member Resource Hub is currently a placeholder. It does not currently '
                           'provide downloads, previews, saved items, or search. There is no resource request or '
                           'upload action on that page.'},
                {'id': 'community_member-30',
                 'question': 'Can AI decide whether my application receives funding?',
                 'answer': 'No. AI is advisory only and must never decide funding. The Community Member workflow has '
                           'no AI funding-decision action. Funding decisions are made by authorised council reviewers '
                           'and administrators through the review and approval process.'}]},
 {'id': 'public_visitor',
  'label': 'Public Visitor',
  'description': 'Marketing website, public information, registration, waitlist/contact forms and the limits of '
                 'visitor access.',
  'questions': [{'id': 'public_visitor-01',
                 'question': 'What can I do without signing in?',
                 'answer': 'You can use the public website to view Home, Features, Pricing, the ROI Calculator, '
                           'Resources, and Contact pages. You can also use the standalone interactive map at `/map`. '
                           'Community portal areas require a signed-in account and redirect visitors to login when '
                           'accessed without a session.'},
                {'id': 'public_visitor-02',
                 'question': 'How do I move around the public website?',
                 'answer': 'Use the top navigation for Home, Features, Pricing, ROI Calculator, Resources, and '
                           'Contact. On a phone or smaller screen, use the menu button. Select Login to enter the '
                           'portal or Get Started to open the Contact page.'},
                {'id': 'public_visitor-03',
                 'question': 'Where can I download free grant guides and templates?',
                 'answer': 'Open Resources from the public navigation. The page provides downloadable PDFs including '
                           'the Grant Writing Guide, Application Checklist, Council ROI Report Template, Community '
                           'Engagement Playbook, Compliance & Governance Guide, and Grant Program Metrics Guide. '
                           'Select Download Free for the resource you want.'},
                {'id': 'public_visitor-04',
                 'question': 'Can I use the ROI Calculator without an account?',
                 'answer': 'Yes. The ROI Calculator is public and does not require a portal sign-in. Open it from the '
                           'public navigation or visit `/roi-calculator`.'},
                {'id': 'public_visitor-05',
                 'question': 'How do I contact GrantThrive for help or a general question?',
                 'answer': 'Open the public Contact page and choose the relevant enquiry type: demo, pricing, support, '
                           'or general. Complete the form and its verification step, then select Send Message. For '
                           'product or account support that you cannot resolve yourself, choose Support.'},
                {'id': 'public_visitor-06',
                 'question': 'What information does the contact form require?',
                 'answer': 'Your full name, email address, and message are required. Council or organisation and phone '
                           'are optional. Choose an enquiry type and complete the on-page verification before '
                           'sending.'},
                {'id': 'public_visitor-07',
                 'question': 'Why can’t I send the contact form until I complete verification?',
                 'answer': 'Public contact and waitlist forms require verification. Complete it, then try sending '
                           'again. If it expires, complete it again. If verification cannot load, refresh the page and '
                           'retry; the form cannot be submitted until a valid verification token is available.'},
                {'id': 'public_visitor-08',
                 'question': 'My contact form did not send. What should I do?',
                 'answer': 'Check that required fields are complete, the email address is valid, and verification is '
                           'complete, then submit again. If the site reports too many requests, wait and retry later. '
                           'If the problem continues, submit a Support enquiry through the public contact form when it '
                           'is available to contact Customer Service.'},
                {'id': 'public_visitor-09',
                 'question': 'How do I join the GrantThrive launch list?',
                 'answer': 'On the public home page, enter your first name and email address in the launch-list '
                           'section, complete verification, and select Notify Me. The page confirms a successful '
                           'sign-up. If it fails, complete verification again and retry.'},
                {'id': 'public_visitor-10',
                 'question': 'Can I create a GrantThrive account as a member of the public?',
                 'answer': 'Yes. Select Register from the portal login page, then choose Community Member. This '
                           'account type is for individuals or organisations applying for grants and participating in '
                           'the community portal. Successful Community Member registration activates the account.'},
                {'id': 'public_visitor-11',
                 'question': 'What do I need to register, and how strong must my password be?',
                 'answer': 'Follow the registration form and provide the required personal and organisation details '
                           'for the account type selected. Registration requires an email address, password, first '
                           'name, and last name; organisation details may also be requested. Follow the on-screen '
                           'password rule: the registration form requires at least 12 characters with uppercase and '
                           'lowercase letters, a number, and a special character.'},
                {'id': 'public_visitor-12',
                 'question': 'The site says an account already exists for my email. What now?',
                 'answer': 'Do not create another account with the same email address. Try signing in instead. If you '
                           'do not remember the password, use Forgot password? on the login page.'},
                {'id': 'public_visitor-13',
                 'question': 'How do I sign in to the portal?',
                 'answer': 'Select Login on the public site, or go to `/portal/login/`. Enter the email address and '
                           'password for your GrantThrive account, then select Sign In. After a successful sign-in, '
                           'the portal directs you to the workspace allowed for your role.'},
                {'id': 'public_visitor-14',
                 'question': 'Why can’t I sign in, or why does my account say it is pending?',
                 'answer': 'Recheck your email address and password, then try again. If the page cannot reach the '
                           'server, check your connection and retry. A pending account cannot be approved from the '
                           'login page. Community Member accounts are normally active after successful '
                           'self-registration; for an account that remains pending, use the public Support contact '
                           'form to contact Customer Service.'},
                {'id': 'public_visitor-15',
                 'question': 'I forgot my password, or my reset link does not work. What should I do?',
                 'answer': 'On the login page, select Forgot password?, enter your account email address, and request '
                           'a reset link. Check your inbox and spam folder. If the link is missing, invalid, expired, '
                           'or used, request a new one. Reset tokens expire after one hour; meet the password '
                           'requirements displayed on the reset page.'},
                {'id': 'public_visitor-16',
                 'question': 'Why was I sent back to the login page?',
                 'answer': 'Portal pages require a valid signed-in session. If a saved session is expired, invalid, or '
                           'no longer accepted, GrantThrive clears it and returns you to login. Sign in again; if it '
                           'repeats, check your connection and use password reset if needed.'},
                {'id': 'public_visitor-17',
                 'question': 'Why can’t I open a community portal page as a visitor?',
                 'answer': 'Community dashboard, grants, applications, voting, grant map, winners, resources, forum, '
                           'transparency, and public-results pages are protected portal routes. Register as a '
                           'Community Member or sign in to continue.'},
                {'id': 'public_visitor-18',
                 'question': 'How do I browse grant opportunities?',
                 'answer': 'Sign in as a Community Member and open Browse Grants from the community navigation. You '
                           'can search, filter, sort, paginate, and open grant-detail pages. Community Members see '
                           'published grants for their own council; drafts and unpublished grants are not shown.'},
                {'id': 'public_visitor-19',
                 'question': 'Where can I find a grant’s eligibility, documents, and deadline?',
                 'answer': 'After signing in, open the grant’s Details page. It presents published descriptions, '
                           'funding, dates, eligibility criteria, required documents, and application-process '
                           'information where available. A section that says information has not been published is not '
                           'available in the portal for that grant.'},
                {'id': 'public_visitor-20',
                 'question': 'How do I apply for a grant?',
                 'answer': 'Sign in as a Community Member, open an eligible grant, and select Apply Now. Complete the '
                           'in-portal application form and accept all required declarations before submission. The '
                           'application is created as a draft first; only a draft can be edited through the '
                           'implemented application flow.'},
                {'id': 'public_visitor-21',
                 'question': 'Why can’t I apply for a grant?',
                 'answer': 'A grant accepts applications only while it is published, open, and within its opening and '
                           'closing dates. You also cannot apply outside your council scope. Some grants permit only '
                           'one active application per applicant; an existing non-withdrawn application can block '
                           'another. Contact the Council Administrator for program-specific eligibility or '
                           'existing-application clarification.'},
                {'id': 'public_visitor-22',
                 'question': 'Can I see public grant outcomes and transparency information?',
                 'answer': 'In the current interface, Public Results and Transparency are Community Member portal '
                           'pages, so sign in as a Community Member to open them. They present published program-level '
                           'information such as approved funding, project outcomes, categories, counts, and '
                           'participation measures, not draft grants or private application records.'},
                {'id': 'public_visitor-23',
                 'question': 'Can I take part in community voting?',
                 'answer': 'Sign in as a Community Member and open Voting to view active published voting sessions. '
                           'Some sessions require registration; in those cases, use an approved Community Member '
                           'account linked to the same council as the session.'},
                {'id': 'public_visitor-24',
                 'question': 'Does a community vote decide who receives funding?',
                 'answer': 'No. Community voting is advisory and non-binding. It does not approve, reject, rank for '
                           'funding, or allocate grants. Funding decisions remain with the council’s authorised review '
                           'and approval process.'},
                {'id': 'public_visitor-25',
                 'question': 'Why was my vote rejected or not submitted?',
                 'answer': 'Check that the session is still open, the option belongs to that session, and the value is '
                           'within the allowed range. If registration is required, sign in with an eligible Community '
                           'Member account for that council. A vote can also be refused where comments are disabled, '
                           'the same vote was already recorded, or security checks detect too-rapid or suspicious '
                           'activity. Follow the message shown and retry only when you can correct the issue.'},
                {'id': 'public_visitor-26',
                 'question': 'Can I change a vote after it is recorded?',
                 'answer': 'The current voting page does not provide a self-service edit control for a recorded vote. '
                           'Review your selections before selecting Submit my votes. If you need to ask how a recorded '
                           'vote should be handled, contact the Council Administrator; no change can be promised.'},
                {'id': 'public_visitor-27',
                 'question': 'Can I read or post in a community forum?',
                 'answer': 'Sign in as a Community Member to access forums. Community Members can see active public '
                           'forums for their council, read posts, and post messages there. You can edit or delete only '
                           'your own posts. A closed or non-public forum is unavailable to Community Members.'},
                {'id': 'public_visitor-28',
                 'question': 'How can I explore grant locations on the public map?',
                 'answer': 'Open the standalone Interactive Grant Mapping page at `/map`. You can search grants and '
                           'filter displayed national data by category, state, and size, then use Clear Filters to '
                           'reset. The council-specific Community Grant Map is a signed-in Community Member portal '
                           'page with its own council-published map data.'},
                {'id': 'public_visitor-29',
                 'question': 'Why is a grant missing from the council map, and are applicant locations shown?',
                 'answer': 'A council grant appears only when it is published, the council has explicitly approved map '
                           'display, and valid coordinates are provided. If no grants meet those conditions, no mapped '
                           'grants are shown. Public map locations must use a council-approved public location such as '
                           'a suburb, precinct, or facility—not an applicant’s private address. Private applicant '
                           'locations must never be shown.'},
                {'id': 'public_visitor-30',
                 'question': 'Can AI decide whether a grant or application receives funding?',
                 'answer': 'No. The AI Assistant is advisory drafting support for council grant drafts. Suggestions '
                           'are not applied automatically and do not make funding decisions. Funding approvals and '
                           'rejections are performed through the council’s authorised application-review workflow, not '
                           'by AI.'}]}]

COHORTS_BY_ID = {cohort["id"]: cohort for cohort in COHORTS}
QUESTIONS_BY_ID = {
    question["id"]: {**question, "cohort_id": cohort["id"]}
    for cohort in COHORTS
    for question in cohort["questions"]
}
