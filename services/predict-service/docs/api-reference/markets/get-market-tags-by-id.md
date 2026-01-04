# Get market tags by id - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/markets/get-market-tags-by-id

---

Get market tags by id - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Markets

Get market tags by id

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

GET

List markets

GET

Get market by id

GET

Get market tags by id

GET

Get market by slug

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

Get market tags by id

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/markets/{id}/tags

200

404

Copy

Ask AI

[

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"slug"

:

"<string>"

,

"forceShow"

:

true

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

123

,

"updatedBy"

:

123

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"forceHide"

:

true

,

"isCarousel"

:

true

}

]

GET

/

markets

/

{id}

/

tags

Try it

Get market tags by id

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/markets/{id}/tags

200

404

Copy

Ask AI

[

{

"id"

:

"<string>"

,

"label"

:

"<string>"

,

"slug"

:

"<string>"

,

"forceShow"

:

true

,

"publishedAt"

:

"<string>"

,

"createdBy"

:

123

,

"updatedBy"

:

123

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

,

"forceHide"

:

true

,

"isCarousel"

:

true

}

]

Path Parameters

​

id

integer

required

Response

200

application/json

Tags attached to the market

​

id

string

​

label

string | null

​

slug

string | null

​

forceShow

boolean | null

​

publishedAt

string | null

​

createdBy

integer | null

​

updatedBy

integer | null

​

createdAt

string<date-time> | null

​

updatedAt

string<date-time> | null

​

forceHide

boolean | null

​

isCarousel

boolean | null

Get market by id

Get market by slug

⌘

I