Feature: Notification Management
    As a user
    I want to manage my notifications
    So that I receive relevant market updates

    Background:
        Given I am an authenticated user

    Scenario: Enable price alert notifications
        Given I have price alerts disabled
        When I enable price alert notifications
        Then I should receive a confirmation
        And my notification settings should show price alerts enabled

    Scenario: Set price drop alert
        Given I am watching item "AK-47 | Vulcan"
        And the current price is $50.00
        When I set a price alert for when it drops below $40.00
        Then the alert should be saved
        And I should receive a confirmation message

    Scenario: Receive notification when price drops
        Given I have a price alert set for "AWP | Asiimov" at $30.00
        And the item price drops to $28.00
        When the price check runs
        Then I should receive a notification about the price drop
        And the notification should include the old and new prices

    Scenario: Disable all notifications
        Given I have various notifications enabled
        When I disable all notifications
        Then I should receive a confirmation
        And I should not receive any automated notifications

    Scenario: Configure digest frequency
        Given I want daily digest notifications
        When I set digest frequency to "daily"
        Then my digest preference should be saved
        And I should receive one digest per day
