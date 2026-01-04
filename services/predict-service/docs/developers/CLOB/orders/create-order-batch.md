# Place Multiple Orders (Batching) - Polymarket Documentation

URL: https://docs.polymarket.com/developers/CLOB/orders/create-order-batch

---

Place Multiple Orders (Batching) - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Order Manipulation

Place Multiple Orders (Batching)

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

typescript

Example Payload

Copy

Ask AI

from

py_clob_client.client

import

ClobClient

from

py_clob_client.clob_types

import

OrderArgs, OrderType, PostOrdersArgs

from

py_clob_client.order_builder.constants

import

BUY

host:

str

=

"https://clob.polymarket.com"

key:

str

=

""

##This is your Private Key. Export from https://reveal.magic.link/polymarket or from your Web3 Application

chain_id:

int

=

137

#No need to adjust this

POLYMARKET_PROXY_ADDRESS

:

str

=

''

#This is the address listed below your profile picture when using the Polymarket site.

#Select from the following 3 initialization options to matches your login method, and remove any unused lines so only one client is initialized.

### Initialization of a client using a Polymarket Proxy associated with an Email/Magic account. If you login with your email use this example.

client

=

ClobClient(host,

key

=

key,

chain_id

=

chain_id,

signature_type

=

1

,

funder

=

POLYMARKET_PROXY_ADDRESS

)

### Initialization of a client using a Polymarket Proxy associated with a Browser Wallet(Metamask, Coinbase Wallet, etc)

client

=

ClobClient(host,

key

=

key,

chain_id

=

chain_id,

signature_type

=

2

,

funder

=

POLYMARKET_PROXY_ADDRESS

)

### Initialization of a client that trades directly from an EOA.

client

=

ClobClient(host,

key

=

key,

chain_id

=

chain_id)

## Create and sign a limit order buying 100 YES tokens for 0.50c each

#Refer to the Markets API documentation to locate a tokenID: https://docs.polymarket.com/developers/gamma-markets-api/get-markets

client.set_api_creds(client.create_or_derive_api_creds())

resp

=

client.post_orders([

PostOrdersArgs(

# Create and sign a limit order buying 100 YES tokens for 0.50 each

order

=

client.create_order(OrderArgs(

price

=

0.01

,

size

=

5

,

side

=

BUY

,

token_id

=

"88613172803544318200496156596909968959424174365708473463931555296257475886634"

,

)),

orderType

=

OrderType.

GTC

,

# Good 'Til Cancelled

),

PostOrdersArgs(

# Create and sign a limit order selling 200 NO tokens for 0.25 each

order

=

client.create_order(OrderArgs(

price

=

0.01

,

size

=

5

,

side

=

BUY

,

token_id

=

"93025177978745967226369398316375153283719303181694312089956059680730874301533"

,

)),

orderType

=

OrderType.

GTC

,

# Good 'Til Cancelled

)

])

print

(resp)

print

(

"Done!"

)

This endpoint requires a L2 Header

Polymarket’s CLOB supports batch orders, allowing you to place up to

15

orders in a single request. Before using this feature, make sure you’re comfortable placing a single order first. You can find the documentation for that

here.

HTTP REQUEST

POST /<clob-endpoint>/orders

​

Request Payload Parameters

Name

Required

Type

Description

PostOrder

yes

PostOrders[]

list of signed order objects (Signed Order + Order Type + Owner)

A

PostOrder

object is the form:

Name

Required

Type

Description

order

yes

order

See below table for details on crafting this object

orderType

yes

string

order type (“FOK”, “GTC”, “GTD”, “FAK”)

owner

yes

string

api key of order owner

An

order

object is the form:

Name

Required

Type

Description

salt

yes

integer

random salt used to create unique order

maker

yes

string

maker address (funder)

signer

yes

string

signing address

taker

yes

string

taker address (operator)

tokenId

yes

string

ERC1155 token ID of conditional token being traded

makerAmount

yes

string

maximum amount maker is willing to spend

takerAmount

yes

string

minimum amount taker will pay the maker in return

expiration

yes

string

unix expiration timestamp

nonce

yes

string

maker’s exchange nonce of the order is associated

feeRateBps

yes

string

fee rate basis points as required by the operator

side

yes

string

buy or sell enum index

signatureType

yes

integer

signature type enum index

signature

yes

string

hex encoded signature

​

Order types

FOK

: A Fill-Or-Kill order is an market order to buy (in dollars) or sell (in shares) shares that must be executed immediately in its entirety; otherwise, the entire order will be cancelled.

FAK

: A Fill-And-Kill order is a market order to buy (in dollars) or sell (in shares) that will be executed immediately for as many shares as are available; any portion not filled at once is cancelled.

GTC

: A Good-Til-Cancelled order is a limit order that is active until it is fulfilled or cancelled.

GTD

: A Good-Til-Date order is a type of order that is active until its specified date (UTC seconds timestamp), unless it has already been fulfilled or cancelled. There is a security threshold of one minute. If the order needs to expire in 90 seconds the correct expiration value is: now + 1 minute + 30 seconds

​

Response Format

Name

Type

Description

success

boolean

boolean indicating if server-side err (

success = false

) -> server-side error

errorMsg

string

error message in case of unsuccessful placement (in case

success = false

, e.g.

client-side error

, the reason is in

errorMsg

)

orderId

string

id of order

orderHashes

string[]

hash of settlement transaction order was marketable and triggered a match

​

Insert Error Messages

If the

errorMsg

field of the response object from placement is not an empty string, the order was not able to be immediately placed. This might be because of a delay or because of a failure. If the

success

is not

true

, then there was an issue placing the order. The following

errorMessages

are possible:

​

Error

Error

Success

Message

Description

INVALID_ORDER_MIN_TICK_SIZE

yes

order is invalid. Price breaks minimum tick size rules

order price isn’t accurate to correct tick sizing

INVALID_ORDER_MIN_SIZE

yes

order is invalid. Size lower than the minimum

order size must meet min size threshold requirement

INVALID_ORDER_DUPLICATED

yes

order is invalid. Duplicated. Same order has already been placed, can’t be placed again

INVALID_ORDER_NOT_ENOUGH_BALANCE

yes

not enough balance / allowance

funder address doesn’t have sufficient balance or allowance for order

INVALID_ORDER_EXPIRATION

yes

invalid expiration

expiration field expresses a time before now

INVALID_ORDER_ERROR

yes

could not insert order

system error while inserting order

EXECUTION_ERROR

yes

could not run the execution

system error while attempting to execute trade

ORDER_DELAYED

no

order match delayed due to market conditions

order placement delayed

DELAYING_ORDER_ERROR

yes

error delaying the order

system error while delaying order

FOK_ORDER_NOT_FILLED_ERROR

yes

order couldn’t be fully filled, FOK orders are fully filled/killed

FOK order not fully filled so can’t be placed

MARKET_NOT_READY

no

the market is not yet ready to process new orders

system not accepting orders for market yet

​

Insert Statuses

When placing an order, a status field is included. The status field provides additional information regarding the order’s state as a result of the placement. Possible values include:

​

Status

Status

Description

matched

order placed and matched with an existing resting order

live

order placed and resting on the book

delayed

order marketable, but subject to matching delay

unmatched

order marketable, but failure delaying, placement successful

Python

typescript

Example Payload

Copy

Ask AI

from

py_clob_client.client

import

ClobClient

from

py_clob_client.clob_types

import

OrderArgs, OrderType, PostOrdersArgs

from

py_clob_client.order_builder.constants

import

BUY

host:

str

=

"https://clob.polymarket.com"

key:

str

=

""

##This is your Private Key. Export from https://reveal.magic.link/polymarket or from your Web3 Application

chain_id:

int

=

137

#No need to adjust this

POLYMARKET_PROXY_ADDRESS

:

str

=

''

#This is the address listed below your profile picture when using the Polymarket site.

#Select from the following 3 initialization options to matches your login method, and remove any unused lines so only one client is initialized.

### Initialization of a client using a Polymarket Proxy associated with an Email/Magic account. If you login with your email use this example.

client

=

ClobClient(host,

key

=

key,

chain_id

=

chain_id,

signature_type

=

1

,

funder

=

POLYMARKET_PROXY_ADDRESS

)

### Initialization of a client using a Polymarket Proxy associated with a Browser Wallet(Metamask, Coinbase Wallet, etc)

client

=

ClobClient(host,

key

=

key,

chain_id

=

chain_id,

signature_type

=

2

,

funder

=

POLYMARKET_PROXY_ADDRESS

)

### Initialization of a client that trades directly from an EOA.

client

=

ClobClient(host,

key

=

key,

chain_id

=

chain_id)

## Create and sign a limit order buying 100 YES tokens for 0.50c each

#Refer to the Markets API documentation to locate a tokenID: https://docs.polymarket.com/developers/gamma-markets-api/get-markets

client.set_api_creds(client.create_or_derive_api_creds())

resp

=

client.post_orders([

PostOrdersArgs(

# Create and sign a limit order buying 100 YES tokens for 0.50 each

order

=

client.create_order(OrderArgs(

price

=

0.01

,

size

=

5

,

side

=

BUY

,

token_id

=

"88613172803544318200496156596909968959424174365708473463931555296257475886634"

,

)),

orderType

=

OrderType.

GTC

,

# Good 'Til Cancelled

),

PostOrdersArgs(

# Create and sign a limit order selling 200 NO tokens for 0.25 each

order

=

client.create_order(OrderArgs(

price

=

0.01

,

size

=

5

,

side

=

BUY

,

token_id

=

"93025177978745967226369398316375153283719303181694312089956059680730874301533"

,

)),

orderType

=

OrderType.

GTC

,

# Good 'Til Cancelled

)

])

print

(resp)

print

(

"Done!"

)

Place Single Order

Get Order

⌘

I