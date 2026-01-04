# Get total markets a user has traded - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/misc/get-total-markets-a-user-has-traded

---

Get total markets a user has traded - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Misc

Get total markets a user has traded

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

Get total markets a user has traded

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://data-api.polymarket.com/traded

200

400

401

500

Copy

Ask AI

{

"user"

:

"0x56687bf447db6ffa42ffe2204a05edaa20f55839"

,

"traded"

:

123

}

GET

/

traded

Try it

Get total markets a user has traded

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://data-api.polymarket.com/traded

200

400

401

500

Copy

Ask AI

{

"user"

:

"0x56687bf447db6ffa42ffe2204a05edaa20f55839"

,

"traded"

:

123

}

Query Parameters

​

user

string

required

User Profile Address (0x-prefixed, 40 hex chars)

Example

:

"0x56687bf447db6ffa42ffe2204a05edaa20f55839"

Response

200

application/json

Success

​

user

string

User Profile Address (0x-prefixed, 40 hex chars)

Example

:

"0x56687bf447db6ffa42ffe2204a05edaa20f55839"

​

traded

integer

Get closed positions for a user

Get open interest

⌘

I