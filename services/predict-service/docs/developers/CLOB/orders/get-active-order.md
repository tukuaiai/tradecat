# Get Active Orders - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CLOB/orders/get-active-order

---

Get Active Orders - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Order Manipulation

Get Active Orders

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

from

py_clob_client.clob_types

import

OpenOrderParams

resp

=

client.get_orders(

OpenOrderParams(

market

=

"0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af"

,

)

)

print

(resp)

print

(

"Done!"

)

This endpoint requires a L2 Header.

Get active order(s) for a specific market.

HTTP REQUEST

GET /<clob-endpoint>/data/orders

​

Request Parameters

Name

Required

Type

Description

id

no

string

id of order to get information about

market

no

string

condition id of market

asset_id

no

string

id of the asset/token

​

Response Format

Name

Type

Description

null

OpenOrder[]

list of open orders filtered by the query parameters

Python

Typescript

Copy

Ask AI

from

py_clob_client.clob_types

import

OpenOrderParams

resp

=

client.get_orders(

OpenOrderParams(

market

=

"0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af"

,

)

)

print

(resp)

print

(

"Done!"

)

Get Order

Check Order Reward Scoring

⌘

I