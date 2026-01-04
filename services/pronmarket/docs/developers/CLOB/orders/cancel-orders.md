# Cancel Orders(s) - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CLOB/orders/cancel-orders

---

Cancel Orders(s) - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Order Manipulation

Cancel Orders(s)

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

On this page

Cancel an single Order

Request Payload Parameters

Response Format

Cancel Multiple Orders

Request Payload Parameters

Response Format

Cancel ALL Orders

Response Format

Cancel orders from market

Request Payload Parameters

Response Format

​

Cancel an single Order

This endpoint requires a L2 Header.

Cancel an order.

HTTP REQUEST

DELETE /<clob-endpoint>/order

​

Request Payload Parameters

Name

Required

Type

Description

orderID

yes

string

ID of order to cancel

​

Response Format

Name

Type

Description

canceled

string[]

list of canceled orders

not_canceled

a order id -> reason map that explains why that order couldn’t be canceled

Python

Typescript

Copy

Ask AI

resp

=

client.cancel(

order_id

=

"0x38a73eed1e6d177545e9ab027abddfb7e08dbe975fa777123b1752d203d6ac88"

)

print

(resp)

​

Cancel Multiple Orders

This endpoint requires a L2 Header.

HTTP REQUEST

DELETE /<clob-endpoint>/orders

​

Request Payload Parameters

Name

Required

Type

Description

null

yes

string[]

IDs of the orders to cancel

​

Response Format

Name

Type

Description

canceled

string[]

list of canceled orders

not_canceled

a order id -> reason map that explains why that order couldn’t be canceled

Python

Typescript

Copy

Ask AI

resp

=

client.cancel_orders([

"0x38a73eed1e6d177545e9ab027abddfb7e08dbe975fa777123b1752d203d6ac88"

,

"0xaaaa..."

])

print

(resp)

​

Cancel ALL Orders

This endpoint requires a L2 Header.

Cancel all open orders posted by a user.

HTTP REQUEST

DELETE /<clob-endpoint>/cancel-all

​

Response Format

Name

Type

Description

canceled

string[]

list of canceled orders

not_canceled

a order id -> reason map that explains why that order couldn’t be canceled

Python

Typescript

Copy

Ask AI

resp

=

client.cancel_all()

print

(resp)

print

(

"Done!"

)

​

Cancel orders from market

This endpoint requires a L2 Header.

Cancel orders from market.

HTTP REQUEST

DELETE /<clob-endpoint>/cancel-market-orders

​

Request Payload Parameters

Name

Required

Type

Description

market

no

string

condition id of the market

asset_id

no

string

id of the asset/token

​

Response Format

Name

Type

Description

canceled

string[]

list of canceled orders

not_canceled

a order id -> reason map that explains why that order couldn’t be canceled

Python

Typescript

Copy

Ask AI

resp

=

client.cancel_market_orders(

market

=

"0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af"

,

asset_id

=

"52114319501245915516055106046884209969926127482827954674443846427813813222426"

)

print

(resp)

Check Order Reward Scoring

Onchain Order Info

⌘

I