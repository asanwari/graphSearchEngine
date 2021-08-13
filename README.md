# Graph Search Engine
A fully Dockerized two container solution which 
*   Extracts data from source pdfs
    * For more information on which data is extracted, see annotated_documents.pdf in dataset folder
*   Adds the extracted data to a graph database (Neo4j). The graph has two relations:
    * Product [Entity] is_without [relationship] Substance [Entity]
    * Product [Entity] complies [relationship] Regulation [Entity]
*   Exposes a restful API to enable querying over the extracted data
    * The queries are natural language text. No real ML methods are used for query understanding. Only heuristics are used. For more information, see the Final Words section.

# Installation Steps
Each container has it's own docker-compose file. In order to allow the containers to talk to each other, I have configured them to be on the same bridged network. 

### Step 1: Create a bridged network on docker
Create a new bridged network called my-bridge-network by executing the following:
```
docker network create -d bridge my-bridge-network
```
### Step 2: Start the neo4j container
Go to the database directory and execute the folloing 
```
docker-compose up --build -d
```

The database container named testNeo4j should be up and running. Verify this by going to 
> http://localhost:7474/browser/

### Step 3: Set the neo4j IP in restAPI's config
Since the two containers are using a custom bridged network, we have to set the IP of neo4j in the restAPI container. To see the IP of Neo4j container, check the current running containers

> docker ps

```
CONTAINER ID   IMAGE                  COMMAND                  CREATED          STATUS          PORTS
                                                                         NAMES
e7069319cefd   neo4j:latest           "/sbin/tini -g -- /d…"   12 hours ago     Up 37 minutes   0.0.0.0:7474->7474/tcp, :::7474->7474/tcp, 7473/tcp, 0.0.0.0:7687->7687/tcp, :::7687->7687/tcp   testneo4j
```

Then, inspect the container

> docker inspect e7069319cefd

We need to extract the IP address from this json. It would be in the networks -> my-bridge-network -> IPAddress. Now we need to set it in the config file of the restapi

Go to restApi/config.json. and set the ip address in bolt_url. The port remains the same
```
{
    "neo4j_username" : "neo4j",
    "neo4j_password" : "test",
    "bolt_url" : "bolt://172.19.0.3:7687" ,
    "extracted_json_path" : "/home/graphSearchEngine/dataset/dataset/products.json",
    "data_dir": "/home/graphSearchEngine/dataset/dataset/",
    "fuzzy_match_threshold": 80    
}

```


Now, we can start the restApi.

### Step 4: Start restApi server
Navigate to restApi and run 

> docker-compose up --build -d

Once the container is up, the setup is complete. The restApi server is hosted on localhost:5000

# Testing the connection
To test the connection with neo4j, send a get request to
> http://localhost:5000/checkDatabaseConnection

If successful, you should see this:

```
connection successful
```


# RestApi Endpoints
Apart from /checkDatabaseConnection, the restApi has the following connections

| End Point     | Description   |
| ------------- |-------------|
|/              |Hello world. This is to check if the restApi server is up.|
|/extract       |Extracts the data from pdf and stores it in products.json file|
|/constructGraph|Reads the data from products.json and populated the neo4j Graph|
|/getQuery      |Takes a natural langauge query in the body of the request and returns the results|
|/dropDatabase  |Drops the Neo4j database. This is useful for extracting new data|


### Anatomy of getQuery
In order for retrieval to work, the /getQuery request has to be a post request. the query should be sent in the body of the request with the type application/json. A sample request is shown below.

```
{
 "query":"does ultrafoam contain latex?"
}
```

The response looks like this:
```
{
    "queryAnalysis": {
        "productNameCorrected": true,
        "relationType": "IS_WITHOUT",
        "sourceEntity": "ultraform",
        "sourceEntityType": "Product",
        "targetEntity": "latex",
        "targetEntityType": "Substance"
    },
    "retrievalResult": [
        {
            "product": "ultraform",
            "relation": "IS_WITHOUT",
            "target": "latex"
        }
    ]
}
```
The queryAnalysis object is the information of the parameters that were used for generating the graph search. It is elaborated below:

| field  | description |
| ------------- |-------------|
|productNameCorrected|The product names in the query are matched in a fuzzy manner if original names aren't found. if this is set to true, it means that the match was a fuzzy match. The fuzzy match threshold is controlled by the fuzzy_match_threshold field in the cofig.json file|
|relationType         | The predicted relationship type     |
| sourceEntity        | The product that needs to be retrieved. would be null for queries that don't have a particular product, eg for the query "products without latex"|
| sourceEntityType    | The predicted type of the source entity|
| targetEntity        | The predicted target entity. Can be null|
| targetEntityType    | The predicted type of the target entity|

The retrievalResult field is simply the matched data.

# Files 
| file  | description |
| ------------- |-------------|
| extractor.py| Extracts the pdf files and stores data in a json file called products.json|
|graphPopulator.py| Uses the extracted data from the extractor to populate the neo4j database|
|retrievalEngine.py| Processes the queries and retrieves the results|
|databaseService.py| Handles all communication with the database. This is used by all classes to perform functions on the database|
# Final Words
Since this is a demo, I have done some things in a temporary way. I would certainly not do this in production. It is worth noting these things down. The following is a list of such things plus some observations about my implementation
* Extraction
    * Substance extraction is very basic. For example, I am not extracting all ozone depleting substances (The list of individual substances). However, this is in compliance with the annotated document.
    * I have extracted only the brand names, i.e. the names that end on the registered trademark sign. This can easily be extended to the full names but for this basic implementation, i deemed it an overkill
    * Product names in the document and the list had insonsistencies in terms of case sensitiviHyety. Hence, I stored all products with lower case. 
    *  Regulations are somewhat blindly extracted. I am not checking what the document is saying about the regulation, e.g. "regulation x replaces the regulation y"
* graph creation
    * Not doing bulk inserts. This will certainly improve speed.

For retrieval, I am using several weak heuristics.
* Retrieval and restApi
    *  For extracting the substance, I am looking for words like "contains" or "without".
    *  For extraction of regulation, I am simply using regex.
    *  For pridicting the relation type, I am using a lemmatized keyword search. Example: if the query is "all products containing latex", containing would be lemmatized to contain and would match in the substance relation words. Similar thing is done for regulations (words like comply, follow etc.) 
    * For extracting products, I am using a fuzzy search over all nouns. I am also searching for words like "product", which implies that the query is not for a particular product, but rather for all products.
    *  Since regex search is much easier (as it doesn't have to be fuzzy), I am first checking the heuristic for regulation. If that fails, I am checking the heuristic for substances.
    * In the query, the substance is always assumed to be the last phrase of the sentence, making it prone to errors.
    * The retrieval performance is hurt due to database service not being injected. Each time a new call is made, the service is reinstantiated. This is an easy fix
    * The extract and constructGraph endpoints are just for showing that things work. in real life, such time-consuming jobs would never be done like this. Instead, they would be backend jobs. Doing it would have been an overkill. 
    * Since no real machine learning is used here, the query results may be unexpected. It would work for simple queries but not for complicated ones. 

features
* muti-word substances are hiphenated to aid in search
* uses a databaseService that controls the connection to neo4j. 

Packages used:
* see requirements.txt