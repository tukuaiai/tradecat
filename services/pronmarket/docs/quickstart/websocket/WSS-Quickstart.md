# WSS Quickstart - Polymarket Documentation

URL: https://docs.polymarket.com/quickstart/websocket/WSS-Quickstart

---

WSS Quickstart - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Websocket

WSS Quickstart

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

Getting your API Keys

Using those keys to connect to the Market or User Websocket

The following code samples and explanation will show you how to subsribe to the Marker and User channels of the Websocket.

You’ll need your API keys to do this so we’ll start with that.

​

Getting your API Keys

DeriveAPIKeys-Python

DeriveAPIKeys-TS

Copy

Ask AI

from

py_clob_client.client

import

ClobClient

host:

str

=

"https://clob.polymarket.com"

key:

str

=

""

#This is your Private Key. If using email login export from https://reveal.magic.link/polymarket otherwise export from your Web3 Application

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

#This is the address you deposit/send USDC to to FUND your Polymarket account.

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

print

( client.derive_api_key() )

See all 20 lines

​

Using those keys to connect to the Market or User Websocket

WSS-Connection

Copy

Ask AI

from

websocket

import

WebSocketApp

import

json

import

time

import

threading

MARKET_CHANNEL

=

"market"

USER_CHANNEL

=

"user"

class

WebSocketOrderBook

:

def

__init__

(

self

,

channel_type

,

url

,

data

,

auth

,

message_callback

,

verbose

):

self

.channel_type

=

channel_type

self

.url

=

url

self

.data

=

data

self

.auth

=

auth

self

.message_callback

=

message_callback

self

.verbose

=

verbose

furl

=

url

+

"/ws/"

+

channel_type

self

.ws

=

WebSocketApp(

furl,

on_message

=

self

.on_message,

on_error

=

self

.on_error,

on_close

=

self

.on_close,

on_open

=

self

.on_open,

)

self

.orderbooks

=

{}

def

on_message

(

self

,

ws

,

message

):

print

(message)

pass

def

on_error

(

self

,

ws

,

error

):

print

(

"Error: "

, error)

exit

(

1

)

def

on_close

(

self

,

ws

,

close_status_code

,

close_msg

):

print

(

"closing"

)

exit

(

0

)

def

on_open

(

self

,

ws

):

if

self

.channel_type

==

MARKET_CHANNEL

:

ws.send(json.dumps({

"assets_ids"

:

self

.data,

"type"

:

MARKET_CHANNEL

}))

elif

self

.channel_type

==

USER_CHANNEL

and

self

.auth:

ws.send(

json.dumps(

{

"markets"

:

self

.data,

"type"

:

USER_CHANNEL

,

"auth"

:

self

.auth}

)

)

else

:

exit

(

1

)

thr

=

threading.Thread(

target

=

self

.ping,

args

=

(ws,))

thr.start()

def

ping

(

self

,

ws

):

while

True

:

ws.send(

"PING"

)

time.sleep(

10

)

def

run

(

self

):

self

.ws.run_forever()

if

__name__

==

"__main__"

:

url

=

"wss://ws-subscriptions-clob.polymarket.com"

#Complete these by exporting them from your initialized client.

api_key

=

""

api_secret

=

""

api_passphrase

=

""

asset_ids

=

[

"109681959945973300464568698402968596289258214226684818748321941747028805721376"

,

]

condition_ids

=

[]

# no really need to filter by this one

auth

=

{

"apiKey"

: api_key,

"secret"

: api_secret,

"passphrase"

: api_passphrase}

market_connection

=

WebSocketOrderBook(

MARKET_CHANNEL

, url, asset_ids, auth,

None

,

True

)

user_connection

=

WebSocketOrderBook(

USER_CHANNEL

, url, condition_ids, auth,

None

,

True

)

market_connection.run()

# user_connection.run()

See all 86 lines

WSS Overview

WSS Authentication

⌘

I