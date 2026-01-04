# Get comments by user address - Polymarket Documentation

URL: https://docs.polymarket.com/api-reference/comments/get-comments-by-user-address

---

Get comments by user address - Polymarket Documentation

Skip to main content

Polymarket Documentation

home page

Search...

⌘

K

Search...

Navigation

Comments

Get comments by user address

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

GET

List comments

GET

Get comments by comment id

GET

Get comments by user address

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

Get comments by user address

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/comments/user_address/{user_address}

200

Copy

Ask AI

[

{

"id"

:

"<string>"

,

"body"

:

"<string>"

,

"parentEntityType"

:

"<string>"

,

"parentEntityID"

:

123

,

"parentCommentID"

:

"<string>"

,

"userAddress"

:

"<string>"

,

"replyAddress"

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

,

"profile"

: {

"name"

:

"<string>"

,

"pseudonym"

:

"<string>"

,

"displayUsernamePublic"

:

true

,

"bio"

:

"<string>"

,

"isMod"

:

true

,

"isCreator"

:

true

,

"proxyWallet"

:

"<string>"

,

"baseAddress"

:

"<string>"

,

"profileImage"

:

"<string>"

,

"profileImageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"positions"

: [

{

"tokenId"

:

"<string>"

,

"positionSize"

:

"<string>"

}

]

},

"reactions"

: [

{

"id"

:

"<string>"

,

"commentID"

:

123

,

"reactionType"

:

"<string>"

,

"icon"

:

"<string>"

,

"userAddress"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"profile"

: {

"name"

:

"<string>"

,

"pseudonym"

:

"<string>"

,

"displayUsernamePublic"

:

true

,

"bio"

:

"<string>"

,

"isMod"

:

true

,

"isCreator"

:

true

,

"proxyWallet"

:

"<string>"

,

"baseAddress"

:

"<string>"

,

"profileImage"

:

"<string>"

,

"profileImageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"positions"

: [

{

"tokenId"

:

"<string>"

,

"positionSize"

:

"<string>"

}

]

}

}

],

"reportCount"

:

123

,

"reactionCount"

:

123

}

]

GET

/

comments

/

user_address

/

{user_address}

Try it

Get comments by user address

cURL

Copy

Ask AI

curl

--request

GET

\

--url

https://gamma-api.polymarket.com/comments/user_address/{user_address}

200

Copy

Ask AI

[

{

"id"

:

"<string>"

,

"body"

:

"<string>"

,

"parentEntityType"

:

"<string>"

,

"parentEntityID"

:

123

,

"parentCommentID"

:

"<string>"

,

"userAddress"

:

"<string>"

,

"replyAddress"

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

,

"profile"

: {

"name"

:

"<string>"

,

"pseudonym"

:

"<string>"

,

"displayUsernamePublic"

:

true

,

"bio"

:

"<string>"

,

"isMod"

:

true

,

"isCreator"

:

true

,

"proxyWallet"

:

"<string>"

,

"baseAddress"

:

"<string>"

,

"profileImage"

:

"<string>"

,

"profileImageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"positions"

: [

{

"tokenId"

:

"<string>"

,

"positionSize"

:

"<string>"

}

]

},

"reactions"

: [

{

"id"

:

"<string>"

,

"commentID"

:

123

,

"reactionType"

:

"<string>"

,

"icon"

:

"<string>"

,

"userAddress"

:

"<string>"

,

"createdAt"

:

"2023-11-07T05:31:56Z"

,

"profile"

: {

"name"

:

"<string>"

,

"pseudonym"

:

"<string>"

,

"displayUsernamePublic"

:

true

,

"bio"

:

"<string>"

,

"isMod"

:

true

,

"isCreator"

:

true

,

"proxyWallet"

:

"<string>"

,

"baseAddress"

:

"<string>"

,

"profileImage"

:

"<string>"

,

"profileImageOptimized"

: {

"id"

:

"<string>"

,

"imageUrlSource"

:

"<string>"

,

"imageUrlOptimized"

:

"<string>"

,

"imageSizeKbSource"

:

123

,

"imageSizeKbOptimized"

:

123

,

"imageOptimizedComplete"

:

true

,

"imageOptimizedLastUpdated"

:

"<string>"

,

"relID"

:

123

,

"field"

:

"<string>"

,

"relname"

:

"<string>"

},

"positions"

: [

{

"tokenId"

:

"<string>"

,

"positionSize"

:

"<string>"

}

]

}

}

],

"reportCount"

:

123

,

"reactionCount"

:

123

}

]

Path Parameters

​

user_address

string

required

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

Response

200 - application/json

Comments

​

id

string

​

body

string | null

​

parentEntityType

string | null

​

parentEntityID

integer | null

​

parentCommentID

string | null

​

userAddress

string | null

​

replyAddress

string | null

​

createdAt

string<date-time> | null

​

updatedAt

string<date-time> | null

​

profile

object

Show

child attributes

​

reactions

object[]

Show

child attributes

​

reportCount

integer | null

​

reactionCount

integer | null

Get comments by comment id

Search markets, events, and profiles

⌘

I