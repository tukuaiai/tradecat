# Get Trades - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CLOB/trades/trades

---

Get Trades - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Trades

Get Trades

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

TradeParams

resp

=

client.get_trades(

TradeParams(

maker_address

=

client.get_address(),

market

=

"0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af"

,

),

)

print

(resp)

print

(

"Done!"

)

This endpoint requires a L2 Header.

Get trades for the authenticated user based on the provided filters.

HTTP REQUEST

GET /<clob-endpoint>/data/trades

​

Request Parameters

Name

Required

Type

Description

id

no

string

id of trade to fetch

taker

no

string

address to get trades for where it is included as a taker

maker

no

string

address to get trades for where it is included as a maker

market

no

string

market for which to get the trades (condition ID)

before

no

string

unix timestamp representing the cutoff up to which trades that happened before then can be included

after

no

string

unix timestamp representing the cutoff for which trades that happened after can be included

​

Response Format

Name

Type

Description

null

Trade[]

list of trades filtered by query parameters

A

Trade

object is of the form:

Name

Type

Description

id

string

trade id

taker_order_id

string

hash of taker order (market order) that catalyzed the trade

market

string

market id (condition id)

asset_id

string

asset id (token id) of taker order (market order)

side

string

buy or sell

size

string

size

fee_rate_bps

string

the fees paid for the taker order expressed in basic points

price

string

limit price of taker order

status

string

trade status (see above)

match_time

string

time at which the trade was matched

last_update

string

timestamp of last status update

outcome

string

human readable outcome of the trade

maker_address

string

funder address of the taker of the trade

owner

string

api key of taker of the trade

transaction_hash

string

hash of the transaction where the trade was executed

bucket_index

integer

index of bucket for trade in case trade is executed in multiple transactions

maker_orders

MakerOrder[]

list of the maker trades the taker trade was filled against

type

string

side of the trade: TAKER or MAKER

A

MakerOrder

object is of the form:

Name

Type

Description

order_id

string

id of maker order

maker_address

string

maker address of the order

owner

string

api key of the owner of the order

matched_amount

string

size of maker order consumed with this trade

fee_rate_bps

string

the fees paid for the taker order expressed in basic points

price

string

price of maker order

asset_id

string

token/asset id

outcome

string

human readable outcome of the maker order

side

string

the side of the maker order. Can be

buy

or

sell

Python

Typescript

Copy

Ask AI

from

py_clob_client.clob_types

import

TradeParams

resp

=

client.get_trades(

TradeParams(

maker_address

=

client.get_address(),

market

=

"0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af"

,

),

)

print

(resp)

print

(

"Done!"

)

Trades Overview

WSS Overview

⌘

I