# Python FlaskBasic
This Project is using the Bootstrap admin theme [Startbootstrap SB Admin](https://blackrockdigital.github.io/startbootstrap-sb-admin/index.html).

### Features
* User Management
* Profile Page
* Account verification
* Multi Factor Authentication (MFA) using tme based one time pad's (and gpg message decryption)
* Password Reset (using email)
* (GPG encrypted mails)

### TODO
* Tests: Add missing test cases
  * flask_mail
  * Password reset
  * Account verification
  * Profile Picture upload
* Update admin dashboard to partly js frontend
* Features:
  * Messaging System
  * GPG (flask_gnupg) Encrypted Mails
  * GPG (flask_gnupg) MFA
* Improve profile page design (Image Upload: https://codepen.io/jeikuinu/pen/GBvgge)

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
