# reminderYandexBot

ManagerBot is a Telegram bot designed to identify and authenticate managers from a team's local Google spreadsheet. It provides managers with a list of tasks based on specific statuses.

The bot retrieves data from multiple columns and categorizes tasks into three groups based on their assigned status:

Group 1 contains tasks scheduled for the sprint.
<br>
Group 2 consists of tasks marked as completed.
<br>
Group 3 includes tasks that are not completed.

The bot operates in two modes:

- On request: Managers can query the bot to receive their assigned tasks along with relevant details.

- Automatic reminders: The bot sends task reminders to managers three times a week, automatically at 10:00.

Additionally, the bot sends a report to the head of the team, providing information about each team member's progress. The report includes the total number of tasks currently in progress, completed tasks, and tasks that are yet to be completed. This notification is scheduled to be sent on the last day of the week at 19:00.

If user's Telegram username does not match any entry in the spreadsheet, the bot responds with a message indicating that the feature is not available.
