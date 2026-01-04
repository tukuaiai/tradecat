# Check Order Reward Scoring - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CLOB/orders/check-scoring

---

Check Order Reward Scoring - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Order Manipulation

Check Order Reward Scoring

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

Python

Typescript

Copy

Ask AI

scoring

=

client.is_order_scoring(

OrderScoringParams(

orderId

=

"0x..."

)

)

print

(scoring)

scoring

=

client.are_orders_scoring(

OrdersScoringParams(

orderIds

=

[

"0x..."

]

)

)

print

(scoring)

This endpoint requires a L2 Header.

Returns a boolean value where it is indicated if an order is scoring or not.

HTTP REQUEST

GET /<clob-endpoint>/order-scoring?order_id={...}

​

Request Parameters

Name

Required

Type

Description

orderId

yes

string

id of order to get information about

​

Response Format

Name

Type

Description

null

OrdersScoring

order scoring data

An

OrdersScoring

object is of the form:

Name

Type

Description

scoring

boolean

indicates if the order is scoring or not

​

Check if some orders are scoring

This endpoint requires a L2 Header.

Returns to a dictionary with boolean value where it is indicated if an order is scoring or not.

HTTP REQUEST

POST /<clob-endpoint>/orders-scoring

​

Request Parameters

Name

Required

Type

Description

orderIds

yes

string[]

ids of the orders to get information about

​

Response Format

Name

Type

Description

null

OrdersScoring

orders scoring data

An

OrdersScoring

object is a dictionary that indicates the order by if it score.

Python

Typescript

Copy

Ask AI

scoring

=

client.is_order_scoring(

OrderScoringParams(

orderId

=

"0x..."

)

)

print

(scoring)

scoring

=

client.are_orders_scoring(

OrdersScoringParams(

orderIds

=

[

"0x..."

]

)

)

print

(scoring)

Get Active Orders

Cancel Orders(s)

⌘

I