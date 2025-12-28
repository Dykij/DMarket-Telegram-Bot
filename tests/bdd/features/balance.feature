Feature: Balance Management
    As a user
    I want to check my balance
    So that I can see how much money I have available

    Background:
        Given I am an authenticated user
        And the bot is running

    Scenario: Check balance successfully
        Given I have $100.50 USD balance
        And I have 250 DMC balance
        When I execute the /balance command
        Then I should see my USD balance as "$100.50"
        And I should see my DMC balance as "250"

    Scenario: Check balance with zero funds
        Given I have $0.00 USD balance
        And I have 0 DMC balance
        When I execute the /balance command
        Then I should see my balance as zero
        And I should see a suggestion to deposit funds

    Scenario: Handle API error gracefully
        Given the API is temporarily unavailable
        When I execute the /balance command
        Then I should see an error message
        And I should be advised to try again later

    Scenario: Balance updates after purchase
        Given I have $100.00 USD balance
        And I purchase an item for $10.00
        When I execute the /balance command
        Then I should see my USD balance as "$90.00"
