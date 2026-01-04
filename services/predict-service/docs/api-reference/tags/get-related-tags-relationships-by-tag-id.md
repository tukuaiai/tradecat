# Get related tags (relationships) by tag id - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/tags/get-related-tags-relationships-by-tag-id

---

Get related tags (relationships) by tag id - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Tags

Get related tags (relationships) by tag id

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

GET

List tags

GET

Get tag by id

GET

Get tag by slug

GET

Get related tags (relationships) by tag id

GET

Get related tags (relationships) by tag slug

GET

Get tags related to a tag id

GET

Get tags related to a tag slug

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

Get related tags (relationships) by tag id

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/tags/{id}/related-tags

200

Copy

Ask AI

[

{

"id"

:

"<string>"

,

"tagID"

:

123

,

"relatedTagID"

:

123

,

"rank"

:

123

}

]

GET

/

tags

/

{id}

/

related-tags

Try it

Get related tags (relationships) by tag id

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/tags/{id}/related-tags

200

Copy

Ask AI

[

{

"id"

:

"<string>"

,

"tagID"

:

123

,

"relatedTagID"

:

123

,

"rank"

:

123

}

]

Path Parameters

​

id

integer

required

Query Parameters

​

omit_empty

boolean

​

status

enum<string>

Available options:

active

,

closed

,

all

Response

200 - application/json

Related tag relationships

​

id

string

​

tagID

integer | null

​

relatedTagID

integer | null

​

rank

integer | null

Get tag by slug

Get related tags (relationships) by tag slug

⌘

I