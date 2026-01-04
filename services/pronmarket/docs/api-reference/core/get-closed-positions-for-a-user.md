# Get closed positions for a user - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/core/get-closed-positions-for-a-user

---

Get closed positions for a user - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Core

Get closed positions for a user

User Guide

For Developers

Changelog

Polymarket

Discord Community

Twitter

Developer Quickstart

Developer Quickstart

Your First Order

Glossary

API Rate Limits

Endpoints

Central Limit Order Book

CLOB Introduction

Status

Clients

Authentication

CLOB Requests

Orderbook

Pricing

Spreads

Order Manipulation

Orders Overview

Place Single Order

Place Multiple Orders (Batching)

Get Order

Get Active Orders

Check Order Reward Scoring

Cancel Orders(s)

Onchain Order Info

Trades

Trades Overview

Get Trades

Websocket

WSS Overview

WSS Quickstart

WSS Authentication

User Channel

Market Channel

Real Time Data Stream

RTDS Overview

RTDS Crypto Prices

RTDS Comments

Gamma Structure

Overview

Gamma Structure

Fetching Markets

Gamma Endpoints

Health

Sports

Tags

Events

Markets

Series

Comments

Search

Data-API

Health

Core

GET

Get current positions for a user

GET

Get trades for a user or markets

GET

Get user activity

GET

Get top holders for markets

GET

Get total value of a user's positions

GET

Get closed positions for a user

Misc

Subgraph

Overview

Resolution

Resolution

Rewards

Liquidity Rewards

Conditional Token Frameworks

Overview

Splitting USDC

Merging Tokens

Reedeeming Tokens

Deployment and Additional Information

Proxy Wallets

Proxy wallet

Negative Risk

Overview

Get closed positions for a user

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://data-api.polymarket.com/closed-positions

200

400

401

500

Copy

Ask AI

[

{

"proxyWallet"

:

"0x56687bf447db6ffa42ffe2204a05edaa20f55839"

,

"asset"

:

"<string>"

,

"conditionId"

:

"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"

,

"avgPrice"

:

123

,

"totalBought"

:

123

,

"realizedPnl"

:

123

,

"curPrice"

:

123

,

"title"

:

"<string>"

,

"slug"

:

"<string>"

,

"icon"

:

"<string>"

,

"eventSlug"

:

"<string>"

,

"outcome"

:

"<string>"

,

"outcomeIndex"

:

123

,

"oppositeOutcome"

:

"<string>"

,

"oppositeAsset"

:

"<string>"

,

"endDate"

:

"<string>"

}

]

GET

/

closed-positions

Try it

Get closed positions for a user

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://data-api.polymarket.com/closed-positions

200

400

401

500

Copy

Ask AI

[

{

"proxyWallet"

:

"0x56687bf447db6ffa42ffe2204a05edaa20f55839"

,

"asset"

:

"<string>"

,

"conditionId"

:

"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"

,

"avgPrice"

:

123

,

"totalBought"

:

123

,

"realizedPnl"

:

123

,

"curPrice"

:

123

,

"title"

:

"<string>"

,

"slug"

:

"<string>"

,

"icon"

:

"<string>"

,

"eventSlug"

:

"<string>"

,

"outcome"

:

"<string>"

,

"outcomeIndex"

:

123

,

"oppositeOutcome"

:

"<string>"

,

"oppositeAsset"

:

"<string>"

,

"endDate"

:

"<string>"

}

]

Query Parameters

​

user

string

required

The address of the user in question

Example

:

"0x56687bf447db6ffa42ffe2204a05edaa20f55839"

​

market

string[]

The conditionId of the market in question. Supports multiple csv separated values. Cannot be used with the eventId param.

0x-prefixed 64-hex string

​

title

string

Filter by market title

Maximum length:

100

​

eventId

integer[]

The event id of the event in question. Supports multiple csv separated values. Returns positions for all markets for those event ids. Cannot be used with the market param.

​

limit

integer

default:

50

The max number of positions to return

Required range:

0 <= x <= 500

​

offset

integer

default:

0

The starting index for pagination

Required range:

0 <= x <= 10000

​

sortBy

enum<string>

default:

REALIZEDPNL

The sort criteria

Available options:

REALIZEDPNL

,

TITLE

,

PRICE

,

AVGPRICE

​

sortDirection

enum<string>

default:

DESC

The sort direction

Available options:

ASC

,

DESC

Response

200

application/json

Success

​

proxyWallet

string

User Profile Address (0x-prefixed, 40 hex chars)

Example

:

"0x56687bf447db6ffa42ffe2204a05edaa20f55839"

​

asset

string

​

conditionId

string

0x-prefixed 64-hex string

Example

:

"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"

​

avgPrice

number

​

totalBought

number

​

realizedPnl

number

​

curPrice

number

​

title

string

​

slug

string

​

icon

string

​

eventSlug

string

​

outcome

string

​

outcomeIndex

integer

​

oppositeOutcome

string

​

oppositeAsset

string

​

endDate

string

Get total value of a user's positions

Get total markets a user has traded

⌘

I