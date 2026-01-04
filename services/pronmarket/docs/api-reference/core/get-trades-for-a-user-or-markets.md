# Get trades for a user or markets - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/core/get-trades-for-a-user-or-markets

---

Get trades for a user or markets - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Core

Get trades for a user or markets

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

Get trades for a user or markets

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://data-api.polymarket.com/trades

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

"side"

:

"BUY"

,

"asset"

:

"<string>"

,

"conditionId"

:

"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"

,

"size"

:

123

,

"price"

:

123

,

"timestamp"

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

,

"transactionHash"

:

"<string>"

}

]

GET

/

trades

Try it

Get trades for a user or markets

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://data-api.polymarket.com/trades

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

"side"

:

"BUY"

,

"asset"

:

"<string>"

,

"conditionId"

:

"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"

,

"size"

:

123

,

"price"

:

123

,

"timestamp"

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

,

"transactionHash"

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

0 <= x <= 10000

​

offset

integer

default:

0

Required range:

0 <= x <= 10000

​

takerOnly

boolean

default:

true

​

filterType

enum<string>

Must be provided together with filterAmount.

Available options:

CASH

,

TOKENS

​

filterAmount

number

Must be provided together with filterType.

Required range:

x >= 0

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

user

string

User Profile Address (0x-prefixed, 40 hex chars)

Example

:

"0x56687bf447db6ffa42ffe2204a05edaa20f55839"

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

side

enum<string>

Available options:

BUY

,

SELL

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

size

number

​

price

number

​

timestamp

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

outcomeIndex

integer

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

​

transactionHash

string

Get current positions for a user

Get user activity

⌘

I