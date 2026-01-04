# Get open interest - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/misc/get-open-interest

---

Get open interest - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Misc

Get open interest

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

Misc

GET

Get total markets a user has traded

GET

Get open interest

GET

Get live volume for an event

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

Get open interest

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://data-api.polymarket.com/oi

200

400

500

Copy

Ask AI

[

{

"market"

:

"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"

,

"value"

:

123

}

]

GET

/

oi

Try it

Get open interest

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://data-api.polymarket.com/oi

200

400

500

Copy

Ask AI

[

{

"market"

:

"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"

,

"value"

:

123

}

]

Query Parameters

​

market

string[]

0x-prefixed 64-hex string

Response

200

application/json

Success

​

market

string

0x-prefixed 64-hex string

Example

:

"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"

​

value

number

Get total markets a user has traded

Get live volume for an event

⌘

I