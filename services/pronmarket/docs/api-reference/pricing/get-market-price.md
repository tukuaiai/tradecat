# Get market price - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/pricing/get-market-price

---

Get market price - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Pricing

Get market price

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

Get market price

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://clob.polymarket.com/price

200

example

Copy

Ask AI

{

"price"

:

"1800.50"

}

GET

/

price

Try it

Get market price

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://clob.polymarket.com/price

200

example

Copy

Ask AI

{

"price"

:

"1800.50"

}

Query Parameters

​

token_id

string

required

The unique identifier for the token

​

side

enum<string>

required

The side of the market (BUY or SELL)

Available options:

BUY

,

SELL

Response

200

application/json

Successful response

​

price

string

required

The market price (as string to maintain precision)

Example

:

"1800.50"

Get multiple order books summaries by request

Get multiple market prices

⌘

I