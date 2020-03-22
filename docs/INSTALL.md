# Installation

### Productive Environment docker-compose

1. [Install Docker](https://docs.docker.com/install/)

2. [Install docker-compose](https://docs.docker.com/compose/install/)
    ```bash
    curl -L "https://github.com/docker/compose/releases/download/1.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ```

3. Define your container in the file `docker-compose.yml`
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
        depends_on:
          - db
          - redis
        ports:
          - "8080:80"
        environment:
          MYSQL_USERNAME: root
          MYSQL_PASSWORD: root
    ```
   
4. Start all container (`docker-compose up -d`)

5. Create the default roles
    ```sql
    INSERT INTO `role` (`id`, `name`, `description`) VALUES
    (1, 'admin', 'Admin'),
    (2, 'user', 'User');
    ```

6. Change database collection from `latin1_swedish_ci` to `utf8mb4_unicode_ci`

### Development Environment

```bash
$ python3 -m pip install requirements.txt
$ FLASK_ENV=development FLASK_DEBUG=1 flask run
```