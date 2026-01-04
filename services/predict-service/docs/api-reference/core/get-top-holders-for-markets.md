# Get top holders for markets - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/core/get-top-holders-for-markets

---

Get top holders for markets - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Core

Get top holders for markets

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

Get top holders for markets

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://data-api.polymarket.com/holders

200

400

401

500

Copy

Ask AI

[

{

"token"

:

"<string>"

,

"holders"

: [

{

"proxyWallet"

:

"0x56687bf447db6ffa42ffe2204a05edaa20f55839"

,

"bio"

:

"<string>"

,

"asset"

:

"<string>"

,

"pseudonym"

:

"<string>"

,

"amount"

:

123

,

"displayUsernamePublic"

:

true

,

"outcomeIndex"

:

123

,

"name"

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

}

]

GET

/

holders

Try it

Get top holders for markets

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://data-api.polymarket.com/holders

200

400

401

500

Copy

Ask AI

[

{

"token"

:

"<string>"

,

"holders"

: [

{

"proxyWallet"

:

"0x56687bf447db6ffa42ffe2204a05edaa20f55839"

,

"bio"

:

"<string>"

,

"asset"

:

"<string>"

,

"pseudonym"

:

"<string>"

,

"amount"

:

123

,

"displayUsernamePublic"

:

true

,

"outcomeIndex"

:

123

,

"name"

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

market

string[]

required

Comma-separated list of condition IDs.

0x-prefixed 64-hex string

​

minBalance

integer

default:

1

Required range:

0 <= x <= 999999

Response

200

application/json

Success

​

token

string

​

holders

object[]

Show

child attributes

Get user activity

Get total value of a user's positions

⌘

I