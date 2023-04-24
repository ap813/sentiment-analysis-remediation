# sentiment-analysis-remediation

This project is a Lambda function fronted by an API Gateway with Infrastructure written in Pulumi (Python). The API is used to send alerts to an SNS topic when negative sentiment is detected. This is an extremely inexpensive solution for remediating negative customer feedback.

## The reason behind the solution

Solutions are cool, but the *why* is really the important part. Let's say uou have a comment section on your application. You want to provide immediate feedback from your organization when you get negative comments. This is usually seen in the real world where people leave comments on Google about a business when they have an unsatisfactory experience. Then the owner of the business goes on Google and replies to the comment how they see fit.

What is being built here is a model of how to react to those negative comments. You provide an email in an environment variable about where you want emails to go to. Then you'll receive those emails when customers are upset.

## What do you need

* [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/)
* AWS Credentials that are allowed to provision the infrastructure
* Python3.7 or higher installed on your computer
* Curl (if you want to test it at the end)

## Architecture

[Sentiment Analysis Diagram](./sentiment-analysis-diagram.png)

## Build it

Here are the steps to build this project. Make sure that you have installed the requirements to do these commands.

1. Clone the repo
2. Add in your desired email in the environment variable *SNS_EMAIL*
3. Run *pulumi up*, review the infrastructure being created, then select *yes*
4. Once the stack is completely built, you will get an email from AWS asking you to opt-in to alerts from the newly created SNS target. Accept it so you will receive alerts later
5. The execution will give you the new API Gateway url when you run *pulumi stack output api_gateway*. Replace {{ api_gateway }} down below with your generated API Gateway url and run the command

```bash
curl -XPOST -H "Content-type: application/json" -d '{
    "name": "John Smith",
    "email": "john@email.com",
    "review": "This is the worst product I've ever purchased"
}' '{{ api_gateway }}/stage/sentiment'
```

6. You should get an email at your desired email address in less than 10s