# Get multiple market prices - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/pricing/get-multiple-market-prices

---

Get multiple market prices - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Pricing

Get multiple market prices

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

Get multiple market prices

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://clob.polymarket.com/prices

200

400

500

Copy

Ask AI

{

"1234567890"

: {

"BUY"

:

"1800.50"

,

"SELL"

:

"1801.00"

},

"0987654321"

: {

"BUY"

:

"50.25"

,

"SELL"

:

"50.30"

}

}

GET

/

prices

Try it

Get multiple market prices

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://clob.polymarket.com/prices

200

400

500

Copy

Ask AI

{

"1234567890"

: {

"BUY"

:

"1800.50"

,

"SELL"

:

"1801.00"

},

"0987654321"

: {

"BUY"

:

"50.25"

,

"SELL"

:

"50.30"

}

}

Response

200

application/json

Successful response

Map of token_id to side to price

​

{key}

object

Show

child attributes

Get market price

Get multiple market prices by request

⌘

I