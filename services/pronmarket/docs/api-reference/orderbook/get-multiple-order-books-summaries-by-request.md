# Get multiple order books summaries by request - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/orderbook/get-multiple-order-books-summaries-by-request

---

Get multiple order books summaries by request - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Orderbook

Get multiple order books summaries by request

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

GET

Get order book summary

POST

Get multiple order books summaries by request

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

Get multiple order books summaries by request

cURL

Copy

Ask AI

curl

--request

POST

\

--url

https://clob.polymarket.com/books

\

--header

'Content-Type: application/json'

\

--data

'[

{

"token_id": "1234567890"

},

{

"token_id": "0987654321"

}

]'

200

example

Copy

Ask AI

[

{

"market"

:

"0x1b6f76e5b8587ee896c35847e12d11e75290a8c3934c5952e8a9d6e4c6f03cfa"

,

"asset_id"

:

"1234567890"

,

"timestamp"

:

"2023-10-01T12:00:00Z"

,

"hash"

:

"0xabc123def456..."

,

"bids"

: [

{

"price"

:

"1800.50"

,

"size"

:

"10.5"

}

],

"asks"

: [

{

"price"

:

"1800.50"

,

"size"

:

"10.5"

}

],

"min_order_size"

:

"0.001"

,

"tick_size"

:

"0.01"

,

"neg_risk"

:

false

}

]

POST

/

books

Try it

Get multiple order books summaries by request

cURL

Copy

Ask AI

curl

--request

POST

\

--url

https://clob.polymarket.com/books

\

--header

'Content-Type: application/json'

\

--data

'[

{

"token_id": "1234567890"

},

{

"token_id": "0987654321"

}

]'

200

example

Copy

Ask AI

[

{

"market"

:

"0x1b6f76e5b8587ee896c35847e12d11e75290a8c3934c5952e8a9d6e4c6f03cfa"

,

"asset_id"

:

"1234567890"

,

"timestamp"

:

"2023-10-01T12:00:00Z"

,

"hash"

:

"0xabc123def456..."

,

"bids"

: [

{

"price"

:

"1800.50"

,

"size"

:

"10.5"

}

],

"asks"

: [

{

"price"

:

"1800.50"

,

"size"

:

"10.5"

}

],

"min_order_size"

:

"0.001"

,

"tick_size"

:

"0.01"

,

"neg_risk"

:

false

}

]

Body

application/json · object[]

​

token_id

string

required

The unique identifier for the token

Example

:

"1234567890"

​

side

enum<string>

Optional side parameter for certain operations

Available options:

BUY

,

SELL

Example

:

"BUY"

Response

200

application/json

Successful response

​

market

string

required

Market identifier

Example

:

"0x1b6f76e5b8587ee896c35847e12d11e75290a8c3934c5952e8a9d6e4c6f03cfa"

​

asset_id

string

required

Asset identifier

Example

:

"1234567890"

​

timestamp

string<date-time>

required

Timestamp of the order book snapshot

Example

:

"2023-10-01T12:00:00Z"

​

hash

string

required

Hash of the order book state

Example

:

"0xabc123def456..."

​

bids

object[]

required

Array of bid levels

Show

child attributes

​

asks

object[]

required

Array of ask levels

Show

child attributes

​

min_order_size

string

required

Minimum order size for this market

Example

:

"0.001"

​

tick_size

string

required

Minimum price increment

Example

:

"0.01"

​

neg_risk

boolean

required

Whether negative risk is enabled

Example

:

false

Get order book summary

Get market price

⌘

I