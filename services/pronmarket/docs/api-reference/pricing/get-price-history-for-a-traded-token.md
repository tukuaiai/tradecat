# Get price history for a traded token - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/pricing/get-price-history-for-a-traded-token

---

Get price history for a traded token - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Pricing

Get price history for a traded token

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

GET

Get market price

GET

Get multiple market prices

POST

Get multiple market prices by request

GET

Get midpoint price

GET

Get price history for a traded token

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

Get price history for a traded token

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://clob.polymarket.com/prices-history

200

400

404

500

Copy

Ask AI

{

"history"

: [

{

"t"

:

1697875200

,

"p"

:

1800.75

}

]

}

GET

/

prices-history

Try it

Get price history for a traded token

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://clob.polymarket.com/prices-history

200

400

404

500

Copy

Ask AI

{

"history"

: [

{

"t"

:

1697875200

,

"p"

:

1800.75

}

]

}

Query Parameters

​

market

string

required

The CLOB token ID for which to fetch price history

​

startTs

number

The start time, a Unix timestamp in UTC

​

endTs

number

The end time, a Unix timestamp in UTC

​

interval

enum<string>

A string representing a duration ending at the current time. Mutually exclusive with startTs and endTs

Available options:

1m

,

1w

,

1d

,

6h

,

1h

,

max

​

fidelity

number

The resolution of the data, in minutes

Response

200

application/json

A list of timestamp/price pairs

​

history

object[]

required

Show

child attributes

Get midpoint price

Get bid-ask spreads

⌘

I