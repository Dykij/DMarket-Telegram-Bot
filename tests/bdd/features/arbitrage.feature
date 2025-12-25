Feature: Arbitrage Scanning
    As a trader
    I want to scan for arbitrage opportunities
    So that I can make profit from price differences

    Background:
        Given the trading system is initialized
        And the API connection is established

    Scenario: Successful arbitrage scan on standard level
        Given I have valid API credentials
        And I select "csgo" game
        When I scan "standard" level for opportunities
        Then I should see opportunities with profit > 5%
        And each opportunity should have buy and sell prices

    Scenario: No opportunities found on boost level
        Given I have valid API credentials
        And market conditions are unfavorable
        When I scan "boost" level for opportunities
        Then I should see an empty results list
        And I should receive a message "No opportunities found"

    Scenario: Scan multiple games simultaneously
        Given I have valid API credentials
        When I scan "standard" level for games:
            | game   |
            | csgo   |
            | dota2  |
            | rust   |
        Then I should see combined opportunities from all games
        And opportunities should be sorted by profit descending

    Scenario: Filter opportunities by minimum profit
        Given I have valid API credentials
        And I set minimum profit threshold to 10%
        When I scan "standard" level for opportunities
        Then all returned opportunities should have profit >= 10%

    Scenario: Scan with price range filter
        Given I have valid API credentials
        And I set price range from $1.00 to $50.00
        When I scan "standard" level for opportunities
        Then all opportunities should have buy price between $1.00 and $50.00
