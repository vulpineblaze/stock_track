# Stock Track
> This project is a proof-of-concept to do some big-data number crunching using only a t1.tiny AWS instance.

## Table of contents
* [General info](#general-info)
* [Screenshots](#screenshots)
* [Technologies](#technologies)
* [Setup](#setup)
  * [Requirements](#requirements)
  * [Usage](#usage)
* [Features](#features)
* [Status](#status)
* [Inspiration](#inspiration)
* [Contact](#contact)

## General info
The project was successful in that the ti.tiny AWS EC2 instance could properly handle large datasets and correct execute desired algorithms. Having scarce resources have forced innovations that have improved the data mining algorithms preciseness by whole orders of magnitude.


## Screenshots
![Example screenshot](./img/screenshot.png)

## Technologies
* Python - version 2.7
* Django
* nginx
* gunicorn
* MySQL
* Tech 2 - version 2.0
* Tech 3 - version 3.0

## Setup
Outlined in [install_instructions](./install_instructions)

### Requirements
Outlined in [requirements.txt](./requirements.txt)

### Usage
Scripts hold various data collection and scraping functions, while web API calls via cron updated data and performed analytics to display to User via web interface.

## Features
List of features ready and TODOs for future development
* Takes in internet stock data and store it
* Updates with new stock data
* Performs analyutics on data and memoize results
* Provides web API interface and Google Charts API for User

To-do list:
* Refine analytics algorithm

## Status
Project is: _no longer continue_, due to older technologies it uses.

## Inspiration
Discussion on "solving" the stock market with a fellow CSUS student lead to this project. The results were accurate, but the answer was not as promising as hoped. 

## Contact
Created by [@vulpineblaze](https://github.com/vulpineblaze) - feel free to contact me!



### Monetization
I may attempt to monetize this project. (C) All Rights Reserved 2015.
