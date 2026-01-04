# Get sports metadata information - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/sports/get-sports-metadata-information

---

Get sports metadata information - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Sports

Get sports metadata information

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

Get sports metadata information

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/sports

200

Copy

Ask AI

[

{

"sport"

:

"<string>"

,

"image"

:

"<string>"

,

"resolution"

:

"<string>"

,

"ordering"

:

"<string>"

,

"tags"

:

"<string>"

,

"series"

:

"<string>"

}

]

GET

/

sports

Try it

Get sports metadata information

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/sports

200

Copy

Ask AI

[

{

"sport"

:

"<string>"

,

"image"

:

"<string>"

,

"resolution"

:

"<string>"

,

"ordering"

:

"<string>"

,

"tags"

:

"<string>"

,

"series"

:

"<string>"

}

]

Response

200 - application/json

List of sports metadata objects containing sport configuration details, visual assets, and related identifiers

​

sport

string

The sport identifier or abbreviation

​

image

string<uri>

URL to the sport's logo or image asset

​

resolution

string<uri>

URL to the official resolution source for the sport (e.g., league website)

​

ordering

string

Preferred ordering for sport display, typically "home" or "away"

​

tags

string

Comma-separated list of tag IDs associated with the sport for categorization and filtering

​

series

string

Series identifier linking the sport to a specific tournament or season series

List teams

List tags

⌘

I