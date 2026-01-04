# List teams - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/sports/list-teams

---

List teams - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Sports

List teams

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

GET

List teams

GET

Get sports metadata information

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

List teams

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/teams

200

Copy

Ask AI

[

{

"id"

:

123

,

"name"

:

"<string>"

,

"league"

:

"<string>"

,

"record"

:

"<string>"

,

"logo"

:

"<string>"

,

"abbreviation"

:

"<string>"

,

"alias"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

}

]

GET

/

teams

Try it

List teams

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/teams

200

Copy

Ask AI

[

{

"id"

:

123

,

"name"

:

"<string>"

,

"league"

:

"<string>"

,

"record"

:

"<string>"

,

"logo"

:

"<string>"

,

"abbreviation"

:

"<string>"

,

"alias"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"updatedAt"

:

"2023-11-07T05:31:56Z"

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

league

string[]

​

name

string[]

​

abbreviation

string[]

Response

200 - application/json

List of teams

​

id

integer

​

name

string | null

​

league

string | null

​

record

string | null

​

logo

string | null

​

abbreviation

string | null

​

alias

string | null

​

createdAt

string<date-time> | null

​

updatedAt

string<date-time> | null

Health check

Get sports metadata information

⌘

I