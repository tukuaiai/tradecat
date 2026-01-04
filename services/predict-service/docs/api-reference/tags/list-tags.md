# List tags - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/tags/list-tags

---

List tags - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Tags

List tags

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

List tags

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/tags

200

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

tags

Try it

List tags

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/tags

200

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

Query Parameters

​

limit

integer

Required range:

x >= 0

​

offset

integer

Required range:

x >= 0

​

order

string

Comma-separated list of fields to order by

​

ascending

boolean

​

include_template

boolean

​

is_carousel

boolean

Response

200 - application/json

List of tags

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

Get sports metadata information

Get tag by id

⌘

I