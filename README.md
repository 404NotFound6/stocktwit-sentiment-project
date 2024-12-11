<div align="center">
  
# How do Public Sentiments Affect Stock Metrics?

<font size="5">**11 December 2024**</font>  
<font size="5"><i>Python, Big Data, and Databases (ECO395m)</i></font>



**404 NotFound: Rongzheng Ma, Siyi Li, Sherry Chen**
</div>

---

## Introduction

The goal of this project is to analyze how public sentiments could potentially affect the Dow Jones Index and the prices of Companies in the Index. The public sentiments were acquired from the comments of an open online forum, Stocktwit. By performing a time-series regression analysis, we could have a better understanding of how sentiments score from StockTwits predict future stock movements. 


## Methodology

We scraped the comments and the number of comments that are under each comment of 30 companies in the Dow Jones Index from the forum Stocktwit using Python packaging selenium. Since the total number of data is huge, We then connected to the Google Cloud Platform(GCP) to acquire servers to help with scraping. After scraping, we add these posts to the SQL database and use SQLAlchemy to derive sentiment scores in the (GPT model) (need to switch). 

1. Stocktwit Comments: We acquired 85775 posts from these 30 companies. Based on the date that the program stopped, the number of comments on each company is not the same, and the last date of the comment scarped for each company is not the same as well. The output of all the comments was directly pushed to the databased. The summary of the number of comments and the last date of the comment scraped is provided below and also in the artifact folder.



2. 



## Step for Reproduce


## Results 


## Limitation



