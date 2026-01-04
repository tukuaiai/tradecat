# User Channel - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CLOB/websocket/user-channel

---

User Channel - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Websocket

User Channel

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

Trade Message

Structure

Order Message

Structure

Authenticated channel for updates related to user activities (orders, trades), filtered for authenticated user by apikey.

SUBSCRIBE

<wss-channel> user

​

Trade Message

Emitted when:

when a market order is matched (“MATCHED”)

when a limit order for the user is included in a trade (“MATCHED”)

subsequent status changes for trade (“MINED”, “CONFIRMED”, “RETRYING”, “FAILED”)

​

Structure

Name

Type

Description

asset_id

string

asset id (token ID) of order (market order)

event_type

string

”trade”

id

string

trade id

last_update

string

time of last update to trade

maker_orders

MakerOrder[]

array of maker order details

market

string

market identifier (condition ID)

matchtime

string

time trade was matched

outcome

string

outcome

owner

string

api key of event owner

price

string

price

side

string

BUY/SELL

size

string

size

status

string

trade status

taker_order_id

string

id of taker order

timestamp

string

time of event

trade_owner

string

api key of trade owner

type

string

”TRADE”

Where a

MakerOrder

object is of the form:

Name

Type

Description

asset_id

string

asset of the maker order

matched_amount

string

amount of maker order matched in trade

order_id

string

maker order ID

outcome

string

outcome

owner

string

owner of maker order

price

string

price of maker order

Response

Copy

Ask AI

{

"asset_id"

:

"52114319501245915516055106046884209969926127482827954674443846427813813222426"

,

"event_type"

:

"trade"

,

"id"

:

"28c4d2eb-bbea-40e7-a9f0-b2fdb56b2c2e"

,

"last_update"

:

"1672290701"

,

"maker_orders"

: [

{

"asset_id"

:

"52114319501245915516055106046884209969926127482827954674443846427813813222426"

,

"matched_amount"

:

"10"

,

"order_id"

:

"0xff354cd7ca7539dfa9c28d90943ab5779a4eac34b9b37a757d7b32bdfb11790b"

,

"outcome"

:

"YES"

,

"owner"

:

"9180014b-33c8-9240-a14b-bdca11c0a465"

,

"price"

:

"0.57"

}

],

"market"

:

"0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af"

,

"matchtime"

:

"1672290701"

,

"outcome"

:

"YES"

,

"owner"

:

"9180014b-33c8-9240-a14b-bdca11c0a465"

,

"price"

:

"0.57"

,

"side"

:

"BUY"

,

"size"

:

"10"

,

"status"

:

"MATCHED"

,

"taker_order_id"

:

"0x06bc63e346ed4ceddce9efd6b3af37c8f8f440c92fe7da6b2d0f9e4ccbc50c42"

,

"timestamp"

:

"1672290701"

,

"trade_owner"

:

"9180014b-33c8-9240-a14b-bdca11c0a465"

,

"type"

:

"TRADE"

}

​

Order Message

Emitted when:

When an order is placed (PLACEMENT)

When an order is updated (some of it is matched) (UPDATE)

When an order is canceled (CANCELLATION)

​

Structure

Name

Type

Description

asset_id

string

asset ID (token ID) of order

associate_trades

string[]

array of ids referencing trades that the order has been included in

event_type

string

”order”

id

string

order id

market

string

condition ID of market

order_owner

string

owner of order

original_size

string

original order size

outcome

string

outcome

owner

string

owner of orders

price

string

price of order

side

string

BUY/SELL

size_matched

string

size of order that has been matched

timestamp

string

time of event

type

string

PLACEMENT/UPDATE/CANCELLATION

Response

Copy

Ask AI

{

"asset_id"

:

"52114319501245915516055106046884209969926127482827954674443846427813813222426"

,

"associate_trades"

:

null

,

"event_type"

:

"order"

,

"id"

:

"0xff354cd7ca7539dfa9c28d90943ab5779a4eac34b9b37a757d7b32bdfb11790b"

,

"market"

:

"0xbd31dc8a20211944f6b70f31557f1001557b59905b7738480ca09bd4532f84af"

,

"order_owner"

:

"9180014b-33c8-9240-a14b-bdca11c0a465"

,

"original_size"

:

"10"

,

"outcome"

:

"YES"

,

"owner"

:

"9180014b-33c8-9240-a14b-bdca11c0a465"

,

"price"

:

"0.57"

,

"side"

:

"SELL"

,

"size_matched"

:

"0"

,

"timestamp"

:

"1672290687"

,

"type"

:

"PLACEMENT"

}

WSS Authentication

Market Channel

⌘

I