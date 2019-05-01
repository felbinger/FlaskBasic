# Python FlaskBasic
This Project is using the Bootstrap admin theme [Startbootstrap SB Admin](https://blackrockdigital.github.io/startbootstrap-sb-admin/index.html).

### TODO
* Think of implementing some api calls (e.g. login) client site (via js) to enhance security -> how to get token to flask session
* Tests: Add missing test cases (refresh tokens, totp, mail, views)
* WTForms: Update dashboard/profile (validation using WTForms)
* Features:
  * Profile Picture Upload
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

* Access token's are passed into the Rest API via the `Authorisation` header.
* Token's and password's are **case sensitive**.

### Run FlaskBasic
* Define your container in the file `docker-compose.yml`:
    ```yml
    version: '3'
    services:
      db:
        image: mariadb
        restart: always
        environment:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: flaskbasic
        volumes:
          - "/srv/mysql:/var/lib/mysql"
          
      redis:
        image: redis
        restart: always
        volumes:
          - /srv/redis:/data
          
      flaskbasic:
        image: nicof2000/flaskbasic
        restart: always
        ports:
          - "8080:80"
        environment:
          MYSQL_USERNAME: root
          MYSQL_PASSWORD: root
    ```

* Change database collection from `latin1_swedish_ci` to `utf8mb4_unicode_ci`
* Execute the following sql:
    ```sql
    INSERT INTO `role` (`id`, `name`, `description`) VALUES
    (1, 'admin', 'Admin'),
    (2, 'user', 'User');
    ```
* Start both container: `docker-compose up -d`

#### Environment Variables
| Key                   | Description                                | Default              |
|-----------------------|--------------------------------------------|----------------------|
| MYSQL_USERNAME        |                                            | flaskbasic           |
| MYSQL_PASSWORD        |                                            | flaskbasic           |
| MYSQL_HOSTNAME        |                                            | db                   |
| MYSQL_PORT            |                                            | 3306                 |
| MYSQL_DATABASE        |                                            |                      |
| MAIL_SERVER           |                                            |                      |
| MAIL_PORT             |                                            | 465                  |
| MAIL_SENDER           |                                            | flaskbasic@localhost |
| MAIL_USERNAME         |                                            |                      |
| MAIL_PASSWORD         |                                            |                      |
| MAIL_ENCRYPTION       | valid values: unencrypted / starttls / ssl | unencrypted          |
| RECAPTCHA_PUBLIC_KEY  |                                            |                      |
| RECAPTCHA_PRIVATE_KEY |                                            |                      |
| REDIS_HOSTNAME        |                                            | redis                |
| REDIS_PORT            |                                            | 6379                 |
| REDIS_PASSWORD        |                                            |                      |
| REDIS_DATABASE        |                                            | 0                    |
|                       |                                            |                      ||