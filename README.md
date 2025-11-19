# Cloud5-Serverless-Image-Processing
CS1660 Final Project

## Group Members:
- Chris White
- Mia Miller
-
-
-

## Project Description

### Serverless Image Processing Service
Develop a web application that allows users to upload and process images.
• Suggested AWS Services: S3, Lambda, API Gateway, DynamoDB, Cognito,
CloudFront, Step Functions
• Users upload images to S3
• Lambda functions process images (resize, filter, format conversion)
• Provide downloadable URLs for processed images
• Track processing history per user

### Services used so far
- 

## TODO
- Create S3 Buckets for image uploads
- Set up authentication layer with Cognito(?)
- - Create an account and log in
- - Alter the state of the application (e.g., save preferences, create content)
- - Log out and log back in to see their persisted data
- Set up API Gateway
- - I think making the images downloadable is part of this
- Set up Lambda Functions for image processing
- Set up DynamoDB
- Set up CloudFront
- Step Functions
