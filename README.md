# TextScheduler
I'm terrible at keeping in touch with my friends. Even though I love them, months (or years) will go by without a text. This is my solution to force myself to keep in touch by automating texts to them. To keep it simple for now, the system will rotate through my contact list and send a message to each person once a week.  

## How it works
**Shortcut**
1. Set up a Shortcut that runs every week on Sunday at 12pm EST 
2. Shortcut hits /get_messages API 
3. Sends the specified messages to the specified contacts

**API**
1. 

**Rotation Job**
1. On Sunday at 11am EST, rotation job runs to delete the oldest record from the table, and replace it with an identical copy that is now the newest record in the table

**DynamoDB Schema**
- `created_by (Primary Key): String` - always `saahilc`
- `created_at (Sort Key): Timestamp` - timestamp when this messages was queued
- `contact_first_name: String` - the receiving contact's first name
- `contact_last_name: String` - the receiving contact's last name
- `contact_phone_no: String` - the receiving contact's phone number with international code appended 
- `message: String` - message to send

**Frontend (Stretch Goal)** 
I can see the upcoming messages, add a new message to the queue, or change the order of the existing messages in the queue.