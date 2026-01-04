# Get user activity - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/core/get-user-activity

---

Get user activity - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Core

Get user activity

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

Get user activity

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://data-api.polymarket.com/activity

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

"timestamp"

:

123

,

"conditionId"

:

"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"

,

"type"

:

"TRADE"

,

"size"

:

123

,

"usdcSize"

:

123

,

"transactionHash"

:

"<string>"

,

"price"

:

123

,

"asset"

:

"<string>"

,

"side"

:

"BUY"

,

"outcomeIndex"

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

"name"

:

"<string>"

,

"pseudonym"

:

"<string>"

,

"bio"

:

"<string>"

,

"profileImage"

:

"<string>"

,

"profileImageOptimized"

:

"<string>"

}

]

GET

/

activity

Try it

Get user activity

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://data-api.polymarket.com/activity

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

"timestamp"

:

123

,

"conditionId"

:

"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"

,

"type"

:

"TRADE"

,

"size"

:

123

,

"usdcSize"

:

123

,

"transactionHash"

:

"<string>"

,

"price"

:

123

,

"asset"

:

"<string>"

,

"side"

:

"BUY"

,

"outcomeIndex"

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

"name"

:

"<string>"

,

"pseudonym"

:

"<string>"

,

"bio"

:

"<string>"

,

"profileImage"

:

"<string>"

,

"profileImageOptimized"

:

"<string>"

}

]

Query Parameters

​

limit

integer

default:

100

Required range:

0 <= x <= 500

​

offset

integer

default:

0

Required range:

0 <= x <= 10000

​

user

string

required

User Profile Address (0x-prefixed, 40 hex chars)

Example

:

"0x56687bf447db6ffa42ffe2204a05edaa20f55839"

​

market

string[]

Comma-separated list of condition IDs. Mutually exclusive with eventId.

0x-prefixed 64-hex string

​

eventId

integer[]

Comma-separated list of event IDs. Mutually exclusive with market.

​

type

enum<string>[]

Show

child attributes

​

start

integer

Required range:

x >= 0

​

end

integer

Required range:

x >= 0

​

sortBy

enum<string>

default:

TIMESTAMP

Available options:

TIMESTAMP

,

TOKENS

,

CASH

​

sortDirection

enum<string>

default:

DESC

Available options:

ASC

,

DESC

​

side

enum<string>

Available options:

BUY

,

SELL

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

timestamp

integer

​

conditionId

string

0x-prefixed 64-hex string

Example

:

"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"

​

type

enum<string>

Available options:

TRADE

,

SPLIT

,

MERGE

,

REDEEM

,

REWARD

,

CONVERSION

​

size

number

​

usdcSize

number

​

transactionHash

string

​

price

number

​

asset

string

​

side

enum<string>

Available options:

BUY

,

SELL

​

outcomeIndex

integer

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

name

string

​

pseudonym

string

​

bio

string

​

profileImage

string

​

profileImageOptimized

string

Get trades for a user or markets

Get top holders for markets

⌘

I