Feature: Trading Operations
    As a trader
    I want to buy and sell items
    So that I can make profit from market opportunities

    Background:
        Given I am an authenticated user
        And I have sufficient balance

    Scenario: Successful item purchase
        Given an item "AK-47 | Redline" is available for $15.00
        And I have $20.00 USD balance
        When I purchase the item
        Then the purchase should be successful
        And my balance should decrease by $15.00
        And I should receive a purchase confirmation

    Scenario: Purchase fails due to insufficient balance
        Given an item "AWP | Dragon Lore" is available for $2000.00
        And I have $100.00 USD balance
        When I attempt to purchase the item
        Then the purchase should fail
        And I should see "Insufficient balance" message
        And my balance should remain unchanged

    Scenario: Successful item listing
        Given I own an item "M4A4 | Howl"
        And I want to sell it for $1500.00
        When I list the item for sale
        Then the listing should be created
        And I should receive a listing confirmation
        And the item should appear in my active listings

    Scenario: Cancel active listing
        Given I have an active listing for "Glock-18 | Fade" at $300.00
        When I cancel the listing
        Then the listing should be removed
        And the item should return to my inventory

    Scenario: Purchase with race condition
        Given an item is about to be sold out
        When multiple users attempt to purchase simultaneously
        Then only the first successful purchase should complete
        And other users should receive "Item no longer available" message
