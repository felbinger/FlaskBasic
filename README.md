# Python FlaskBasic
This Project is using the Bootstrap admin theme [Startbootstrap SB Admin](https://blackrockdigital.github.io/startbootstrap-sb-admin/index.html).

### Features
* User Management
* Profile Page
* Account verification
* 2-Factor Authentication (using totp)
* Password Reset (using email)
* (GPG encrypted mails)

### TODO
* Tests: Add missing test cases
  * flask_mail
  * Password reset
  * Account verification
  * Profile Picture upload
* GPG encrypted emails arrive incompleted
* Update admin dashboard to partly js frontend
* Features:
  * Messaging System
  * GPG (flask_gnupg) Encrypted Mails
  * GPG (flask_gnupg) 2FA/3FA


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
