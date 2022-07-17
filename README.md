# TextScheduler
I'm terrible at keeping in touch with my friends. Even though I love them, months (or years) will go by without a text. This is my solution to force myself to keep in touch by automating texts to them.

![Diagram](https://github.com/saahilchadha1/TextScheduler/blob/master/TextSchedulerArchitectureDiagram.drawio.png?raw=true)

## Shortcut
1. Shortcut runs every day at 12pm EST 
2. Shortcut hits `/get_messages` API 
3. Sends the specified messages to the specified contacts

## API
1. Queries DynamoDB table for all messages where `scheduled_for` is today's date 
2. Returns these records as JSON 
```
200
{ 
    "messages": [
        {
            "contact_first_name": "John",
            "contact_last_name": "Doe",
            "contact_phone_no": "12345678900", # includes country code
            "message": "What's up dude?"
        }
    ]
}

500
{
    "error": "Internal server error"
}
```

## Rotation Job
1. Every day at 9am EST, rotation job runs
2. Reads all the messages that were scheduled for yesterday, creates new records for each one based on the `rate_expression`
3. Deletes the old records
4. Sends a Slack notification detailing any errors. Or, states messages upcoming in the next 3 days.

## DynamoDB Schema
- `created_by (Parition Key): String` - always `saahilc`
- `id (Sort Key): String` - `<scheduled_for: Date>#<uuid>` Unique ID that can be used to efficiently query for a single date's scheduled messages
- `scheduled_for: Date` - date that the message is scheduled to be sent
- `created_at: UTC Timestamp` - timestamp when the message was created
- `rate_expression: String` - defines the rate at which the message should be scheduled
    - formatted as `<value> <unit>` where `<unit>` can be `day|days|week|weeks|year|years`
    - e.g. `1 year`
    - `0 <any unit>` means the message should not be requeued
- `contact_first_name: String` - the receiving contact's first name
- `contact_last_name: String` - the receiving contact's last name
- `contact_phone_no: String` - the receiving contact's phone number 
- `message: String` - message to send

## Frontend (Stretch Goal)

See the upcoming messages, add a new message to the queue, or change the order of the existing messages in the queue.
