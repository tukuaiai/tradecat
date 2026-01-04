# Get bid-ask spreads - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/spreads/get-bid-ask-spreads

---

Get bid-ask spreads - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Spreads

Get bid-ask spreads

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

POST

Get bid-ask spreads

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

Get bid-ask spreads

cURL

Copy

Ask AI

curl

--request

POST

\

--url

https://clob.polymarket.com/spreads

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

{

"1234567890"

:

"0.50"

,

"0987654321"

:

"0.05"

}

POST

/

spreads

Try it

Get bid-ask spreads

cURL

Copy

Ask AI

curl

--request

POST

\

--url

https://clob.polymarket.com/spreads

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

{

"1234567890"

:

"0.50"

,

"0987654321"

:

"0.05"

}

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

Map of token_id to spread value

​

{key}

string

Get price history for a traded token

Orders Overview

⌘

I