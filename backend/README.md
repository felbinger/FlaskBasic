# Python FlaskBasic
This Project is using the Bootstrap admin theme [Startbootstrap SB Admin](https://blackrockdigital.github.io/startbootstrap-sb-admin/index.html).

### TODO
* 2FA:
    * Split Login: User should first enter username/password and then be ask for his token if he has 2fa enabled
    * User should check if 2fa is working after setup, only if he can provide a valid token 2fa should be activated.
* API (`authentication`): Redis Blacklist/Refresh Tokens
* Tests: add missing tests
* WTForms: Update dashboard/profile (validation using WTForms)
* Messaging System

### API Information
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

* Login token's are passed into the Rest API via the `Access-Token` header.
* Login token's and password's are **case sensitive**.

### Run FlaskBasic
* Define your container in the file `docker-compose.yml`:
    ```yml
    version: '3'
    services:
      db:
        image: mysql:5.7
        container_name: root_db_1
        restart: always
        environment:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: flaskbasic
        volumes:
          - "/srv/mysql:/var/lib/mysql"
          
      flaskbasic:
        image: nicof2000/flaskbasic
        container_name: root_flaskbasic_1
        restart: always
        ports:
          - "8080:80"
        environment:
          MYSQL_PASSWORD: root
    ```

* Add database web (in this example automatically)
* Change database collection from `latin1_swedish_ci` to `utf8mb4_unicode_ci`
* Execute the following sql:
    ```sql
    INSERT INTO `role` (`id`, `name`, `description`) VALUES
    (1, 'admin', 'Admin'),
    (2, 'user', 'User');
    ```
* Start both container: `docker-compose up -d`
