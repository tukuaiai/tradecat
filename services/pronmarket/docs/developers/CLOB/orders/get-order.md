# Get Order - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CLOB/orders/get-order

---

Get Order - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Order Manipulation

Get Order

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

order

=

clob_client.get_order(

"0xb816482a5187a3d3db49cbaf6fe3ddf24f53e6c712b5a4bf5e01d0ec7b11dabc"

)

print

(order)

This endpoint requires a L2 Header.

Get single order by id.

HTTP REQUEST

GET /<clob-endpoint>/data/order/<order_hash>

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

​

Response Format

Name

Type

Description

order

OpenOrder

order if it exists

An

OpenOrder

object is of the form:

Name

Type

Description

associate_trades

string[]

any Trade id the order has been partially included in

id

string

order id

status

string

order current status

market

string

market id (condition id)

original_size

string

original order size at placement

outcome

string

human readable outcome the order is for

maker_address

string

maker address (funder)

owner

string

api key

price

string

price

side

string

buy or sell

size_matched

string

size of order that has been matched/filled

asset_id

string

token id

expiration

string

unix timestamp when the order expired, 0 if it does not expire

type

string

order type (GTC, FOK, GTD)

created_at

string

unix timestamp when the order was created

Python

Typescript

Copy

Ask AI

order

=

clob_client.get_order(

"0xb816482a5187a3d3db49cbaf6fe3ddf24f53e6c712b5a4bf5e01d0ec7b11dabc"

)

print

(order)

Place Multiple Orders (Batching)

Get Active Orders

⌘

I