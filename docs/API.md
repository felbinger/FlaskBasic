# API Information
* The base endpoint is: [http://localhost:5000/](http://localhost:5000/)
* All endpoints return a JSON object.
* All time and timestamp related fields are in [ISO-8601](https://en.wikipedia.org/wiki/ISO_8601) format.
* In case of error endpoint's will respond with a json object just like that. 
This message should only be used for debugging, not for conditions, you can use the response status code instead:
    ```json
    {
        "message": "Payload is invalid"
    }
    ```

* For `POST`, `PUT`, and `DELETE` endpoints, the parameters should be sent
  in the `request body` with content type `application/json`.
* To address a specific object for example the user with the id 10 you put it into the resource:
  ```
  /api/users/10
  ```
* Parameters may be sent in any order.

* Access token's are passed into the Rest API via the `Authorisation` header.
* Token's and password's are **case sensitive**.
* The OpenAPI documentation is accessable at `/api/docs`